# Decision: Authenticated development databases
Status: proposed

## Problem

Issue56 needs actual databases without privileged Docker/mount/systemd.

## Decision

Pinned PostgreSQL17.11/Redis8.0.2, non-root initdb, mandatory credentials, loopback defaults, explicit expose opt-in, marked persistent workspace data and identity-safe owned process cleanup. Preserve caller data and require actual persisted readback.

## API Design

Eight documented named commands, fixed ports5432/6379 and command API9000. Query clients have bounded output/deadlines and literal argv. PostgreSQL SCRAM, Redis requirepass, private configs, no inherited cloud/model keys.

## Alternatives considered

Docker Compose/mounts unavailable; systemd/root process managers unnecessary. Trust authentication/unauthenticated Redis and fake SQL stores would not meet requirements. Plain exit0 is insufficient: redis-cli -e is required for protocol errors.

## Dependencies

Official Debian13 fixed packages and upstream initdb/Redis docs; native CLI/SDK and canonical source spec. Linux pidfds/procfs. Actual extracted official package binaries used locally without modifying host system packages.

## Test Strategy

Real engines/authentication/SQL/Redis/persistence/cleanup, negative controls and unrelated listener preservation; HTTP L0, image L1 and genuine cloud L2. No provider pass inferred from local tests.

## Acceptance criteria

Complete standalone source/bilingual docs, correct fixed licenses and versions, actual runtime/cloud receipts, independent owned cleanup, current-head CI and normal merge. External TCP forwarding remains explicitly unverified until exercised.
