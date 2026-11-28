# Host Action Manager

The Host Action Manager turns the desktop application catalog into a persistent, approval-gated set of local actions.

## Implemented security model

- The public catalog contains opaque IDs and display metadata only.
- Executable argument vectors remain in a private host-side state file and are never returned by the public catalog.
- Scanned desktop entries and custom actions start disabled and unapproved.
- A person operating the host must explicitly approve an action before enabling it.- A local-only details method lets the PC Control Center display the exact executable and argv before approval; this method must never be exposed in a remote catalog or API.
- Actions requiring confirmation (the default) cannot run without explicit confirmation.
- Launching uses an argument vector with shell disabled. Shell interpreters and privilege-escalation frontends are rejected.
- The manager has no network listener. Pairing, per-device permissions and VDN2 request authentication must be enforced by a future transport before calling it.
- POSIX state and audit files use owner-only permissions. State and audit writes use atomic replacement.
- When a discovered application's argv changes, its previous approval is invalidated.

## Two execution modes

### Launch desktop applications

`launch(action_id, confirmed=True)` starts an approved desktop application as a detached process and returns immediately with its PID. Standard input/output/error are detached from the Control Center, so a long-running GUI such as a browser does not block the interface or get incorrectly reported as a timeout merely because the user keeps it open.

### Run bounded commands

`run(action_id, confirmed=True, timeout=30)` is for short commands that are expected to finish. It returns the exit code and bounded display snippets, or a timeout result. Use `launch()` for ordinary GUI applications.

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
result = manager.launch("custom.firefox", confirmed=True)
print(result["pid"])
```

The PC Control Center provides the intended local UI for these operations.

## Deliberate limitations

This milestone implements the host-side policy and execution primitive. It does not provide a network listener, remote Vita execution, pairing, per-device permissions or remote confirmation. Never expose `approve()`, `launch()` or `run(..., confirmed=True)` directly to an unauthenticated network request.
