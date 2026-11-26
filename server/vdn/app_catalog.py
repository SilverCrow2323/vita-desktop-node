"""Cross-platform application catalog primitives.

Linux desktop entries are indexed as metadata only. Executable argv remains on the
host and is never included in the public catalog sent to the PS Vita.
"""
from __future__ import annotations

import configparser
import hashlib
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

_FIELD_CODE = re.compile(r"%(?:%|[fFuUdDnNickvm])")


@dataclass(frozen=True)
class Application:
    action_id: str
    name: str
    categories: tuple[str, ...]
    icon: str | None
    source: str
    launch_argv: tuple[str, ...]
    platform: str = "linux"

    def public_dict(self) -> dict[str, object]:
        """Safe catalog payload; host-only launch argv is intentionally omitted."""
        return {
            "action_id": self.action_id,
            "name": self.name,
            "categories": list(self.categories),
            "icon": self.icon,
            "source": self.source,
            "platform": self.platform,
        }


def _xdg_application_dirs(env: dict[str, str] | None = None) -> list[Path]:
    env = os.environ if env is None else env
    home = Path(env.get("HOME", str(Path.home())))
    data_home = Path(env.get("XDG_DATA_HOME", home / ".local" / "share"))
    data_dirs = env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share")
    roots = [data_home, *(Path(p) for p in data_dirs.split(":") if p)]
    result: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        candidate = root / "applications"
        key = str(candidate.resolve(strict=False))
        if key not in seen and candidate.is_dir():
            seen.add(key)
            result.append(candidate)
    return result


def _categories(parser: configparser.ConfigParser) -> tuple[str, ...]:
    raw = parser["Desktop Entry"].get("Categories", "")
    return tuple(dict.fromkeys(x for x in raw.split(";") if x))


def _stable_id(path: Path, desktop_root: Path) -> str:
    relative = path.relative_to(desktop_root).as_posix()
    digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:16]
    return "linux.desktop." + digest


def parse_desktop_file(path: Path, desktop_root: Path) -> Application | None:
    """Parse a visible Application desktop entry; never execute its Exec value."""
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        with path.open("r", encoding="utf-8") as handle:
            parser.read_file(handle)
        section = parser["Desktop Entry"]
    except (OSError, UnicodeError, configparser.Error, KeyError):
        return None

    if section.get("Type", "Application") != "Application":
        return None
    if section.get("Hidden", "false").lower() == "true":
        return None
    if section.get("NoDisplay", "false").lower() == "true":
        return None
    name = section.get("Name", "").strip()
    if not name:
        return None
    exec_value = section.get("Exec", "").strip()
    if not exec_value:
        return None
    try:
        argv = tuple(arg for arg in shlex.split(_FIELD_CODE.sub("", exec_value)) if arg)
    except ValueError:
        return None
    if not argv:
        return None

    icon = section.get("Icon", "").strip() or None
    return Application(
        action_id=_stable_id(path, desktop_root),
        name=name,
        categories=_categories(parser),
        icon=icon,
        source=path.name,
        launch_argv=argv,
    )


def scan_linux_applications(
    directories: Iterable[Path] | None = None,
) -> list[Application]:
    """Return visible desktop applications, deduplicated by desktop-file ID."""
    roots = list(_xdg_application_dirs() if directories is None else directories)
    found: dict[str, Application] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.desktop")):
            desktop_id = path.relative_to(root).as_posix().replace("/", "-")
            if desktop_id in found:
                continue
            app = parse_desktop_file(path, root)
            if app is not None:
                found[desktop_id] = app
    return sorted(found.values(), key=lambda app: app.name.casefold())


def validate_custom_action(payload: dict[str, object]) -> dict[str, object]:
    """Validate a Vita-authored action proposal before host-side approval."""
    name = str(payload.get("name", "")).strip()
    action_id = str(payload.get("action_id", "")).strip()
    argv = payload.get("argv")
    if not name or len(name) > 80:
        raise ValueError("name must contain 1..80 characters")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{2,95}", action_id):
        raise ValueError("action_id has an invalid format")
    if not isinstance(argv, list) or not argv or len(argv) > 32:
        raise ValueError("argv must be a non-empty list of at most 32 strings")
    if any(not isinstance(item, str) or not item or len(item) > 512 for item in argv):
        raise ValueError("argv entries must be non-empty strings up to 512 characters")
    categories = payload.get("categories", [])
    if not isinstance(categories, list) or any(
        not isinstance(item, str) or len(item) > 40 for item in categories
    ):
        raise ValueError("categories must be a list of short strings")
    return {
        "action_id": action_id,
        "name": name,
        "categories": list(dict.fromkeys(categories)),
        "argv": list(argv),
        "requires_confirmation": bool(payload.get("requires_confirmation", True)),
        "enabled": False,
        "origin": "vita-proposal",
    }
