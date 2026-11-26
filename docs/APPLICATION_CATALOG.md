# Application Catalog and PC Actions

## Goal

The host maintains one normalized catalog of launchable desktop applications and
user-defined actions. The PC editor and PS Vita browser consume the same catalog.
The Vita never parses operating-system menu files and never receives an executable
shell string.

## Linux discovery

The first provider indexes freedesktop desktop-entry application files from:

- XDG_DATA_HOME/applications (normally ~/.local/share/applications)
- Each applications directory under XDG_DATA_DIRS (normally /usr/local/share
  and /usr/share)

The scanner reads desktop-entry metadata, filters hidden and non-displayable
entries, extracts name/categories/icon, and derives a stable ID from the desktop
file's relative path. It does not execute Exec while scanning and does not
include the raw command in the public catalog payload.

The initial scanner is a metadata provider, not yet a complete freedesktop menu
implementation: desktop-file precedence is handled by desktop-file ID, while
localized names, OnlyShowIn / NotShowIn, TryExec validation, MIME activation,
and desktop action groups are future refinements.

## Windows provider

The catalog API is platform-neutral. A Windows provider will enumerate Start Menu
shortcuts and registered application entries, resolve shortcuts on the host, and
publish the same metadata shape. It must not make Windows-specific paths or
commands part of the Vita protocol.

## Vita-authored actions

The Vita can propose a custom action containing an ID, display name, category,
and an argv array. The host validates the proposal and stores it as disabled.
A user must approve it in the PC Command Center before it can be launched.
Arguments are an array, not a shell command string; execution must use a
non-shell process API. Privileged actions require an additional confirmation.

## Synchronization and conflict rules

- The host is authoritative for whether an action is approved and enabled.
- Both clients may edit presentation metadata (name, category, icon, ordering).
- Vita-created actions enter a pending-approval state.
- Stable IDs identify actions across reconnects; catalog revisions identify changes.
- A removed application becomes unavailable, not an instruction to delete user data.
- Per-device permissions decide which actions each paired Vita may invoke.

## Catalog record

The public record contains action_id, name, categories, icon, source, and platform.
Executable details remain host-side and are never sent as an arbitrary shell string
to the Vita.

## Current implementation status

Implemented: Linux desktop-entry metadata scanning, stable IDs, safe public records,
Vita action proposal validation, and tests.

Not implemented yet: persistent action database, PC graphical editor, Windows
discovery provider, VDN2 catalog transport, Vita catalog UI, and action execution.
