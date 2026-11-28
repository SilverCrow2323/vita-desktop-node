"""Public, deliberately small API surface exposed to built-in add-ons."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class AddonManifest:
    addon_id: str
    name: str
    version: str
    description: str
    api_version: int = 1
    permissions: tuple[str, ...] = ()
    built_in: bool = True

    def validate(self) -> None:
        if not self.addon_id or len(self.addon_id) > 160 or "." not in self.addon_id:
            raise ValueError("add-on ID must be a namespaced identifier")
        if not self.name or not self.version or not self.description:
            raise ValueError("add-on name, version and description are required")
        if self.api_version != 1:
            raise ValueError("unsupported add-on API version")
        if not self.built_in:
            raise ValueError("external add-ons are not supported by this host API yet")


@dataclass
class AddonContext:
    settings: dict[str, Any] = field(default_factory=dict)
    granted_permissions: frozenset[str] = frozenset()
    logger: Any = None


class Addon(Protocol):
    manifest: AddonManifest

    def register(self, context: AddonContext) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def unregister(self) -> None: ...
