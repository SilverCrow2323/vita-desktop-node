"""Bounded VDN2 JSON framing.

Wire format: 4-byte unsigned big-endian payload length + UTF-8 JSON object.
This module deliberately contains no socket policy, TLS setup or authorization.
"""
from __future__ import annotations

import asyncio
import json
import struct
from typing import Any

PROTOCOL_NAME = "VDN2"
PROTOCOL_VERSION = 2
DEFAULT_MAX_FRAME = 1024 * 1024
_HEADER = struct.Struct("!I")


class FrameError(ValueError):
    """The peer sent an invalid or unsupported VDN2 frame."""


def validate_envelope(message: Any) -> dict[str, Any]:
    """Validate the common VDN2 envelope; method-specific validation is separate."""
    if not isinstance(message, dict):
        raise FrameError("message must be a JSON object")
    if message.get("protocol") != PROTOCOL_NAME:
        raise FrameError("unsupported protocol")
    if message.get("version") != PROTOCOL_VERSION:
        raise FrameError("unsupported protocol version")
    if message.get("type") not in {"request", "response", "event"}:
        raise FrameError("invalid message type")
    identifier = message.get("id")
    if not isinstance(identifier, str) or not identifier or len(identifier) > 128:
        raise FrameError("invalid message id")
    if message["type"] == "request":
        method = message.get("method")
        if not isinstance(method, str) or not method or len(method) > 128:
            raise FrameError("invalid request method")
        if not isinstance(message.get("params", {}), dict):
            raise FrameError("request params must be an object")
    elif message["type"] == "response":
        if not isinstance(message.get("ok"), bool):
            raise FrameError("response must contain boolean ok")
        if message["ok"] and not isinstance(message.get("result", {}), dict):
            raise FrameError("successful response result must be an object")
        if not message["ok"] and not isinstance(message.get("error"), dict):
            raise FrameError("failed response must contain an error object")
    else:
        event = message.get("event")
        if not isinstance(event, str) or not event or len(event) > 128:
            raise FrameError("invalid event name")
        if not isinstance(message.get("data", {}), dict):
            raise FrameError("event data must be an object")
    session = message.get("session")
    if session is not None and (not isinstance(session, str) or len(session) > 128):
        raise FrameError("invalid session id")
    return message


def encode_frame(message: dict[str, Any], *, max_frame: int = DEFAULT_MAX_FRAME) -> bytes:
    """Validate and encode one VDN2 envelope."""
    validate_envelope(message)
    try:
        payload = json.dumps(
            message, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise FrameError("message is not valid JSON data") from exc
    if not payload or len(payload) > max_frame:
        raise FrameError("frame size outside permitted bounds")
    return _HEADER.pack(len(payload)) + payload


def decode_payload(payload: bytes, *, max_frame: int = DEFAULT_MAX_FRAME) -> dict[str, Any]:
    """Decode and validate a JSON payload after its length header has been removed."""
    if not payload or len(payload) > max_frame:
        raise FrameError("frame size outside permitted bounds")
    try:
        message = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FrameError("invalid UTF-8 JSON payload") from exc
    return validate_envelope(message)


def decode_frame(frame: bytes, *, max_frame: int = DEFAULT_MAX_FRAME) -> dict[str, Any]:
    """Decode exactly one complete length-prefixed frame."""
    if len(frame) < _HEADER.size:
        raise FrameError("truncated frame header")
    (length,) = _HEADER.unpack(frame[:_HEADER.size])
    if length == 0 or length > max_frame:
        raise FrameError("frame size outside permitted bounds")
    if len(frame) != _HEADER.size + length:
        raise FrameError("frame length does not match header")
    return decode_payload(frame[_HEADER.size:], max_frame=max_frame)


async def read_frame(
    reader: asyncio.StreamReader, *, max_frame: int = DEFAULT_MAX_FRAME
) -> dict[str, Any]:
    """Read one bounded frame from an asyncio stream."""
    try:
        header = await reader.readexactly(_HEADER.size)
        (length,) = _HEADER.unpack(header)
        if length == 0 or length > max_frame:
            raise FrameError("frame size outside permitted bounds")
        payload = await reader.readexactly(length)
    except asyncio.IncompleteReadError as exc:
        raise FrameError("connection closed during frame") from exc
    return decode_payload(payload, max_frame=max_frame)


async def write_frame(
    writer: asyncio.StreamWriter,
    message: dict[str, Any],
    *,
    max_frame: int = DEFAULT_MAX_FRAME,
) -> None:
    """Write one complete frame and drain the stream."""
    writer.write(encode_frame(message, max_frame=max_frame))
    await writer.drain()
