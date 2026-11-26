# VDN2 — Protocol and Security Baseline

**Status:** host-side framing, pairing store, local approval controls and TLS-only read-only service class implemented. Vita TLS/pairing client and automatic listener/certificate integration remain pending.

## Compatibility boundary

- Keep the existing VMON1 UDP telemetry datagram and VMONACK1 reply unchanged.
- VMON1 is telemetry-only. Never send terminal input, file contents, credentials or privileged commands through it.
- VDN2 is a separate, versioned interactive service.
- Existing VitaMon/VDN telemetry clients continue to work without VDN2.

## Implemented framing

The host module `server/vdn/protocol/framing.py` implements UTF-8 JSON envelopes, a four-byte unsigned big-endian payload length, a default maximum payload of 1 MiB, request/response/event validation, protocol/version checks, message ID and object-shape validation, async stream read/write helpers, and rejection of malformed, oversized, truncated and trailing data.

Framing does **not** provide encryption, authentication, pairing, authorization, replay protection or a network listener. Do not expose host actions through this module alone.

## Logical channels (target architecture)

| Channel | Purpose | Intended transport |
|---|---|---|
| Discovery | Find nodes on the LAN | UDP hints; no secrets |
| Session/control | Pairing, capabilities, requests, acknowledgements | TCP with TLS |
| Terminal | Interactive PTY streams | Authenticated TLS session |
| Files | Listing, metadata, chunked transfer | Authenticated TLS session |
| Display | Remote View media and input | Separately negotiated media transport |
| Telemetry | Existing metrics | Existing VMON1 UDP |

Control and data planes are distinct. A future media transport must not weaken control-channel authentication.

## Pairing and identity — host-side foundation implemented

Implemented host-side flow:

1. User explicitly enables pairing on the host.
2. Host displays a short-lived, single-use pairing code. Host certificate fingerprint display and rotation UI remain pending.
3. Client submits the code over the TLS control channel using `pairing.request`.
4. The request remains pending; the one-time code is consumed and grants no access.
5. The host user reviews the device and grants a subset of its requested permissions in the PC Control Center.
6. Host issues a random per-device credential once; only its SHA-256 digest is persisted.
7. Authenticated requests validate credential, expiry, revocation and required permission.

Pairing codes are not reusable session passwords. Use a reviewed TLS implementation and certificate/public-key pinning suitable for the Vita runtime. Do not invent cryptography. Never log pairing secrets or send them over plaintext discovery.

## Authorization — host-side foundation

Default deny. Permissions are granted per paired device, for example: `telemetry.read`, `node.info`, `process.read`, `notification.send`, `files.list`, `files.read`, `files.write`, `files.delete`, `terminal.open`, `terminal.execute`, `desktop.view`, `desktop.control`, `display.session`, `actions.catalog.read`, `actions.propose`, `actions.invoke`.

File deletion, overwrites, system changes and privilege elevation require fresh confirmation. A terminal session must not silently inherit administrator/root privileges.

## Host action boundary currently implemented

The local Host Action Manager and PC Control Center provide host-side approval and execution controls. The manager stores executable argv locally, returns metadata-only public action records, requires approval and explicit confirmation, uses `shell=False`, blocks shell/privilege-escalation launchers and records bounded audit events.

The TLS service exposes only authenticated `node.info` and `node.capabilities` read-only methods. Pairing requests can create pending records but cannot approve themselves. No network endpoint invokes the Host Action Manager; remote actions remain blocked.

## TLS host service boundary

`server/vdn/services/host_service.py` provides a TLS-only asyncio listener (TLS 1.2 minimum, bounded frames, maximum eight concurrent clients). It requires a caller-supplied `ssl.PROTOCOL_TLS_SERVER` context with a configured certificate and private key. The listener is not automatically started by the desktop application yet. The Vita client must pin/validate the host certificate before sending a pairing code or credential.

## Secure terminal — planned

- Allocate a PTY through a dedicated service; do not pass shell command strings to subprocess.
- Start as the paired user's normal account, with a configurable working directory.
- Never concatenate untrusted input into shell commands; no implicit sudo, root shell, password capture or privilege escalation.
- Bound session count, idle time, output buffer and input size.
- Support explicit close, disconnect cleanup and audit events. Do not log terminal contents or secrets by default.

## File transfer — planned

- Resolve paths beneath an explicitly shared root; reject traversal and symlink escapes.
- Use chunked transfer, size limits, checksums and resumable transfer IDs.
- Confirm overwrites and deletions.
- Default to authenticated TLS. FTP is compatibility-only on trusted LANs and must never be described as secure.

## Display — planned

- Remote View captures and encodes an existing desktop/session.
- Remote Desktop adds interactive input, with a separate permission grant and visible host-side session status.
- Extended Display creates or attaches to a distinct virtual display output; it is not mirroring.
- If the host cannot create an additional display, report that limitation rather than silently falling back to mirroring.
- Keep media transport isolated from pairing, authorization and control messages.

## Versioning and security tests

- Change the major version only for incompatible envelope or semantic changes.
- Discover capabilities at runtime; do not assume every host supports every module.
- Ignore unknown optional fields; fail closed on unknown required capabilities.
- Before network exposure, test malformed/oversized frames, replayed pairing codes, revoked devices, unauthorized methods, path traversal and interrupted transfers.

## Implementation order

1. Framing and envelope validation. (Implemented.)
2. Host pairing store, local approval, credential hashing and revocation. (Host-side implemented.)
3. TLS-only read-only host service and per-request authorization. (Service class implemented; automatic startup/certificate lifecycle pending.)
4. Vita-side TLS pinning, pairing UI and credential storage.
4. Read-only node information and process inventory.
5. Secure PTY service.
6. Sandboxed file service, then LAN/mesh routing.
7. Display capture and virtual-display providers.
