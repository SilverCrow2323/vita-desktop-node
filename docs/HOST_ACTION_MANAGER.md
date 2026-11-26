# Host Action Manager

The Host Action Manager turns the desktop application catalog into a persistent, approval-gated set of local actions.

## Implemented security model

- The public catalog contains opaque IDs and display metadata only.
- Executable argument vectors remain in a private host-side state file and are never returned by the public catalog.
- Scanned desktop entries and custom actions start disabled and unapproved.
- A person operating the host must explicitly approve an action before enabling it.
- Actions requiring confirmation (the default) cannot run without explicit confirmation.
- Launching uses an argument vector with shell disabled. Shell interpreters and privilege-escalation frontends are rejected.
- The manager has no network listener. Pairing, per-device permissions and VDN2 request authentication must be enforced by a future transport before calling it.
- POSIX state and audit files use owner-only permissions. The audit log is bounded.
- When a catalog application's argv changes, its previous approval is invalidated.

## Local API

```python
from pathlib import Path
from vdn.action_manager import ActionManager

manager = ActionManager(Path.home() / ".local/share/vitadesktopnode")
manager.add_custom_action(
    action_id="custom.firefox",
    name="Firefox",
    argv=["firefox", "--new-window"],
)
manager.approve("custom.firefox")
result = manager.run("custom.firefox", confirmed=True)
```

The PC Control Center provides the intended local UI for these operations.

## Deliberate limitations

This milestone implements the host-side policy and execution primitive. It does not provide a network listener, remote Vita execution, pairing, per-device permissions or remote confirmation. Never expose `approve()` or `run(..., confirmed=True)` directly to an unauthenticated network request.
