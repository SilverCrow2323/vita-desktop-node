# Application Catalog and PC Actions

## Goal

The host maintains a normalized catalog of launchable desktop applications and user-defined actions. The PC Control Center and a future PS Vita browser will consume the same metadata model. The Vita must never parse operating-system menu files or receive executable shell strings.

## Linux discovery — implemented

The first provider indexes freedesktop desktop-entry application files from XDG_DATA_HOME/applications (normally `~/.local/share/applications`) and each applications directory under XDG_DATA_DIRS (normally `/usr/local/share` and `/usr/share`).

The scanner reads desktop-entry metadata, filters hidden and non-displayable entries, extracts name/categories/icon and derives a stable ID from the desktop file's relative path. It does not execute `Exec` while scanning and does not include raw command data in the public catalog.

This is an initial metadata scanner, not a complete freedesktop menu implementation. Localized names, OnlyShowIn / NotShowIn, TryExec validation, MIME activation and desktop action groups remain possible refinements.

## Host Action Manager — implemented locally

The Host Action Manager stores executable argv privately on the host. It supports registering discovered applications, creating custom actions from validated argv arrays, local approval and enable/disable state, explicit confirmation before execution, shell-free process launch, blocked shell/privilege-escalation frontends, revocation, bounded JSONL audit history and metadata-only public records.

When a discovered application's argv changes, its previous approval is invalidated and the action returns to a disabled state.

## PC Control Center — implemented locally

The Tkinter Control Center provides Linux catalog scanning/import, custom action creation, approval, enable/disable, local run confirmation, revocation and activity-log inspection. It is a host-local UI; it is not a remote Vita interface.

## Windows provider — pending

The catalog API is platform-neutral. A Windows provider is expected to enumerate Start Menu shortcuts and registered application entries, resolve shortcuts on the host and publish the same metadata shape. It must not expose Windows-specific executable paths or commands to the Vita.

## Vita-authored actions — future workflow

A paired Vita client may eventually propose a custom action containing an ID, display name, category and validated argument data. The host must store it disabled and require approval in the PC Control Center before it can be launched. Remote execution also requires a paired-device permission and host confirmation policy.

## Current implementation status

Implemented: Linux desktop-entry metadata scanning, stable IDs, safe public records, proposal validation, persistent host action storage, local approval/confirmation, execution audit and PC Control Center.

Not implemented: Windows discovery, VDN2 catalog transport, Vita catalog UI, remote action requests, pairing or remote confirmation.
