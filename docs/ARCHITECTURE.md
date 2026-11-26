# Vita Desktop Node — Host Architecture

**Target:** evolve VitaMon into a cross-platform, multi-node companion without breaking the existing PS Vita monitor.

## Design principles
1. Preserve the existing VMON1 Vita experience while the new client/server protocol is developed.
2. Separate platform integrations from product features.
3. Keep normal monitoring usable without administrator/root privileges.
4. Make optional capabilities discoverable; do not assume every OS, desktop or GPU exposes the same data.
5. Treat network peers as untrusted until explicitly paired.
6. Make every feature independently testable and disableable.

## Proposed source layout
```text
server/
  vitamon_server.py          # existing VMON1 compatibility path
  vitamon_gui.py             # legacy GUI; refactor incrementally
  vdn/
    app.py                   # application lifecycle
    config.py                # XDG/Windows configuration
    node.py                  # node identity and capabilities
    protocol/                # framing, messages, sessions
    security/                # pairing, credentials, permissions, audit
    services/                # monitoring, processes, terminal, files, etc.
    platforms/
      linux/                 # XFCE/X11, sensors, display, packaging
      windows/               # desktop, sensors and display adapters
  tests/vdn/
```

The tree is a target layout, not a claim that these modules already exist.

## Host platform strategy
### Linux first-class target
MX Linux/XFCE is the first Linux validation environment. Deliver a Debian package (.deb) with desktop entry, icons, dependencies and clean uninstall; an AppImage; XDG config/state/log/cache paths; optional autostart and tray integration; and a headless-capable core.

Validate XFCE/X11 first. Wayland support varies by compositor and must be reported through capabilities. Use psutil, /proc and /sys as portable monitoring sources, then optional GPU/sensor providers. Missing sensors are unavailable, not zero.

### Windows
Retain the Windows distribution while moving registry autostart, DXGI, LibreHardwareMonitor and RTSS behind platform adapters. Produce an executable and portable ZIP after the new host entry point is stable.

## Service boundaries
| Service | Responsibility | Security boundary |
|---|---|---|
| Node Core | Lifecycle, identity, capabilities, sessions | Trusted local process |
| Protocol | Framing, validation, version negotiation | Reject malformed peers |
| Pairing | Device approval and credentials | Explicit user consent |
| Monitoring | Metrics and sensor adapters | Read-only |
| Processes | Process inventory | Read-only by default |
| Terminal | PTY allocation and lifecycle | Per-device permission; no implicit root |
| Files | Sandboxed roots and chunked transfer | Explicit shares and confirmations |
| Notifications | Host/client messages | Paired device only |
| Network | LAN discovery and optional mesh routing | No plaintext secrets |
| Display | Capture, virtual output and input | Separate view/control grants |

## Display implementation
### Remote View
Start with capture-provider discovery and a local preview/test harness. Linux X11 capture differs from Wayland portal capture; Windows uses a separate provider. Select encoders/decoders through capability negotiation.

### Extended Display
Treat virtual output creation as a host-specific provider. Linux may require compositor/X server support, a virtual display driver or virtual output. XFCE on X11 is the initial target to investigate; Wayland support varies. Windows may require a dedicated virtual display driver or supported OS APIs.

A compressed copy of the primary desktop is Remote View, not Extended Display.

## Networking
- LAN discovery is advisory; privileged requests require an authenticated session.
- Tailscale is an optional network path, not an application dependency.
- Investigate userspace WireGuard/lwIP work in the Vita ecosystem for reusable, independently licensed components. A Moonlight-specific integration is not automatically a general Tailscale client.
- Never install kernel modules, alter routing tables or create system-wide tunnels silently.
- Provide manual-IP pairing when discovery is blocked.

## Delivery milestones
| Milestone | Deliverable | Exit criteria |
|---|---|---|
| M0 — Foundation | Architecture and VDN2 baseline | Design committed |
| M1 — Host Core | Cross-platform entry point, config/logging, Linux packaging skeleton | Starts on Linux; VMON1 intact |
| M2 — VDN2 Core | Framing, validation, capability handshake and tests | Valid/invalid/oversized frame tests pass |
| M3 — Trust | Pairing, credentials, revocation, permissions, audit | Unpaired/revoked peers cannot invoke services |
| M4 — Monitoring | Unified metrics and process inventory | Linux/Windows availability is accurate |
| M5 — Terminal | Secure PTY sessions | Permission, timeout, disconnect and audit tests pass |
| M6 — Files + Network | Sandboxed transfer and optional mesh routing | Traversal, overwrite, resume and auth tests pass |
| M7 — Display | Remote View then Extended Display | Distinct modes; measured latency documented |
| M8 — Release | .deb, AppImage, Windows executable/ZIP, Vita VPK | Reproducible CI and installation tests |

## Immediate engineering task
Implement M1/M2 without rewriting the legacy GUI or changing the Vita VMON1 parser. Establish the server/vdn package and tests first; add Linux packaging after the new host entry point can start and stop cleanly.