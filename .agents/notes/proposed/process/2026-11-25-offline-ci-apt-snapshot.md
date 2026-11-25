# Decision: Preserve offline engine contracts with a dated Debian archive

Status: proposed

## Problem

The documentation PR's required database and document jobs fail during apt preparation, before checkout. Debian's current PostgreSQL index no longer offers the reviewed 17.11 packages; LibreOffice u9 dependencies conflict with newer u12 security candidates. The same exact versions remain enforced by the templates' Dockerfiles, native version checks and E2E assertions.

## Decision

Use the official Debian and Debian-security archives at `20261112T000000Z` for only these two CI jobs. The previously successful baseline run used these engine pins on that date. Keep Debian archive-keyring signature verification and every package pin, native assertion and required job. Disable only the historical archives' metadata-expiry check using their per-source `Check-Valid-Until: no` setting.

This is a CI preparation repair. It does not update template images, runtime versions, catalog identities or historical cloud acceptance. Snapshot availability must be established by the actual GitHub jobs before merge.

## API Design

No public API, CLI or template runtime contract changes. The two jobs replace their default Debian source definitions before their existing apt installation commands.

## Alternatives considered

- Updating PostgreSQL to 17.12 or LibreOffice to u12 only in CI would contradict the templates' exact-version assertions. A coordinated runtime/image upgrade needs separate acceptance.
- Skipping the jobs or relaxing installed-version assertions would remove existing coverage.
- Downloading old pool files directly would add a separate checksum/distribution mechanism and retain removal risk.
- Moving the entire CI matrix or every template to a historical distribution is broader than the demonstrated preparation failures.

## Dependencies

Official Debian snapshots, the image's Debian archive keyring and the unchanged Debian 13 CI container. The original baseline and failed PR jobs are linked in the verification record.

## Test Strategy

Parse the workflow, syntax-check the modified shell blocks, compare engine pins and test commands against the prior head, run document/link checks and inspect the scoped diff. Push the existing PR and require actual successful apt preparation and unchanged native test jobs; local network failures are not passes.

## Acceptance criteria

Both required offline jobs install the existing exact engines and pass their unchanged native/HTTP checks on the current PR head. All other required checks remain enabled. Snapshot metadata continues to require Debian signatures. No cloud resources are created for this CI repair.
