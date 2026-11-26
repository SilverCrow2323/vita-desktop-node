# Vita Desktop Node

**A PS Vita + PC companion evolving from VitaMon into a modular desktop node.**

Vita Desktop Node (VDN) keeps the existing PS Vita telemetry experience working while building a larger host-side ecosystem: Linux/Windows desktop integration, a secure node protocol, application catalog, approval-gated PC actions, file workflows, remote desktop capabilities and multi-node networking.

> **Current development release:** the Vita application still uses the legacy VMON1 telemetry protocol. The host now includes a pairing store, local device-approval controls and a TLS-only read-only service foundation. Automatic listener/certificate setup and the Vita-side VDN2 client are still pending. Read [Release 1 scope](docs/RELEASE_1.md) before treating any roadmap item as available.

<div align="center">

[![Build](https://github.com/SilverCrow2323/vita-desktop-node/actions/workflows/build.yml/badge.svg)](https://github.com/SilverCrow2323/vita-desktop-node/actions/workflows/build.yml)
[![Latest release](https://img.shields.io/github/v/release/SilverCrow2323/vita-desktop-node?include_prereleases&label=download)](https://github.com/SilverCrow2323/vita-desktop-node/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

## Project status

| Component | Status | What is actually available |
|---|---|---|
| PS Vita telemetry | Implemented | Existing VMON1 dashboard and UDP telemetry |
| VDN2 framing | Implemented | Bounded length-prefixed JSON framing and validation |
| Host identity/config | Implemented | Persistent node ID and per-user XDG/Windows paths |
| Linux host integration | Foundation | XDG config, autostart, single-instance lock and Debian packaging |
| Add-on framework | Foundation | Built-in add-on contracts, registry and lifecycle manager |
| Linux application catalog | Implemented | XDG `.desktop` metadata scanner |
| Host Action Manager | Implemented locally | Persistent actions, local approval, confirmation, audit and shell-free argv execution |
| PC Control Center | Implemented locally | Tkinter UI for Linux app import, custom actions and local action management |
| VDN2 pairing/network bridge | Host foundation | One-time pairing, local approval, revocation and TLS service class; no automatic listener startup or Vita client yet |
| PSVita Direct Node sync | Planned | Folder design documented; no transfer engine |
| Remote View / Remote Desktop / Extended Display | Planned | Separate product modes; no streaming provider shipped |
| Secure PTY / mesh / multi-node | Planned | Security and architecture requirements documented |

The status above describes repository code, not aspirations. A documented feature is not considered implemented.

## Release 1

Release 1 is the **host foundation and local desktop-control milestone**. It focuses on a usable host-side base while preserving the original Vita telemetry path.

Included foundations:

- VDN2 framing with a 4-byte big-endian length prefix, UTF-8 JSON envelopes and a 1 MiB default frame limit.
- Persistent host node identity and capability reporting.
- XDG-aware Linux configuration/state paths and Windows path discovery.
- Initial Linux desktop integration and Debian package build.
- Built-in add-on API, registry and lifecycle manager.
- Linux XDG application discovery.
- Persistent host-side action storage, explicit approval, confirmation before execution and bounded audit log.
- PC Control Center for local application/action management and VDN2 device pairing/revocation, including command review before approval.\n- Desktop application launch returns immediately with a process ID instead of waiting for the GUI app to close.
- Vita VPK identity and verification tooling, while retaining VMON1 compatibility.

**Not included in Release 1:** VDN2 pairing, remote PC actions from Vita, catalog synchronization, file transfer/sync, terminal, remote display, Tailscale integration or multi-node control.

See [Release 1 scope and acceptance checklist](docs/RELEASE_1.md).

## Downloads and installation

Use the repository's [GitHub Releases](https://github.com/SilverCrow2323/vita-desktop-node/releases) page. Do not use the upstream VitaMon release page for VDN builds.

Expected release artifacts are:

| Artifact | Target | Notes |
|---|---|---|
| `VitaDesktopNode.vpk` | PS Vita | Built with VitaSDK; current client remains VMON1 telemetry |
| `vitamon_*_all.deb` | Debian-based Linux | Initial host package; legacy internal launcher/package naming is retained during transition |
| Windows executable / ZIP | Windows | Compatibility build; check the release notes for availability |

A CI artifact is not automatically a hardware-certified release. The release notes must identify which artifacts were actually built and tested.

### Linux build

On MX Linux, Debian or Ubuntu, install the build dependencies:

```sh
sudo apt install python3 python3-tk python3-psutil python3-pil python3-pystray dpkg-dev
./packaging/linux/build-deb.sh
```

The package is written to `dist/`. For full installation, build details and current limitations, see [Linux installation](docs/LINUX_INSTALL.md).

### Vita build

With VitaSDK and CMake installed:

```sh
cd vita
cmake -S . -B build
cmake --build build --parallel
python3 tools/verify_vpk.py build/VitaDesktopNode.vpk
```

See [Vita client preview](docs/VITA_CLIENT_PREVIEW.md) for identity, installation and the precise feature boundary.

## Host development

Run the host-core information command:

```sh
PYTHONPATH=server python -m vdn.app --print-info
```

Run the host unit tests:

```sh
PYTHONPATH=server python -m unittest discover -s server/tests/vdn -v
```

The capability report is deliberately conservative. Host-side pairing primitives do not mean the Vita can pair yet; PTY, file transfer, mesh networking and display capabilities remain unavailable.

## Architecture and documentation

- [VDN2 Pairing & Host Service](docs/VDN2_PAIRING_HOST_SERVICE.md)
- [Release 1 scope and checklist](docs/RELEASE_1.md)
- [Roadmap R1–R8](docs/ROADMAP.md)
- [Host architecture](docs/ARCHITECTURE.md)
- [VDN2 protocol and security baseline](docs/VDN2_PROTOCOL.md)
- [VDN2 Pairing & Host Service](docs/VDN2_PAIRING_HOST_SERVICE.md)
- [Linux installation and Debian packaging](docs/LINUX_INSTALL.md)
- [Vita client preview and limitations](docs/VITA_CLIENT_PREVIEW.md)
- [Add-on framework](docs/ADDON_SYSTEM.md)
- [Application catalog](docs/APPLICATION_CATALOG.md)
- [Host Action Manager](docs/HOST_ACTION_MANAGER.md)
- [PC Control Center](docs/PC_CONTROL_CENTER.md)
- [PSVita Direct Node folder/sync design](docs/PSVITA_DIRECT_NODE_SYNC.md)
- [Remote View, Remote Desktop and Extended Display](docs/R2_DISPLAY_REMOTE.md)
- [Release policy](docs/RELEASE_POLICY.md)

## Product direction

VDN is designed as a set of independently testable services:

1. **Monitor** — preserve and extend the existing telemetry dashboard.
2. **Direct Node** — a user-selected `PSVita Direct Node` root with app/data/patch/download drop zones, transfer queue and safe synchronization.
3. **PC Control** — an application catalog and host-approved actions initiated from the Vita.
4. **Quick Dock** — connection state, telemetry, transfers, notifications and shortcuts on the Vita.
5. **Remote Desktop** — Remote View, interactive Remote Desktop and true Extended Display as distinct modes.
6. **Secure Terminal and Automation** — paired, scoped, audited and confirmation-gated.
7. **Multi-Node** — multiple PCs/Vita clients over LAN and optional mesh networking.

The intended first Linux validation environment is MX Linux/XFCE. Windows compatibility is retained. Linux X11 and Wayland, Windows display providers and Vita hardware capabilities are treated separately rather than assumed interchangeable.

## Security principles

- VMON1 remains telemetry-only; no credentials, files, terminal input or privileged commands are sent through it.
- VDN2 framing is not authentication. No network-facing action execution is enabled until pairing and authorization exist.
- Public action records contain metadata, never executable argv.
- Host actions are disabled until locally approved and require explicit confirmation to run.
- Process creation uses argv with `shell=False`; shell interpreters and privilege-escalation frontends are rejected.
- Future file services must be rooted in explicit shares, reject traversal and default to non-destructive behavior.
- Remote View, Remote Desktop input and Extended Display require separate capability grants.

## Compatibility and credits

Vita Desktop Node is a fork and continuation of [VitaPCMonitor](https://github.com/MrWhite2312-IS/VitaPCMonitor). The original VMON1 telemetry path and Vita dashboard are preserved while the host and product architecture are being expanded. Upstream authors and third-party component authors retain their respective credits and licenses; see the repository license and source headers.

## Contributing

Issues and pull requests are welcome. Please include the host OS/desktop environment, Python version, Vita firmware and exact build/test commands when reporting a problem. Do not report roadmap-only functionality as a regression in the current release.
