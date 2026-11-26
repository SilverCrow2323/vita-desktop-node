# Vita Desktop Node — Vita Client Preview

## Package identity

- Application name: Vita Desktop Node
- Title ID: VDN000001
- PARAM.SFO application version: 00.10
- Client protocol: VMON1 telemetry compatibility
- Release track: 0.1.0-alpha.1

This package is the first branded Vita client preview for the Vita Desktop Node
project. It is not yet the full Direct Node client.

## Included in this preview

- Existing VitaMon-derived telemetry dashboard, rebranded as Vita Desktop Node.
- CPU/GPU/RAM/network/disk telemetry supplied by the existing desktop host.
- Six UI languages: Spanish, English, Portuguese, French, German and Italian.
- Touch and button navigation, compact view, debug overlay and connection status.
- Battery reporting and low-activity power-saving behavior.
- Stable application identity and dedicated Vita data directory.
- Migration of the saved language preference from ux0:data/VitaMon/lang.txt to
  ux0:data/VDN/lang.txt on first run.

## Not included yet

- VDN2 transport on the Vita.
- Pairing, device identity authentication or catalog synchronization.
- Direct Node file manager, transfer queue or folder synchronization.
- PC Actions / application launcher.
- Remote View, Remote Desktop, screen mirroring or Extended Display.
- Secure terminal, mesh networking or multi-node management.

The host and Vita client currently communicate through the legacy VMON1 telemetry
protocol. Do not expose this preview as the completed Vita Desktop Node ecosystem.

## Build

The VPK is built using VitaSDK and CMake:

```sh
cd vita
cmake -S . -B build
cmake --build build --parallel
python3 tools/verify_vpk.py build/VitaDesktopNode.vpk
```

The CI build runs the same commands in the official VitaSDK container and validates
the VPK archive, required files, Title ID, display name and application version.

## Install

1. Transfer VitaDesktopNode.vpk to the PS Vita.
2. Open VitaShell and install the VPK.
3. Launch Vita Desktop Node from LiveArea.
4. Start the compatible desktop host and configure the Vita IP / UDP connection.

The Vita application uses Title ID VDN000001 and stores its language setting under
ux0:data/VDN. The legacy VitaMon language preference is read once as a migration
fallback; the new preference is written to the VDN directory.

## Release gate

A CI artifact is not a hardware-certified release. Before publishing a stable
release, test installation, first launch, Wi-Fi reception, all six languages,
touch/button navigation, sleep/wake, and clean exit on physical PS Vita hardware.
