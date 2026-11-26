# Vita Desktop Node Roadmap

The roadmap distinguishes implemented foundations from planned release scope.

## R1 — Host foundation

- Linux host integration and Debian packaging foundation.
- VDN2 length-prefixed framing and host identity/configuration.
- Add-on lifecycle foundation and initial documentation.
- Preserve the original VMON1 telemetry path.

## R2 — Direct Node and desktop interaction

- User-selected PSVita Direct Node root and managed folders.
- Host application catalog, Linux desktop-entry provider, Windows application provider.
- PC Command Center and Vita catalog browser.
- Vita-authored custom-action proposals with host approval.
- PC Actions with per-device permissions and confirmation policy.
- Remote View / screen mirroring.
- Remote Desktop with separately authorized input.
- Extended Display through platform-specific virtual-display providers.

## R3 — Transfer Center

- Copy and Move jobs, progress, checksums, resume, and queue persistence.
- Explicit destination mapping and safe handling of interrupted transfers.

## R4 — Folder Watcher

- Watch selected Direct Node folders and enqueue changes.
- Debounce, ignore rules, and non-destructive defaults.

## R5 — Two-Way Sync

- Conflict detection, version history, and explicit conflict resolution.
- Deletions are not propagated by default.

## R6 — Vita Quick Dock

- Connection, telemetry, transfers, notifications, and shortcuts.
- Customizable Vita button combinations.

## R7 — Secure Terminal and Automation

- Authenticated PTY, scoped permissions, audit trail, timeouts, and privileged
  operation confirmations.
- Approved automation actions; no unrestricted shell endpoint.

## R8 — Multi-Node

- Multiple PCs and Vita clients, LAN and mesh routing, node-level permissions,
  and synchronized catalogs.

A release is not considered complete merely because its documentation exists.
Each release must ship at least one new, tested user-facing capability, and every
platform-specific limitation must be stated explicitly.
\n\n### PC Control Center implementation\nThe local Tkinter Control Center now scans Linux desktop entries, creates custom argv actions, manages approvals and revocations, runs confirmed local actions, and displays the audit log. Windows discovery and Vita/VDN2 transport remain pending.\n