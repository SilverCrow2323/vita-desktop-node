# Linux Host — Initial VitaMon Port

The first Linux target is MX Linux/XFCE. The existing VitaMon GUI and VMON1 sender are being ported before new Vita Desktop Node services are added.

## Current Linux integration

- XDG configuration: `$XDG_CONFIG_HOME/VitaMon/config.json` (defaults to `~/.config/VitaMon/config.json`).
- Login startup: per-user XDG autostart entry at `$XDG_CONFIG_HOME/autostart/vitamon.desktop`.
- Single-instance guard: per-user runtime lock (or cache fallback).
- Hardware monitoring: psutil and Linux sensor interfaces where exposed.
- Tray icon: optional pystray integration; the app remains usable without it.

## Build a Debian package

On a Debian/Ubuntu-based development machine with Python 3 and dpkg tools:

```sh
sudo apt install python3 python3-tk python3-psutil python3-pil python3-pystray dpkg-dev
./packaging/linux/build-deb.sh
```

The generated package is placed under `dist/`. Install it with:

```sh
sudo apt install ./dist/vitamon_*_all.deb
```

## Current limitations

This is the initial host GUI port, not the complete Vita Desktop Node host. Windows-only GPU/FPS sources such as DXGI, LibreHardwareMonitor web-server integration and RivaTuner remain Windows-specific. Linux GPU support is currently strongest when `nvidia-smi` is available; other vendors need dedicated providers. Wayland tray behavior depends on the desktop environment and tray host.

The package is a first installable baseline. AppImage, signed releases, polished icons and automatic dependency/desktop integration tests are later packaging work.
