# PSVita Direct Node — Folder and Sync Design

## User-selected root folder

On first setup, the PC application asks where to create or use the **PSVita Direct Node** root folder. The selected path is stored in the user's host configuration. The user can change it later; moving an existing root must be an explicit operation with validation.

Initial structure:

```text
PSVita Direct Node/
  app/
  data/
  patch/
  downloads/
  media/
  backups/
  exports/
  queue/
  profiles/
  logs/
  .vdn/
    manifest.json
    index/
    conflicts/
    staging/
```

The first four folders are visible, user-facing drop zones requested for the initial workflow. Other folders may be created by the corresponding add-on. Internal metadata lives under `.vdn/` and is not intended for manual editing.

## Folder mapping

Every category has a configurable Vita destination and transfer policy. Do not hard-code unsafe or undocumented application paths. The UI must show the source folder, target device/path, free space and current policy before enabling synchronization.

## Transfer policies

- **Copy to Vita:** preserve the PC source; publish only after verification.
- **Move to Vita:** stage and verify the Vita copy first; delete the PC source only after an explicit policy permits it and the destination checksum is confirmed.
- **Two-way Sync:** compare manifests and content hashes; never resolve simultaneous edits by silently overwriting either side.
- **Watch Folder:** detect changes and enqueue work; it is a trigger, not a transfer policy itself.

The default is Copy to Vita. Move and two-way Sync require explicit opt-in.

## Reliability and safety

- Use temporary staging names and atomic rename where the destination filesystem supports it.
- Chunk large files; verify size and cryptographic hash after transfer.
- Persist queue state so interrupted transfers resume.
- Detect case sensitivity and filename restrictions on the Vita storage target.
- Protect against symlink/path traversal and root-folder escape.
- Detect conflicts (same path changed on both sides); preserve both copies until the user resolves them.
- Deletion propagation is off by default. A local deletion must not silently erase the remote copy.
- Exclude internal metadata, temporary files and logs from sync.
- Provide per-folder pause, bandwidth limit, Wi-Fi-only policy and device allow-list.

## Vita-side destination providers

Destination support must be provider-based (for example VitaShell-accessible storage, application data roots, or a future privileged integration). A provider declares its capabilities and safety constraints. Do not assume every Vita homebrew can write every system path.

## Status surface

Show queued, transferring, verifying, completed, paused, conflict and failed states. Include progress, speed, ETA where reliable, source/destination, last successful sync and a retry action.

## First implementation scope

The initial Linux port remains the current VMON host application. The folder root and synchronization engine are separate future add-ons; do not block the Linux telemetry port on a half-built sync feature.
