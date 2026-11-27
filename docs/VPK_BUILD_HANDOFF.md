# Vita Desktop Node — VPK build handoff

**Target build:** `0.1.0-alpha.2`
**VPK filename:** `VitaDesktopNode-0.1.0-alpha.2.vpk`
**Title:** `Vita Desktop Node`
**Title ID:** `VDN000001`
**PARAM.SFO APP_VER:** `00.10`

## What this package contains

This build preserves the existing PS Vita VMON1 telemetry client, with the Vita Desktop Node application identity and the dedicated `ux0:data/VDN/lang.txt` preference path. It is not the VDN2 client: pairing, TLS, PC actions, file management/synchronization, terminal and remote display are not included in the Vita binary yet.

## Build artifact

The GitHub Actions workflow has a manually runnable `Build and Package` workflow. Select branch `feature/vdn2-foundation` and run it. The VPK job compiles with VitaSDK, verifies the archive, PARAM.SFO identity, PNG signatures and LiveArea XML, then uploads an artifact named:

`VitaDesktopNode-VPK-alpha.2`

The artifact contains:
- `VitaDesktopNode-0.1.0-alpha.2.vpk`
- `VitaDesktopNode-0.1.0-alpha.2.vpk.sha256`
- `VitaDesktopNode-0.1.0-alpha.2-build.txt`

## Verify after download

On Linux, extract the artifact ZIP and run:

```sh
sha256sum -c VitaDesktopNode-0.1.0-alpha.2.vpk.sha256
```

The build report records the VPK verifier result. A successful archive check is not a substitute for installing and testing on physical PS Vita hardware.

## Verified CI evidence — 27 November 2026

Workflow run [#45973429954](https://github.com/SilverCrow2323/vita-desktop-node/actions/runs/45973429954) completed successfully on `feature/vdn2-foundation`.

- **VPK:** VitaSDK build, archive/identity verification, checksum and build-report handoff, and artifact upload all passed.
- **Host tests:** Python unit tests, C protocol/translation tests, server-line parser, GPU fixture readers and RivaTuner/FPS/update/Vita-reply checks all passed.
- **Windows:** executable and ZIP packaging completed and artifacts uploaded.
- **Debian:** package build completed and artifact uploaded.
- **Release job:** skipped because this was not a release-tag run; no GitHub Release was published.

This is reproducible CI/build evidence for the branch. It does not establish a clean install or functional validation on a physical PS Vita.

## Current release boundary

This is a development VPK artifact, not a published GitHub Release and not a hardware-certified build. Do not mark the release stable until CI, artifact inspection, clean install and physical Vita checks are complete.
