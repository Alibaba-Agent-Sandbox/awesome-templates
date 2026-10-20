# Decision: configurable database ports preserve foreign listeners

Status: proposed

## Problem

[Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56) actual SDK-created Express tests found6379 occupied before any owned service start. Independent bind returned EADDRINUSE98; owner was not determined. Runtime1.0.0 correctly refused but could not select a usable Redis port.

## Decision

Version1.1.0 adds explicit ports and process-start defaults. The image uses PostgreSQL5432/Redis16379; bare source without configuration retains5432/6379. Never stop or reuse the unknown listener. New runtime requires new actual image/Express proof.

## API Design

services_start adds postgres_port:int=0/redis_port:int=0;0 reads DEV_SERVICES_POSTGRES_PORT/DEV_SERVICES_REDIS_PORT. Require distinct integers1024..65535 excluding9000. Start/status/clients use actual selected ports. Auth, bounded clients, persistent data and pidfd cleanup remain unchanged. Existing1.0.0 storage marker remains a storage-format contract.

## Alternatives considered

Killing the occupied port is unauthorized. Blind retries cannot repair a persistent foreign listener. Hardcoding a different Redis port without a selector would move the same problem to another environment. Reading only configured exact ports keeps behavior explicit.

## Dependencies

Same official pinned PostgreSQL17.11/Redis8.0.2 packages, source server and non-root Linux/procfs profile. Native fixtures extracted from the previously verified1.0.0 image preserve exact binaries; they do not qualify the new runtime image.

## Test Strategy

Actual pre-fix runtime ignores configured alternate port and fails while preserving a controlled6379 listener. New12 actual native regressions pass including persistence/auth, configured alternate port plus foreign listener preservation and invalid-port no-mutation guards. Complete required-engine HTTP6/0SKIP passes. Rebuild1.1.0 and run actual Express SDK creation/full HTTP/independent cleanup.

## Acceptance criteria

Bilingual exact defaults/API/compatibility and diagnosis, actual native/HTTP regressions, fresh image/Express receipts with exact hashes and independently verified cleanup. Latest-head CI/normal merge before Issue closure; raw external TCP forwarding remains unverified.
