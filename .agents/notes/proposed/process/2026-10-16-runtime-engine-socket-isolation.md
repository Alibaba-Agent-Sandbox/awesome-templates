# Decision: Isolate the source-runtime engine socket per invocation

Status: proposed

## Problem

The source-runtime diagnostic derived its local SDK engine socket only from the
process ID. Native exec processes in this environment can expose identical PIDs
while sharing the filesystem. A later diagnostic can attach to the first process's
engine; when that process exits, the later process recreates an empty engine and
receives E2009 for its still-running remote sandbox.

This mechanism was reproduced with real local gRPC engines and synthetic sessions.
The earlier Droid run was not instrumented for engine ownership, so its exact
shutdown sequence remains unconfirmed; its E2009 does not establish remote TTL expiry.

## Decision

Append `secrets.token_hex(6)` to the existing PID-based socket basename in
`scripts/express_runtime_e2e.py`. Each invocation retains a short local Unix socket
and the existing in-process engine/owned cloud cleanup behavior, without borrowing
another diagnostic's engine. No SDK lifecycle behavior or permission settings change.

## API Design

N/A — this decision does not involve API changes.

The diagnostic's process environment selects a fresh socket per run; it is not a
user-supplied provider endpoint or a persisted cross-process engine address.

## Alternatives considered

- Increase remote TTL: rejected because the missing local engine session is
  independent of provider expiration.
- Automatically reconnect/adopt inside the SDK: rejected because the isolated
  reproducer identifies a diagnostic address collision, not an SDK expiry bug.
- Use PID alone: rejected because PID namespaces do not guarantee filesystem-wide
  uniqueness across concurrent native execs.

## Dependencies

Existing Python standard-library `secrets` import; no dependency addition.

## Test Strategy

Run three credential-free startup regressions against the actual socket assignment,
including independent processes with equal PID views and the gRPC path-length
limit. Record the old-expression failures before changing the line. Use two native
execs with actual local gRPC engines for negative and positive controls: shared
socket ownership disappears when the owner exits; isolated sockets preserve the
other process's session. No cloud/image/model acceptance is inferred.

## Acceptance criteria

- Equal PID views cannot select the same diagnostic engine socket except for an
  unpredictable nonce collision.
- The name stays local and within the SDK's Unix socket path limit.
- Old naming fails the regression and new naming passes; native engine controls
  demonstrate the actual session-loss mechanism and its isolation.
- Existing runtime choices, reports, provider endpoints and owned cloud cleanup
  remain unchanged.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-runtime-engine-socket-isolation.md).
[Harness issue 84](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/84). Related observation: [SDK issue 35](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/35).
