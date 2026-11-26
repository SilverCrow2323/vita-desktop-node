# Host Action Manager

The Host Action Manager turns the desktop application catalog into a persistent,
approval-gated set of local actions.

## Security model

- The Vita-facing catalog contains opaque IDs and display metadata only.
- Executable argument vectors remain in a private host-side state file and are
  never returned by the public catalog API.
- Scanned desktop entries and custom actions start disabled and unapproved.
- A person operating the host must explicitly approve an action before enabling it.
- Actions requiring confirmation (the default) cannot run without an explicit
  confirmation supplied by the caller after presenting the action to the user.
- Launching uses an argument vector with shell disabled. Shell interpreters and
  privilege-escalation frontends are rejected.
- The manager has no network listener. Pairing, per-node permissions and VDN2
  request authentication must be enforced by the transport before calling it.
- POSIX state and audit files use owner-only permissions. The audit log is bounded.

## Python API

    from pathlib import Path
    from server.vdn.action_manager import ActionManager

    manager = ActionManager(Path.home() / ".local/share/VitaDesktopNode")
    manager.add_custom_action(action_id="custom.firefox", name="Firefox", argv=["firefox"])
    manager.approve("custom.firefox")
    result = manager.run("custom.firefox", confirmed=True)

Import a scanned Linux Application with register_application(app). It remains
disabled until host approval.

## Deliberate limitations

This milestone implements the host-side policy and execution primitive. It does
not yet provide a graphical editor, Windows discovery, VDN2 transport, Vita UI,
or remote confirmation. Never expose approve() or run(..., confirmed=True)
directly to an unauthenticated network request.
