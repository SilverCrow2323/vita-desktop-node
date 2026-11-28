"""Registry for trusted, built-in add-on factories."""
from __future__ import annotations

from collections.abc import Callable

from .api import Addon, AddonManifest


class AddonRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Addon]] = {}

    def register(self, factory: Callable[[], Addon]) -> None:
        addon = factory()
        manifest = addon.manifest
        manifest.validate()
        if manifest.addon_id in self._factories:
            raise ValueError(f"duplicate add-on ID: {manifest.addon_id}")
        self._factories[manifest.addon_id] = factory

    def create(self, addon_id: str) -> Addon:
        try:
            return self._factories[addon_id]()
        except KeyError as exc:
            raise KeyError(f"unknown add-on: {addon_id}") from exc

    def manifests(self) -> tuple[AddonManifest, ...]:
        return tuple(self.create(addon_id).manifest for addon_id in sorted(self._factories))
