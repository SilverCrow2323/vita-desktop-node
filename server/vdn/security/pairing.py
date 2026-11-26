"""Local approval-based device pairing and per-device authorization.

Pairing codes and device credentials are high-entropy bearer secrets. Only
SHA-256 digests are persisted; secrets are returned once to the caller.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Iterable

DEFAULT_PERMISSIONS = frozenset({
    "node.info", "telemetry.read", "process.read", "actions.catalog.read",
    "actions.propose", "files.list", "files.read", "files.write",
    "files.delete", "terminal.open", "terminal.execute", "desktop.view",
    "desktop.control", "display.session", "notification.send",
})


class PairingError(ValueError):
    """Pairing or authorization request rejected."""


class PairingStore:
    """Persistent pairing state; approvals must be invoked by the local host UI."""

    def __init__(self, state_dir: Path, *, credential_ttl: int = 90 * 86400):
        self.state_dir = Path(state_dir)
        self.path = self.state_dir / "paired-devices.json"
        self.credential_ttl = max(300, int(credential_ttl))
        self._lock = threading.RLock()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "posix":
            self.state_dir.chmod(0o700)
        self._state = self._load()

    def _load(self):
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {"pairing": None, "pending": {}, "devices": {}}
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PairingError("cannot read pairing store") from exc
        if not isinstance(value, dict):
            raise PairingError("pairing store must be an object")
        for key in ("pending", "devices"):
            if not isinstance(value.get(key), dict):
                value[key] = {}
        return value

    def _save(self):
        fd, name = tempfile.mkstemp(prefix=".pairing-", dir=self.state_dir)
        try:
            if os.name == "posix":
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._state, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
            if os.name == "posix":
                self.path.chmod(0o600)
        finally:
            try:
                os.unlink(name)
            except FileNotFoundError:
                pass

    @staticmethod
    def _device_id(value: str) -> str:
        try:
            return str(uuid.UUID(value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise PairingError("device_id must be a UUID") from exc

    @staticmethod
    def _permissions(values: Iterable[str]) -> list[str]:
        if isinstance(values, (str, bytes)):
            raise PairingError("permissions must be a list")
        requested = list(values)
        if len(requested) > len(DEFAULT_PERMISSIONS) or any(
            not isinstance(item, str) or item not in DEFAULT_PERMISSIONS
            for item in requested
        ):
            raise PairingError("unknown or invalid permission")
        return sorted(set(requested))

    def open_pairing_window(self, *, ttl: int = 180) -> dict:
        """Open a short-lived local pairing window and return its one-time code."""
        if not 30 <= int(ttl) <= 600:
            raise PairingError("pairing window must be 30..600 seconds")
        code = secrets.token_urlsafe(18)
        now = int(time.time())
        with self._lock:
            self._state["pairing"] = {
                "code_hash": hashlib.sha256(code.encode("ascii")).hexdigest(),
                "expires_at": now + int(ttl),
                "attempts": 0,
            }
            self._save()
        return {"code": code, "expires_at": now + int(ttl)}

    def close_pairing_window(self) -> None:
        with self._lock:
            self._state["pairing"] = None
            self._save()

    def request_pairing(self, *, code: str, device_id: str,
                        device_name: str, requested_permissions: Iterable[str]) -> dict:
        """Validate one-time code and create a pending request; grants nothing."""
        device_id = self._device_id(device_id)
        if not isinstance(code, str) or not code or len(code) > 128:
            raise PairingError("invalid pairing code")
        if not isinstance(device_name, str) or not device_name.strip() or len(device_name) > 80:
            raise PairingError("device name must contain 1..80 characters")
        permissions = self._permissions(requested_permissions)
        now = int(time.time())
        supplied = hashlib.sha256(code.encode("utf-8")).hexdigest()
        with self._lock:
            window = self._state.get("pairing")
            if not isinstance(window, dict) or now > int(window.get("expires_at", 0)):
                self._state["pairing"] = None
                self._save()
                raise PairingError("pairing window is closed or expired")
            expected = str(window.get("code_hash", ""))
            if not hmac.compare_digest(supplied, expected):
                window["attempts"] = int(window.get("attempts", 0)) + 1
                if window["attempts"] >= 5:
                    self._state["pairing"] = None
                self._save()
                raise PairingError("invalid pairing code")
            self._state["pairing"] = None  # one request consumes the code
            existing = self._state["devices"].get(device_id)
            if isinstance(existing, dict) and not existing.get("revoked"):
                self._save()
                raise PairingError("device is already paired; revoke it before pairing again")
            if any(item.get("device_id") == device_id
                   for item in self._state["pending"].values()):
                self._save()
                raise PairingError("device already has a pending pairing request")
            request_id = str(uuid.uuid4())
            self._state["pending"][request_id] = {
                "device_id": device_id,
                "device_name": device_name.strip(),
                "requested_permissions": permissions,
                "created_at": now,
            }
            self._save()
        return {"request_id": request_id, "status": "pending_host_approval"}

    def pending_requests(self) -> list[dict]:
        with self._lock:
            return [
                {"request_id": key, "device_id": value["device_id"],
                 "device_name": value["device_name"],
                 "requested_permissions": list(value["requested_permissions"]),
                 "created_at": value["created_at"]}
                for key, value in self._state["pending"].items()
            ]

    def approve_request(self, request_id: str, *, permissions: Iterable[str] | None = None) -> dict:
        """Approve locally and return the new device credential exactly once."""
        with self._lock:
            pending = self._state["pending"].get(request_id)
            if pending is None:
                raise PairingError("unknown or already handled pairing request")
            granted = self._permissions(
                pending["requested_permissions"] if permissions is None else permissions
            )
            if not set(granted).issubset(set(pending["requested_permissions"])):
                raise PairingError("host may grant only permissions requested by the device")
            credential = secrets.token_urlsafe(32)
            now = int(time.time())
            device_id = pending["device_id"]
            self._state["devices"][device_id] = {
                "device_id": device_id,
                "device_name": pending["device_name"],
                "credential_hash": hashlib.sha256(credential.encode("ascii")).hexdigest(),
                "permissions": granted,
                "created_at": now,
                "expires_at": now + self.credential_ttl,
                "revoked": False,
            }
            del self._state["pending"][request_id]
            self._save()
        return {"device_id": device_id, "credential": credential,
                "permissions": granted, "expires_at": now + self.credential_ttl}

    def authenticate(self, *, device_id: str, credential: str,
                      required_permission: str) -> dict:
        """Validate credential, expiry, revocation and the requested permission."""
        device_id = self._device_id(device_id)
        if not isinstance(credential, str) or not credential or len(credential) > 256:
            raise PairingError("invalid device credential")
        supplied = hashlib.sha256(credential.encode("utf-8")).hexdigest()
        with self._lock:
            device = self._state["devices"].get(device_id)
            if not isinstance(device, dict) or device.get("revoked"):
                raise PairingError("device is not paired")
            expected = str(device.get("credential_hash", ""))
            if not hmac.compare_digest(supplied, expected):
                raise PairingError("invalid device credential")
            if int(time.time()) > int(device.get("expires_at", 0)):
                raise PairingError("device credential has expired")
            if required_permission not in device.get("permissions", []):
                raise PairingError("device lacks required permission")
            return {"device_id": device_id, "device_name": device["device_name"],
                    "permissions": list(device["permissions"])}

    def revoke_device(self, device_id: str) -> None:
        device_id = self._device_id(device_id)
        with self._lock:
            device = self._state["devices"].get(device_id)
            if not isinstance(device, dict):
                raise PairingError("unknown device")
            device["revoked"] = True
            device["revoked_at"] = int(time.time())
            self._save()

    def paired_devices(self) -> list[dict]:
        with self._lock:
            return [
                {"device_id": value["device_id"], "device_name": value["device_name"],
                 "permissions": list(value["permissions"]),
                 "created_at": value["created_at"], "expires_at": value["expires_at"],
                 "revoked": bool(value.get("revoked"))}
                for value in self._state["devices"].values()
            ]
