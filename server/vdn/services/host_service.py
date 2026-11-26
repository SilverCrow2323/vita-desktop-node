"""TLS-only VDN2 host service exposing a minimal read-only node API."""
from __future__ import annotations

import asyncio
import ssl
import uuid
from typing import Callable

from .. import PROTOCOL_NAME, PROTOCOL_VERSION
from ..protocol.framing import FrameError, read_frame, write_frame
from ..security.pairing import PairingError, PairingStore

MAX_CLIENTS = 8
MAX_FRAME = 1024 * 1024


class HostService:
    """No action, terminal, file, or display methods are registered here."""

    def __init__(self, pairing: PairingStore, node_info: Callable[[], dict]):
        self.pairing = pairing
        self.node_info = node_info
        self._server = None
        self._clients = set()

    @staticmethod
    def _response(message_id: str, *, result=None, error=None) -> dict:
        response = {
            "protocol": PROTOCOL_NAME, "version": PROTOCOL_VERSION,
            "type": "response", "id": message_id,
        }
        if error is None:
            response.update({"ok": True, "result": result or {}})
        else:
            response.update({"ok": False, "error": {"code": error[0], "message": error[1]}})
        return response

    def dispatch(self, message: dict) -> dict:
        """Dispatch one validated request. Pairing request never grants access."""
        message_id = message.get("id", str(uuid.uuid4()))
        try:
            if message.get("type") != "request":
                raise PairingError("only request messages are accepted")
            method = message["method"]
            params = message.get("params", {})
            if method == "pairing.request":
                result = self.pairing.request_pairing(
                    code=params.get("code"),
                    device_id=params.get("device_id"),
                    device_name=params.get("device_name"),
                    requested_permissions=params.get("requested_permissions", []),
                )
                return self._response(message_id, result=result)
            if method not in {"node.info", "node.capabilities"}:
                return self._response(message_id, error=("method_not_found", "method is not available"))
            auth = params.get("auth")
            if not isinstance(auth, dict):
                raise PairingError("device authentication is required")
            permission = "node.info"
            identity = self.pairing.authenticate(
                device_id=auth.get("device_id"),
                credential=auth.get("credential"),
                required_permission=permission,
            )
            info = self.node_info()
            if method == "node.capabilities":
                result = {"node_id": info.get("node_id"), "capabilities": info.get("capabilities", {})}
            else:
                result = info
            result = dict(result)
            result["authenticated_device"] = identity["device_id"]
            return self._response(message_id, result=result)
        except (PairingError, KeyError, TypeError, ValueError) as exc:
            return self._response(message_id, error=("request_rejected", str(exc)))

    async def _client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        task = asyncio.current_task()
        if len(self._clients) >= MAX_CLIENTS:
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass
            return
        self._clients.add(task)
        try:
            while True:
                try:
                    message = await read_frame(reader, max_frame=MAX_FRAME)
                except (FrameError, asyncio.IncompleteReadError):
                    break
                response = self.dispatch(message)
                await write_frame(writer, response, max_frame=MAX_FRAME)
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            self._clients.discard(task)
            writer.close()
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass

    async def start(self, host: str, port: int, *, tls_context: ssl.SSLContext):
        """Start a TLS-only listener. A server certificate/key must be configured."""
        if not isinstance(tls_context, ssl.SSLContext):
            raise ValueError("a configured TLS server context is required")
        if tls_context.protocol != ssl.PROTOCOL_TLS_SERVER:
            raise ValueError("TLS context must use PROTOCOL_TLS_SERVER")
        tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
        self._server = await asyncio.start_server(
            self._client, host, int(port), ssl=tls_context,
            limit=MAX_FRAME + 4,
        )
        return self._server

    async def close(self):
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        clients = list(self._clients)
        for task in clients:
            task.cancel()
        if clients:
            await asyncio.gather(*clients, return_exceptions=True)
