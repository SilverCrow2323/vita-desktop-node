# Vita Desktop Node — Release Policy

## One milestone, one user-visible improvement

Each milestone release must add at least one concrete feature compared with the immediately previous release. A release may include several fixes or supporting refactors, but no feature is marked complete without an end-to-end test and user documentation.

## Versioning

- Preserve upstream VitaMon version history and compatibility while the fork is in transition.
- Use semantic versioning for the Vita Desktop Node product once the fork has its own release line.
- Increment the patch number for compatible fixes; minor for new backward-compatible features; major only for incompatible changes.
- Tag and publish only after CI passes for all supported artifacts included in that release.

## Milestone notes

Every release note states:
1. new user-visible feature;
2. changes and fixes;
3. compatibility impact;
4. tested operating systems/devices;
5. known limitations;
6. migration or rollback notes, if needed.

A planned feature is never described as shipped.
