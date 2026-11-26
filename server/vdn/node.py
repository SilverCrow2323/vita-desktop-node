"""Node identity and explicit capability inventory."""
from __future__ import annotations

import json
import platform
import uuid
from pathlib import Path
from typing import Any

from . import PROTOCOL_NAME, PROTOCOL_VERSION
from .config import AppPaths


def load_or_create_node_id(paths: AppPaths) -> str:
    """Return a persistent random node ID; it is an identifier, not an auth secret."""
    paths.ensure()
    identity_file = paths.state / "node-id"
    try:
        value = identity_file.read_text(encoding="ascii").strip()
        return str(uuid.UUID(value))
    except (OSError, ValueError):
        value = str(uuid.uuid4())
        temporary = identity_file.with_suffix(".tmp")
        temporary.write_text(value + "\n", encoding="ascii")
        if hasattr(temporary, "chmod"):
            temporary.chmod(0o600)
        temporary.replace(identity_file)
        return value


def build_node_info(paths: AppPaths) -> dict[str, Any]:
    """Describe implemented foundations without advertising planned features."""
    return {
        "protocol": {"name": PROTOCOL_NAME, "version": PROTOCOL_VERSION},
        "node_id": load_or_create_node_id(paths),
        "hostname": platform.node(),
        "platform": platform.system().lower(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "capabilities": {
            "telemetry.vmon1": True,
            "vdn2.framing": True,
            "vdn2.pairing": False,
            "terminal.pty": False,
            "files.transfer": False,
            "network.mesh": False,
            "display.remote_view": False,
            "display.extended": False,
        },
    }


def render_node_info(paths: AppPaths) -> str:
    return json.dumps(build_node_info(paths), ensure_ascii=False, indent=2)
