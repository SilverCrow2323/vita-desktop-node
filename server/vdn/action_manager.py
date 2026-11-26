"""Persistent approval-gated host actions. Executables never leave the host."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

_BLOCKED = {
    "sh", "bash", "zsh", "fish", "dash", "ash", "csh", "tcsh",
    "cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh",
    "sudo", "doas", "pkexec", "su",
}
_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._-]{2,95}")


class ActionError(ValueError):
    """Invalid, disabled, or unapproved action."""


class ActionManager:
    """Local action store. A future transport must authenticate and authorize first."""

    def __init__(self, state_dir: Path, *, audit_limit: int = 1000):
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / "actions.json"
        self.audit_file = self.state_dir / "action-audit.jsonl"
        self.audit_limit = max(50, audit_limit)
        self._lock = threading.RLock()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "posix":
            self.state_dir.chmod(0o700)
        self._actions = self._load()

    def _load(self):
        try:
            raw = json.loads(self.state_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ActionError(f"cannot read action store: {exc}") from exc
        if not isinstance(raw, dict):
            raise ActionError("action store must contain an object")
        return {key: value for key, value in raw.items()
                if isinstance(key, str) and isinstance(value, dict)}

    def _save(self):
        fd, name = tempfile.mkstemp(prefix=".actions-", dir=self.state_dir)
        try:
            if os.name == "posix":
                os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._actions, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.state_file)
            if os.name == "posix":
                self.state_file.chmod(0o600)
        finally:
            try:
                os.unlink(name)
            except FileNotFoundError:
                pass

    @staticmethod
    def _argv(argv):
        if not isinstance(argv, (list, tuple)) or not argv or len(argv) > 64:
            raise ActionError("argv must contain 1..64 arguments")
        if any(not isinstance(item, str) or not item or len(item) > 2048 for item in argv):
            raise ActionError("invalid argument")
        if Path(argv[0]).name.lower() in _BLOCKED:
            raise ActionError("shells and privilege-escalation tools are not allowed")
        return list(argv)

    def _resolve_argv(self, item, extra_args=None):
        argv = self._argv(item.get("argv"))
        if extra_args is not None:
            if (not isinstance(extra_args, (list, tuple)) or len(extra_args) > 16
                    or any(not isinstance(arg, str) or not arg or len(arg) > 512
                           for arg in extra_args)):
                raise ActionError("invalid extra arguments")
            argv.extend(extra_args)
        executable = shutil.which(argv[0]) if not os.path.isabs(argv[0]) else argv[0]
        if not executable or not Path(executable).is_file():
            raise ActionError("application executable was not found on this host")
        argv[0] = executable
        return argv

    def _approved_argv(self, action_id, *, confirmed, extra_args=None):
        with self._lock:
            item = self._actions.get(action_id)
            if item is None:
                raise ActionError("unknown action")
            if not item.get("approved") or not item.get("enabled"):
                raise ActionError("action is not approved and enabled")
            if item.get("requires_confirmation") and not confirmed:
                raise ActionError("explicit confirmation is required")
            return self._resolve_argv(item, extra_args)

    def _store(self, record):
        with self._lock:
            self._actions[record["action_id"]] = record
            self._save()
        return self.public_action(record["action_id"])

    def register_application(self, app):
        action_id = str(app.action_id)
        if not _ID.fullmatch(action_id):
            raise ActionError("invalid action ID")
        argv = self._argv(app.launch_argv)
        previous = self._actions.get(action_id, {})
        unchanged = previous.get("argv") == argv
        return self._store({
            "action_id": action_id,
            "name": str(app.name)[:120],
            "categories": list(app.categories),
            "icon": app.icon,
            "platform": getattr(app, "platform", "unknown"),
            "argv": argv,
            "enabled": bool(previous.get("enabled")) if unchanged else False,
            "approved": bool(previous.get("approved")) if unchanged else False,
            "requires_confirmation": True,
            "origin": "desktop-catalog",
            "updated_at": int(time.time()),
        })

    def add_custom_action(self, *, action_id, name, argv, categories=None,
                          requires_confirmation=True):
        if not isinstance(action_id, str) or not _ID.fullmatch(action_id):
            raise ActionError("invalid action ID")
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ActionError("name must contain 1..120 characters")
        if action_id in self._actions:
            raise ActionError("action ID already exists")
        if categories is not None and (
            not isinstance(categories, (list, tuple))
            or any(not isinstance(item, str) or len(item) > 40 for item in categories)
        ):
            raise ActionError("categories must be a list of short strings")
        return self._store({
            "action_id": action_id,
            "name": name.strip(),
            "categories": list(categories or []),
            "icon": None,
            "platform": "host",
            "argv": self._argv(argv),
            "enabled": False,
            "approved": False,
            "requires_confirmation": bool(requires_confirmation),
            "origin": "custom",
            "updated_at": int(time.time()),
        })

    def approve(self, action_id, *, enabled=True):
        with self._lock:
            item = self._actions.get(action_id)
            if item is None:
                raise ActionError("unknown action")
            self._argv(item.get("argv"))
            item["approved"] = True
            item["enabled"] = bool(enabled)
            item["updated_at"] = int(time.time())
            self._save()
        self._audit("approved" if enabled else "approved-disabled", action_id)

    def set_enabled(self, action_id, enabled):
        with self._lock:
            item = self._actions.get(action_id)
            if item is None:
                raise ActionError("unknown action")
            if enabled and not item.get("approved"):
                raise ActionError("action must be approved before enabling")
            item["enabled"] = bool(enabled)
            item["updated_at"] = int(time.time())
            self._save()
        self._audit("enabled" if enabled else "disabled", action_id)

    def revoke(self, action_id):
        with self._lock:
            if action_id not in self._actions:
                raise ActionError("unknown action")
            del self._actions[action_id]
            self._save()
        self._audit("revoked", action_id)

    def public_action(self, action_id):
        with self._lock:
            item = self._actions.get(action_id)
            if item is None:
                raise ActionError("unknown action")
            keys = ("action_id", "name", "categories", "icon", "platform",
                    "enabled", "approved", "requires_confirmation", "origin")
            return {key: item.get(key) for key in keys}

    def public_catalog(self):
        with self._lock:
            return [self.public_action(key) for key in sorted(self._actions)]

    def launch(self, action_id, *, confirmed=False, extra_args=None):
        """Start a desktop application and return immediately with its process ID."""
        argv = self._approved_argv(action_id, confirmed=confirmed, extra_args=extra_args)
        started = time.monotonic()
        options = {
            "args": argv,
            "shell": False,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "close_fds": True,
        }
        if os.name == "posix":
            options["start_new_session"] = True
        elif os.name == "nt":
            options["creationflags"] = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        try:
            process = subprocess.Popen(**options)
            self._audit("launched", action_id, pid=process.pid)
            return {
                "action_id": action_id,
                "started": True,
                "pid": process.pid,
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        except OSError as exc:
            self._audit("failed", action_id, error=str(exc)[:300])
            raise ActionError(f"could not start application: {exc}") from exc

    def run(self, action_id, *, confirmed=False, timeout=30.0, extra_args=None):
        """Run a bounded command and capture a short result; use launch() for desktop apps."""
        if not isinstance(timeout, (int, float)) or not 0 < timeout <= 300:
            raise ActionError("timeout must be between 0 and 300 seconds")
        argv = self._approved_argv(action_id, confirmed=confirmed, extra_args=extra_args)
        started = time.monotonic()
        try:
            result = subprocess.run(
                argv, shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, errors="replace", timeout=timeout, check=False,
                close_fds=True,
            )
            self._audit("executed", action_id, returncode=result.returncode)
            return {
                "action_id": action_id,
                "started": True,
                "returncode": result.returncode,
                "stdout": result.stdout[-8192:],
                "stderr": result.stderr[-8192:],
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        except subprocess.TimeoutExpired:
            self._audit("timeout", action_id)
            return {
                "action_id": action_id,
                "started": True,
                "timeout": True,
                "duration_seconds": round(time.monotonic() - started, 3),
            }
        except OSError as exc:
            self._audit("failed", action_id, error=str(exc)[:300])
            raise ActionError(f"could not execute action: {exc}") from exc

    def _audit(self, event, action_id, **details):
        entry = {"timestamp": int(time.time()), "event": event,
                 "action_id": action_id, **details}
        with self._lock:
            try:
                lines = self.audit_file.read_text(encoding="utf-8").splitlines()
            except FileNotFoundError:
                lines = []
            lines = (lines + [json.dumps(entry, ensure_ascii=False)])[-self.audit_limit:]
            fd, name = tempfile.mkstemp(prefix=".audit-", dir=self.state_dir)
            try:
                if os.name == "posix":
                    os.fchmod(fd, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write("\n".join(lines) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(name, self.audit_file)
            finally:
                try:
                    os.unlink(name)
                except FileNotFoundError:
                    pass
