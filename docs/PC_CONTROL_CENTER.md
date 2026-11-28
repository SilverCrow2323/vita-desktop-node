# PC Control Center

The PC Control Center is a host-local Tkinter window opened from the desktop monitor. It manages the applications and actions that the PC is willing to expose to future paired Vita clients; in the current milestone, all operations remain local to the PC.

## Available workflows

1. Scan Linux XDG desktop entries and import applications into the persistent host action store.
2. Add a custom action by entering a display name and executable plus arguments. The command line is parsed into an argv list; no shell is used.
3. Approve and enable, disable, launch with explicit confirmation, or revoke an action.
4. Inspect the bounded local action audit log.
5. Open a short-lived VDN2 pairing window, review pending device requests, grant a permission subset, issue a one-time credential and revoke paired devices.

## Application discovery

The first provider scans visible Linux `.desktop` entries. Hidden and NoDisplay entries are excluded by the catalog scanner. Scanning does not execute applications. New entries are disabled and unapproved.

Windows application discovery is not part of this milestone. The UI reports that limitation instead of pretending to have scanned Windows Start Menu shortcuts.

## Custom actions

The command field is parsed with shell-style quoting into an argv array, but is never passed to a shell. For example:

```text
firefox --new-window
```

The action is created disabled and unapproved. The user must approve each action locally. Before approval, the Control Center displays the exact host-side executable and argument vector for review. Every launch still requires a separate confirmation. Shell interpreters and privilege-escalation frontends are rejected by the host action manager.

## Launch behavior

The Run action starts a desktop application as a detached process and returns its PID immediately. It does not wait for a browser, game launcher or other GUI process to close, and it does not tie the process lifetime to the Control Center window. The separate Action Manager `run()` method is reserved for short bounded commands.

## Device pairing

The Paired Devices tab can open a three-minute one-time pairing window, display the pairing code once, list pending requests, grant only a subset of requested permissions, and revoke individual devices. Device credentials are returned once and only their hashes are stored by the host. Pairing requests do not grant access until local approval.

This UI is host-side groundwork: until a TLS certificate is configured and the host service is started by the application, the Vita cannot complete the handshake.

## State and security

Actions and audit data are stored below the user's Vita Desktop Node state directory (XDG state path on Linux, Local AppData on Windows). The Control Center is a local GUI only. It does not expose approval or action execution through the network. Its Paired Devices tab manages host-side pairing records and approvals, but the VDN2 TLS listener is not automatically started and the PS Vita does not yet implement the VDN2 client.

The Vita-facing public catalog omits executable argv. A future VDN2 bridge must add pairing, per-device authorization, request validation and a distinct confirmation handshake before any remote launch can be enabled.

## Current limitations

- Linux XDG desktop-entry discovery only; Windows discovery is pending.
- No remote action transport or Vita VDN2 UI yet.
- TLS certificate provisioning and automatic listener lifecycle are pending.
- The GUI uses Tkinter and requires a graphical desktop session.
- The GUI has not been validated in a physical desktop session as part of this repository work.
