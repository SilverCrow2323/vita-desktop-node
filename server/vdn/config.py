"""Cross-platform paths and small, permission-conscious JSON configuration."""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppPaths:
    config: Path
    state: Path
    cache: Path
    logs: Path

    @classmethod
    def discover(cls, *, app_name: str = "VitaDesktopNode") -> "AppPaths":
        home = Path.home()
        if os.name == "nt":
            roaming = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
            local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            return cls(roaming / app_name, local / app_name / "state",
                       local / app_name / "cache", local / app_name / "logs")
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        state_home = Path(os.environ.get("XDG_STATE_HOME", home / ".local" / "state"))
        cache_home = Path(os.environ.get("XDG_CACHE_HOME", home / ".cache"))
        return cls(config_home / app_name.lower(), state_home / app_name.lower(),
                   cache_home / app_name.lower(), state_home / app_name.lower() / "logs")

    def ensure(self) -> None:
        for path in (self.config, self.state, self.cache, self.logs):
            path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, *, default: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load an object-valued JSON file; malformed or missing files use defaults."""
    fallback = dict(default or {})
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
        return value if isinstance(value, dict) else fallback
    except (OSError, UnicodeError, json.JSONDecodeError):
        return fallback


def save_json(path: Path, value: dict[str, Any]) -> None:
    """Atomically save JSON and restrict newly-created config files to the user."""
    if not isinstance(value, dict):
        raise TypeError("configuration root must be an object")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        if os.name != "nt":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            path.chmod(0o600)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
