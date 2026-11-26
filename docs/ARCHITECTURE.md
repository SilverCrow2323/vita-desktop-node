# Vita Desktop Node — Host Architecture

**Goal:** evolve VitaMon into a cross-platform, multi-node companion without breaking the existing PS Vita monitor.

## Current implementation boundary

Implemented host foundations:

- Legacy VMON1 telemetry compatibility path.
- VDN2 bounded JSON framing and envelope validation.
- Persistent node identity and capability inventory.
- XDG/Windows configuration path discovery and atomic JSON storage.
- Built-in add-on contracts, registry and lifecycle manager.
- Linux desktop-entry application catalog.
- Persistent host action manager with local approval, confirmation and audit.
- Tkinter PC Control Center for local Linux application/action management.
- Initial Linux Debian packaging foundation.
- Vita VPK identity and verification tooling.

Not implemented: VDN2 listener, TLS/pairing, remote catalog transport, Vita Direct Node transfer engine, PTY, remote display providers, mesh routing or multi-node orchestration.

## Design principles

1. Preserve the existing VMON1 Vita experience while the new client/server protocol is developed.
2. Separate platform integrations from product features.
3. Keep normal monitoring usable without administrator/root privileges.
4. Make optional capabilities discoverable; do not assume every OS, desktop or GPU exposes the same data.
5. Treat network peers as untrusted until explicitly paired.
6. Make every feature independently testable and disableable.
7. Keep executable commands and sensitive host paths on the host.

## Source layout

```text
server/
  vitamon_server.py
  vitamon_gui.py
  vdn/
    app.py
    config.py
    node.py
    protocol/
      framing.py
    addons/
    app_catalog.py
    action_manager.py
    control_center.py
    security/       # future pairing and credentials
    services/       # future terminal, files, display, etc.
    platforms/
      linux/
      windows/
  tests/vdn/
vita/
  src/              # existing VMON1 Vita client
  tools/            # VPK verification
packaging/
  debian/
  linux/
docs/
```

## Host platform strategy

### Linux first-class target

MX Linux/XFCE is the first Linux validation environment. Deliver a Debian package with desktop entry, launcher, dependencies and clean uninstall. AppImage is a later packaging target. Use XDG config/state/log/cache paths and optional autostart/tray integration.

Validate XFCE/X11 first. Wayland support varies by compositor and must be reported through capabilities. Use psutil, /proc and /sys as portable monitoring sources, then optional GPU/sensor providers. Missing sensors are unavailable, not zero.

### Windows

Retain the Windows distribution while moving registry autostart, GPU/sensor providers and display integrations behind platform adapters. Windows application catalog discovery is not implemented in the current milestone.

## Service boundaries

| Service | Responsibility | Current state |
|---|---|---|
| Node Core | Lifecycle, identity, capabilities | Foundation implemented |
| Protocol | Framing and envelope validation | Host framing implemented; no listener |
| Pairing | Device approval and credentials | Planned |
| Monitoring | Metrics and sensor adapters | Legacy telemetry path |
| Processes | Process inventory | Planned |
| Actions | Local approved application launch | Host-local implementation |
| Terminal | PTY allocation and lifecycle | Planned |
| Files | Sandboxed roots and chunked transfer | Planned |
| Notifications | Host/client messages | Planned |
| Network | LAN discovery and optional mesh routing | Planned |
| Display | Capture, virtual output and input | Planned |

## Display implementation

### Remote View

Capture and encode an existing desktop/session. Linux X11 capture differs from Wayland portal capture; Windows uses a separate provider. Select encoders/decoders through capability negotiation.

### Remote Desktop

Remote View plus interactive input, with a separate permission grant and visible host-side session status.

### Extended Display

Create or attach to a distinct virtual display output. Linux may require compositor/X server support, a virtual display driver or virtual output. Windows may require a dedicated virtual display driver or supported OS APIs.

A compressed copy of the primary desktop is Remote View, not Extended Display.

## Networking and trust

- LAN discovery is advisory; privileged requests require an authenticated session.
- VDN2 framing is not authentication.
- Tailscale is an optional routing layer, not a substitute for application-level pairing and authorization.
- No network endpoint may call the local action manager until authentication, per-device permissions, request validation and host confirmation are enforced.
- Never send secrets over VMON1 or plaintext discovery.

## Release discipline

Each milestone must include working code, tests, integration and user-facing documentation. See [Release 1](RELEASE_1.md) and [Release policy](RELEASE_POLICY.md).
