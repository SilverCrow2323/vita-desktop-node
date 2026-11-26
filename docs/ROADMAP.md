# Vita Desktop Node Roadmap

The roadmap tracks user-visible product milestones. Each item is labelled by its real implementation state; documentation alone never means a feature is shipped.

## R1 — Host foundation

**Current milestone.** Establish the cross-platform host foundation while preserving VMON1 telemetry.

- [x] VDN2 bounded JSON framing and envelope validation.
- [x] Persistent host node identity and capability inventory.
- [x] XDG/Windows config path discovery and atomic config storage.
- [x] Built-in add-on API, registry and lifecycle manager.
- [x] Initial Linux host integration and Debian package build foundation.
- [x] Linux desktop-entry application catalog scanner.
- [x] Persistent host action manager with local approval, confirmation and audit.
- [x] PC Control Center for local application/action management.
- [x] Vita VPK identity update and package verification tooling.
- [x] Preserve the legacy VMON1 telemetry path.
- [ ] Full CI pass and physical PS Vita / clean Linux installation validation.
- [ ] Publish Release 1 artifacts after release gates pass.

Release 1 scope and acceptance criteria: [RELEASE_1.md](RELEASE_1.md).

## R2 — VDN2 bridge and desktop interaction

- Host TCP/TLS service and capability handshake.
- Explicit short-lived pairing, per-device credentials, revocation and host identity pinning.
- Per-device authorization and audited request dispatch.
- Sync application catalog metadata to paired Vita clients.
- Vita catalog browser and host-confirmed PC action requests.
- Remote View / screen mirroring.
- Interactive Remote Desktop with separately authorized input.
- Extended Display through platform-specific virtual-display providers.

Remote View, Remote Desktop and Extended Display are three distinct capabilities.

## R3 — PSVita Direct Node and Transfer Center

- User-selected PSVita Direct Node root and managed folders.
- Explicit destination mapping and free-space checks.
- Copy/Move jobs, progress, checksums, resume and queue persistence.
- Safe staging and interrupted-transfer recovery.

## R4 — Folder Watcher

- Watch selected Direct Node folders and enqueue changes.
- Debounce, ignore rules and per-folder pause.
- Non-destructive defaults; watcher is not itself a sync policy.

## R5 — Two-Way Sync

- Manifest comparison, conflict detection and explicit resolution.
- Version history and preserved conflicting copies.
- Deletions are not propagated by default.

## R6 — Vita Quick Dock

- Connection, telemetry, transfers, notifications and shortcuts.
- Customizable Vita button combinations.
- Clear status and recovery actions.

## R7 — Secure Terminal and Automation

- Authenticated PTY with scoped per-device permissions.
- Audit trail, timeouts, disconnect cleanup and privileged-operation confirmations.
- Approved automation actions; no unrestricted shell endpoint.

## R8 — Multi-Node and mesh networking

- Multiple PCs and Vita clients.
- LAN discovery and optional Tailscale/WireGuard routing.
- Node-level permissions, synchronized catalogs and per-node trust.

## Release discipline

A milestone is complete only when working code, tests, integration and user documentation agree. A planned feature must never be advertised as shipped. See [Release policy](RELEASE_POLICY.md).
