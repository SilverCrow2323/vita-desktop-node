"""Lifecycle manager with explicit enablement and permission grants."""
from __future__ import annotations

from .api import AddonContext
from .registry import AddonRegistry


class AddonManager:
    def __init__(self, registry: AddonRegistry) -> None:
        self.registry = registry
        self._running: dict[str, object] = {}

    def enable(
        self,
        addon_id: str,
        *,
        settings: dict | None = None,
        granted_permissions: frozenset[str] = frozenset(),
        logger=None,
    ) -> None:
        if addon_id in self._running:
            return
        addon = self.registry.create(addon_id)
        requested = frozenset(addon.manifest.permissions)
        if not requested.issubset(granted_permissions):
            missing = ", ".join(sorted(requested - granted_permissions))
            raise PermissionError(f"missing add-on permissions: {missing}")
        context = AddonContext(
            settings=dict(settings or {}),
            granted_permissions=granted_permissions,
            logger=logger,
        )
        addon.register(context)
        try:
            addon.start()
        except Exception:
            addon.unregister()
            raise
        self._running[addon_id] = addon

    def disable(self, addon_id: str) -> None:
        addon = self._running.pop(addon_id, None)
        if addon is None:
            return
        try:
            addon.stop()
        finally:
            addon.unregister()

    def stop_all(self) -> None:
        for addon_id in tuple(self._running):
            self.disable(addon_id)

    def running(self) -> tuple[str, ...]:
        return tuple(sorted(self._running))
