# Vita Desktop Node — Vita Client Preview

## Package identity

- Application name: Vita Desktop Node
- Title ID: `VDN000001`
- PARAM.SFO application version: `00.10`
- Client protocol: VMON1 telemetry compatibility
- Host development version: `0.1.0-alpha.1`

This is the first branded Vita client preview for the Vita Desktop Node project. It is not yet the full Direct Node client.

## Included

- Existing VitaMon-derived telemetry dashboard, rebranded as Vita Desktop Node.
- CPU/GPU/RAM/network/disk telemetry supplied by the compatible desktop host.
- Six UI languages: English, Spanish, Portuguese, French, German and Italian.
- Touch and button navigation, compact view, debug overlay and connection status.
- Battery reporting and low-activity power-saving behavior.
- Stable application identity and dedicated Vita data directory.
- Migration fallback for the saved language preference from `ux0:data/VitaMon/lang.txt` to `ux0:data/VDN/lang.txt`.

## Not included

- VDN2 transport on Vita.
- Pairing, device authentication or catalog synchronization.
- Direct Node file manager, transfer queue or folder synchronization.
- PC Actions / remote application launcher.
- Remote View, Remote Desktop, screen mirroring or Extended Display.
- Secure terminal, mesh networking or multi-node management.

The host and Vita client currently communicate through the legacy VMON1 telemetry protocol. VMON1 is not an authenticated control channel and must not be used for remote commands or file transfer.

## Build

With VitaSDK and CMake installed:

```sh
cd vita
cmake -S . -B build
cmake --build build --parallel
python3 tools/verify_vpk.py build/VitaDesktopNode.vpk
```

The CI build uses the VitaSDK container and validates the VPK archive, required files, Title ID, display name and application version.

## Install

1. Transfer `VitaDesktopNode.vpk` to the PS Vita.
2. Open VitaShell and install the VPK.
3. Launch Vita Desktop Node from LiveArea.
4. Start the compatible desktop host on the same network.

The Vita application uses Title ID VDN000001 and stores its language setting under `ux0:data/VDN`. The legacy VitaMon language preference is read as a migration fallback; the new preference is written to the VDN directory.

## Hardware validation gate

A CI artifact is not a hardware-certified release. Before publishing a stable release, test installation, first launch, Wi-Fi reception, all six languages, touch/button navigation, sleep/wake, reconnect and clean exit on physical PS Vita hardware.
