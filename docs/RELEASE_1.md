# Vita Desktop Node — Release 1

**Release track:** R1 host foundation  
**Current repository version:** 0.1.0-alpha.1  
**Release state:** implementation milestone; publication remains gated on CI and target-device validation.

## Purpose

Release 1 establishes the first Vita Desktop Node host foundation. It preserves the working legacy Vita telemetry path and adds the first reusable host-side building blocks for future VDN2 services and local PC interaction.

This is not the full Vita-to-PC ecosystem release. In particular, VDN2 pairing and transport are not yet available to the Vita client.

## Included scope

### Host core

- Stable per-installation node UUID stored in the user's state directory.
- Capability inventory that reports only implemented capabilities.
- Cross-platform config/state/cache/log path discovery.
- Atomic JSON configuration writes and owner-only POSIX permissions.
- CLI smoke-test entry points for node information and config path.

### VDN2 protocol foundation

- Four-byte unsigned big-endian frame length.
- UTF-8 JSON envelope validation.
- Request, response and event message types.
- Protocol/version checks, message ID validation and bounded frame size.
- Async stream read/write helpers and tests for malformed, truncated and oversized frames.

Framing is not a secure channel. It does not provide TLS, peer identity, pairing, replay protection or authorization.

### Host extensibility

- Add-on manifest/context contracts and API version.
- Built-in factory registry and duplicate-ID/manifest validation.
- Enable/disable lifecycle management.
- Explicit permission checks and rollback when startup fails.
- No arbitrary third-party add-on code loading.

### Linux desktop and local actions

- Initial Linux XDG integration and Debian package build script.
- Linux desktop-entry metadata scanner.
- Persistent host-side action records and bounded audit log.
- Actions start disabled and unapproved.
- Local approval and explicit run confirmation.
- argv-based process launch with `shell=False`.
- Rejection of shell interpreters and privilege-escalation frontends.
- Public catalog omits executable argv.
- Tkinter PC Control Center for scanning/importing applications, adding custom actions, approving/enabling/disabling/revoking actions, confirming local execution and inspecting activity.

Windows application discovery is not part of this milestone. The Control Center has not been validated in a Windows desktop session.

### Vita client compatibility

- Vita application identity changed to Vita Desktop Node.
- Title ID: `VDN000001`.
- VPK output name: `VitaDesktopNode.vpk`.
- Dedicated preference directory: `ux0:data/VDN`, with migration fallback for the legacy language preference.
- Existing VMON1 telemetry behavior is retained.

The Vita client does not yet implement VDN2.

## Explicitly out of scope

- VDN2 TCP/TLS listener, pairing handshake, credential issuance or revocation.
- Vita application catalog browser or remote PC action requests.
- Vita-side approval/confirmation flow.
- PSVita Direct Node file transfer, watcher, queue or two-way sync.
- Secure PTY terminal.
- Remote View, interactive Remote Desktop or Extended Display.
- Tailscale/WireGuard integration and multi-node discovery.
- Windows application catalog provider.
- AppImage packaging.

These are subsequent roadmap items, not hidden or partially enabled Release 1 features.

## Build and verification

Run the host tests:

```sh
PYTHONPATH=server python -m unittest discover -s server/tests/vdn -v
```

Inspect the host capability report:

```sh
PYTHONPATH=server python -m vdn.app --print-info
```

Build the Debian package:

```sh
./packaging/linux/build-deb.sh
```

Build and verify the Vita package with VitaSDK:

```sh
cd vita
cmake -S . -B build
cmake --build build --parallel
python3 tools/verify_vpk.py build/VitaDesktopNode.vpk
```

The repository CI workflow is expected to validate host tests, Debian packaging, Vita VPK build/verification and Windows packaging. A release must not be published until the relevant workflow run is green and its artifacts have been inspected.

## Hardware and platform validation checklist

- [ ] Install the Debian package on a clean MX Linux/XFCE system.
- [ ] Launch the host GUI and verify single-instance behavior.
- [ ] Verify login autostart enable/disable.
- [ ] Verify telemetry reception from a physical PS Vita over LAN.
- [ ] Verify all six Vita UI languages and settings migration.
- [ ] Verify sleep/wake, reconnect and clean exit on physical Vita hardware.
- [ ] Open PC Control Center in a graphical session.
- [ ] Scan a Linux desktop catalog and verify hidden entries are excluded.
- [ ] Add a harmless custom application action, approve it and launch it with confirmation.
- [ ] Verify shell/privilege-escalation rejection and audit records.
- [ ] Verify package uninstall leaves user data intact.
- [ ] Inspect VPK metadata and confirm Title ID/version/name.

## Release decision

Release 1 is ready to publish only when:

1. The host test suite passes in CI.
2. The Debian and Vita artifacts build and pass their verification steps.
3. The release artifacts are attached to a draft/release candidate and manually inspected.
4. Hardware and clean-install checks are either completed or explicitly listed as unverified limitations.
5. README, roadmap, installation guide, protocol guide and release notes agree on the same feature boundary.

A successful build alone does not certify physical Vita compatibility. Do not mark the release stable if required hardware checks remain unverified.
