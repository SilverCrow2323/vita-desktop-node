# Linux Host — Installation and Packaging

The first Linux validation target is MX Linux/XFCE. The host retains compatibility with the original VitaMon GUI while introducing Vita Desktop Node host foundations. The Debian package is an initial installable baseline, not a claim that every VDN service is available.

## Current integration

- XDG-aware configuration path discovery.
- Per-user XDG autostart entry.
- Per-user single-instance lock.
- Python host dependencies and Tkinter UI.
- Optional pystray integration; the app remains usable without a tray host.
- Debian package build script using `dpkg-deb`.
- Host-core node identity/configuration and local PC Control Center modules.

Some packaging paths and launcher labels still use the legacy `vitamon` name during the transition. The PS Vita application itself is branded Vita Desktop Node.

## Build a Debian package

On a Debian/Ubuntu-based development machine with Python 3 and dpkg tools:

```sh
sudo apt update
sudo apt install python3 python3-tk python3-psutil python3-pil python3-pystray dpkg-dev
bash packaging/linux/build-deb.sh
```

The generated package is placed under `dist/`. Install it with:

```sh
sudo apt install ./dist/vitamon_*_all.deb
```

Check the actual filename generated in `dist/`; do not assume the package version from the wildcard.

## Development smoke tests

From the repository root:

```sh
PYTHONPATH=server python -m vdn.app --print-info
PYTHONPATH=server python -m unittest discover -s server/tests/vdn -v
```

The node information report is a capability inventory, not a connection status screen. Pairing, terminal, file transfer, mesh and display capabilities must remain unavailable until implemented.

## Current limitations

- This is not yet a complete VDN2 host service; no authenticated VDN2 network listener or pairing is available.
- Windows-only GPU/FPS sources such as DXGI, LibreHardwareMonitor web-server integration and RivaTuner remain Windows-specific.
- Linux GPU support depends on available providers and hardware; missing sensor values are unavailable, not zero.
- Wayland tray behavior depends on the compositor and tray host.
- AppImage, signed packages and automated clean-install/uninstall validation remain future packaging work.
- A successful package build does not replace testing on a clean MX Linux/XFCE installation.
