# PC Control Center

The PC Control Center is a host-local Tkinter window opened from the desktop
monitor. It provides four operator workflows:

1. Scan Linux XDG desktop entries and import applications into the persistent
   host action store.
2. Add a custom action by entering a display name and an executable plus
   arguments. The command line is parsed into an argv list; no shell is used.
3. Approve and enable, disable, run with an explicit confirmation, or revoke
   an action.
4. Inspect the bounded local action audit log.

## Application discovery

The first provider scans visible Linux `.desktop` entries. Hidden and
NoDisplay entries are excluded by the catalog scanner. Scanning does not
execute applications. New entries are disabled and unapproved.

Windows application discovery is not part of this milestone. The UI reports
that limitation instead of pretending to have scanned Windows Start Menu
shortcuts.

## Custom actions

The command field is parsed with shell-style quoting into an argv array, but
is never passed to a shell. For example:

    firefox --new-window

The action is created disabled and unapproved. The user must approve it and
then explicitly confirm each launch. Shell interpreters and privilege
escalation frontends are rejected by the host action manager.

## State and security

Actions and audit data are stored below the user's Vita Desktop Node state
directory (XDG state path on Linux, Local AppData on Windows). The PC Control
Center is a local GUI only. It does not expose approval or execution through
the network, and it does not yet communicate with the PS Vita over VDN2.

The Vita-facing public catalog continues to omit executable argv. A future
VDN2 bridge must add pairing, per-device authorization, request validation
and a distinct confirmation handshake before any remote launch can be enabled.

## Current limitations

- Linux XDG desktop-entry discovery only; Windows discovery is pending.
- No remote action transport or Vita UI yet.
- The GUI uses Tkinter and requires a graphical desktop session.
