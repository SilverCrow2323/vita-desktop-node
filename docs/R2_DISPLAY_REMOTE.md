# R2 Display and Remote Control Scope

R2 brings three distinct display experiences. They share a session manager and
input channel, but they are not interchangeable features.

## Remote View / Mirroring

Capture the existing PC desktop and stream it to the Vita. The initial mode is
view-only. A later control toggle may enable remote input when the paired device
has the required permission.

## Remote Desktop

Stream the PC desktop and accept Vita-originated pointer, button, and keyboard
events. Input is disabled by default until the user grants the paired Vita
desktop.input permission. A visible host indicator and an immediate disconnect
control are required.

## Extended Display

Create or attach a virtual display on the host and stream that display to the
Vita. This is not mirroring: the Vita must represent a separate desktop surface.
The provider is platform-specific:

- Windows: evaluate a supported virtual-display driver/provider.
- Linux X11: evaluate XRandR virtual outputs and available virtual-display drivers.
- Linux Wayland: compositor-specific protocols and support; no universal promise.

## Shared technical requirements

- Negotiate codec, dimensions, frame rate, bitrate, and input capabilities.
- Prefer hardware encoding/decoding where supported; provide a tested fallback.
- Use an authenticated VDN2 session; do not send video over VMON1 telemetry.
- Separate video transport from control/input messages.
- Handle reconnect, pause, resize, monitor selection, and clean shutdown.
- Expose measured latency and dropped-frame counters during development.
- Make the host visibly indicate an active remote-control session.

## Performance gates

No fixed frame-rate or latency promise is made before testing on real PS Vita
hardware and the target host platforms. R2 is complete only when each mode has
an implementation, integration tests where possible, and documented hardware
results. If a platform cannot provide a reliable virtual display, Extended Display
must be marked unsupported there rather than silently falling back to mirroring.

## Security

Pairing, revocation, per-device permissions, explicit session approval, and
immediate disconnect are prerequisites for remote input. Remote View can be
granted independently from desktop input. Extended-display sessions must not
implicitly grant control of the primary desktop.
