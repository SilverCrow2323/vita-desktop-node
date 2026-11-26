# VDN2 Pairing and Host Service

**Status:** host-side pairing store and TLS-only service foundation implemented. Vita client handshake/UI and end-to-end hardware validation remain pending.

## Pairing lifecycle

1. The user opens a short pairing window locally in the host application.
2. The host displays a high-entropy, one-time code (30–600 second window).
3. The Vita sends `pairing.request` over the TLS control channel with its UUID, display name and requested permissions.
4. The code is consumed by the first valid request. Five invalid attempts close the window.
5. The request remains pending; it does not create an authenticated device.
6. The user reviews and approves the request locally. The host may grant only a subset of requested permissions.
7. The host returns a random device credential once. Only its SHA-256 digest is persisted.
8. Each later request authenticates the device, checks credential expiry, revocation and method permission.

The pairing code and device credential are never written to the pairing store. The pairing store is atomically replaced and restricted to owner-only permissions on POSIX systems.

## Permission model

Default deny. The first network service exposes only:
- `node.info`
- `node.capabilities`

Both require `node.info`. Pairing requests are unauthenticated at the application layer but require the short-lived one-time code and a TLS connection. Pairing approval is a local host operation, not a remote API.

The permission vocabulary is defined in `server/vdn/security/pairing.py`. A device can receive only permissions it requested; the host may grant fewer. Credentials expire (90 days by default) and can be individually revoked.

## TLS transport boundary

`HostService.start()` accepts only a configured `ssl.PROTOCOL_TLS_SERVER` context and enforces TLS 1.2 minimum. The caller must provision and load a server certificate and private key before starting the listener. Never expose a plaintext fallback.

The Vita client must validate/pin the host certificate or public-key fingerprint before sending pairing codes or credentials. A server-side TLS listener alone does not implement client-side pinning; this remains a Vita integration requirement.

## Deliberate limitations

- No remote action execution, terminal, file, display or process-control methods are registered.
- No unauthenticated capability or host inventory endpoint exists.
- Pairing approval UI is not yet integrated into the PC Control Center.
- No Vita-side VDN2 transport, TLS stack integration or pairing UI is implemented.
- Rate limiting is per pairing window (five invalid attempts); connection-level throttling and abuse monitoring remain future hardening.
- There is no session-token exchange yet; the per-device credential is presented over TLS for each request.
- Host certificate generation, rotation UI and Vita pin storage are not included in this milestone.

## Tests

Run:

```sh
PYTHONPATH=server python -m unittest discover -s server/tests/vdn -v
```

Tests cover one-time code consumption, invalid-code lockout, pending approval, permission subset enforcement, secret hashing, restart persistence, credential revocation, authenticated read-only methods and denial of remote action invocation.
