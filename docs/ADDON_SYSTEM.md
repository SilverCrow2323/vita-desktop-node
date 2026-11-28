# Vita Desktop Node — Add-on System

**Goal:** ship one meaningful, independently testable capability per release without turning the host application into a monolith.

## Add-on contract

Each add-on is a self-contained module with:
- a stable unique ID (reverse-DNS style, e.g. `org.vdn.filesync`);
- display name, version, description, author and license;
- minimum host API version and declared capabilities;
- explicit settings schema and default values;
- lifecycle hooks: `register(context)`, optional `start()`, `stop()`, `unregister()`;
- permission declarations and structured health/status reporting;
- unit tests and a short user-facing help page.

The host owns the lifecycle, permissions, settings, logging and UI registration. Add-ons must not import or modify private host internals. Dependencies and optional integrations are declared rather than silently installed.

## Initial repository layout

```text
server/
  vdn/
    core/                 # stable host API, events, settings, permissions
    addons/
      api.py              # public add-on contracts
      registry.py         # discovery and metadata validation
      manager.py          # enable/disable and lifecycle
      builtins/
        system_monitor/   # migrated existing monitoring capability
        folder_sync/      # later: PSVita Direct Node synchronizer
        quick_actions/    # later: Vita-to-PC action catalogue
  tests/
    addons/
` ```

This is the target structure. Add-on loading must not execute arbitrary third-party code merely because a folder exists. Initially, only built-in, explicitly enabled add-ons are loaded. External add-ons require signing/trust policy and permission review before support is enabled.

## Capability and permission model

Add-ons request narrow capabilities such as:
- `host.metrics.read`
- `host.processes.read`
- `host.notifications.send`
- `host.actions.invoke`
- `filesystem.shared_roots.read`
- `filesystem.shared_roots.write`
- `network.peer.connect`
- `display.capture`

The user sees the requested permissions before enabling an add-on. Sensitive capabilities default to denied. Add-ons cannot grant permissions to themselves.

## UI integration

Each add-on may register:
- one settings page;
- one optional dashboard card;
- context actions for supported objects;
- help/about content including technical explanation, author and credits.

The host supplies consistent layout, localization, accessibility and status indicators. Add-ons must not create their own unrelated tray icons or background daemons.

## Release rule

A release must include at least one user-visible, tested improvement over the previous release. It may also contain internal refactors and fixes, but a milestone is not called complete until its feature works end-to-end and has documented limitations.
