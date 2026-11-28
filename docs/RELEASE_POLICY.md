# Vita Desktop Node — Release Policy

## Release principles

- Ship coherent, user-visible milestones rather than isolated placeholder commits.
- Preserve VMON1 compatibility until a replacement client is implemented and tested.
- Never mark a capability complete because its design document exists.
- Keep the README, roadmap, installation guides, capability report and release notes consistent.
- Do not merge or publish a release candidate until its stated checks have run.

## Versioning

- The current development line is `0.1.0-alpha.1`.
- R1 is the first host-foundation milestone, not a claim that every planned product feature is complete.
- Use semantic versioning for the Vita Desktop Node product line.
- Increment patch for compatible fixes, minor for new backward-compatible features and major only for incompatible changes.
- Do not tag a stable release while required CI or artifact checks are failing or unverified.

## Release gates

1. Host unit tests pass on the supported CI runner.
2. Debian package builds and installs in a clean Debian-based environment.
3. Vita VPK builds with VitaSDK and passes the repository verifier.
4. Windows artifact builds if included in the release.
5. Release artifacts are manually inspected and checksums are recorded where practical.
6. Physical Vita tests and clean Linux install tests are completed or explicitly listed as unverified.
7. README, release scope, roadmap and release notes match the actual shipped behavior.

## Release notes

Every release note states: new user-visible features; changes and fixes; compatibility impact; platforms/devices actually tested; known limitations; installation/migration/rollback notes; artifact names and verification status.

## Artifact policy

- Publish the PS Vita VPK with the release when the Vita build succeeds.
- Include the Linux Debian package when its build and install checks pass.
- Include Windows executable/ZIP only when those artifacts build and are tested.
- Never substitute an upstream VitaMon download link for a Vita Desktop Node artifact.
- A CI artifact is not automatically a hardware-certified release.
