# VDN2 — Protocol and Security Baseline

**Status:** design baseline. VDN2 is not yet implemented by the Vita client.

## Compatibility boundary
- Keep the existing VMON1 UDP telemetry datagram and VMONACK1 reply unchanged.
- VMON1 is telemetry-only. Never send terminal input, file contents, credentials or privileged commands through it.
- VDN2 is a separate, versioned interactive service. Older VitaMon clients continue to work without VDN2.

## Logical channels
| Channel | Purpose | Initial transport |
|---|---|---|
| Discovery | Find nodes on the LAN | UDP hints; no secrets |
| Session/control | Pairing, capabilities, requests, acknowledgements | TCP with TLS |
| Terminal | Interactive PTY streams | Authenticated TLS session |
| Files | Listing, metadata, chunked transfer | Authenticated TLS session |
| Display | Remote View media and input | Separately negotiated media transport |
| Telemetry | Existing metrics | Existing VMON1 UDP |

Control and data planes are distinct. A future media transport must not weaken control-channel authentication.

## Message framing
VDN2 control messages use UTF-8 JSON. Each frame is a 4-byte unsigned big-endian payload length followed by exactly that many bytes. Initial control-frame limit: 1 MiB.

Example request:
```json
{
  "protocol": "VDN2",
  "version": 2,
  "type": "request",
  "id": "request-unique-id",
  "session": "session-id",
  "method": "node.capabilities",
  "params": {}
}
```

Requirements: reject unsupported protocol identifiers and major versions; validate shapes, types and method parameters; enforce frame limits and timeouts; return structured errors without stack traces, secrets or filesystem details.

## Pairing and identity
1. User explicitly enables pairing on the host.
2. Host displays a short-lived, single-use pairing code and device identity/fingerprint.
3. Client submits the code over an authenticated bootstrap channel.
4. User confirms the requesting device and its displayed identity.
5. Host issues a per-device credential; credentials are independently revocable.
6. Reconnects use the stored credential and pinned host identity.

Pairing codes are not reusable session passwords. Use a reviewed TLS implementation and certificate/public-key pinning suitable for the Vita runtime. Do not invent cryptography. Never log pairing secrets or send them over plaintext discovery.

## Authorization
Default deny. Permissions are granted per paired device:
- telemetry.read, node.info, process.read
- notification.send, clipboard.read, clipboard.write
- files.list, files.read, files.write, files.delete
- terminal.open, terminal.execute
- desktop.view, desktop.control, display.session

File deletion, overwrites, system changes and privilege elevation require fresh confirmation. A terminal session must not silently inherit administrator/root privileges.

## Secure terminal
- Allocate a PTY through a dedicated service; do not pass shell command strings to subprocess.
- Start as the paired user's normal account, with a configurable working directory.
- Never concatenate untrusted input into shell commands; no implicit sudo, root shell, password capture or privilege escalation.
- Bound session count, idle time, output buffer and input size.
- Support explicit close, disconnect cleanup and audit events. Do not log terminal contents or secrets by default.
- Clearly identify the connected device and active terminal session in the host UI.

## File transfer
- Resolve paths beneath an explicitly shared root; reject traversal and symlink escapes.
- Use chunked transfer, size limits, checksums and resumable transfer IDs.
- Confirm overwrites and deletions.
- Default to authenticated TLS. FTP is compatibility-only on trusted LANs and must never be described as secure.

## Display
- Remote View captures and encodes an existing desktop/session.
- Extended Display creates or attaches to a distinct virtual display output; it is not mirroring.
- Negotiate codec, resolution, frame rate, bitrate and input capabilities.
- If the host cannot create an additional display, report that limitation rather than silently falling back to mirroring.
- Keep media transport isolated from pairing, authorization and control messages.

## Versioning and tests
- Change the major version only for incompatible envelope or semantic changes.
- Discover capabilities at runtime; do not assume every host supports every module.
- Ignore unknown optional fields; fail closed on unknown required capabilities.
- Test malformed/oversized frames, replayed pairing codes, revoked devices, unauthorized methods, path traversal and interrupted transfers.

## Implementation order
1. Framing, schema validation and capability handshake.
2. Host identity, pairing, credential storage and revocation.
3. Permission checks and audit events.
4. Read-only node information and process inventory.
5. Secure PTY service.
6. Sandboxed file service, then LAN/Tailscale routing.
7. Display capture and virtual-display providers.