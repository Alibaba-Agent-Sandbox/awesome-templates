# Decision: Own the OpenClaw gateway lifecycle

Status: proposed

## Problem

The legacy template runs `openclaw <action>` synchronously (default `start`),
which does not launch the documented gateway foreground command. Its E2E accepted
HTTP500 as success, so it did not establish gateway behavior. Installs floated,
the image used a non-platform base, and the template lacked the v2 contract.

## Decision

Pin OpenClaw 2026.10.4 with Node 24.16.0, use Alibaba base/non-root/generation2,
and register dedicated start/status/authenticated-health/stop commands. Retain
`gateway` as an explicit bounded action alias. Own the Popen object in memory;
never trust a PID file or reclaim ports using --force. Use a private temporary
config/state and token environment reference. Preserve explicit blocked image,
cloud and model acceptance.

## API Design

See [full bilingual command contract](../../../../openclaw/README.md#command-reference)
and [design](../../../../docs/design/openclaw.md). Start returns only after a real
WebSocket health RPC reports ok:true. Status never implies health. Stop targets
only the currently owned process group and reaps it within a bounded interval.
An invalid action is a failing HTTP500/ValueError, and typed invalid parameters
are HTTP400; tests assert the precise error instead of accepting generic500.

## Alternatives considered

- `openclaw gateway start` installs/manages platform services; it is inappropriate
  for a sandbox without systemd ownership.
- Blocking foreground gateway subprocess does not return a usable API response.
- Persisted PID control can kill unrelated processes after PID reuse.
- Unauthenticated HTTP/TCP/PID probes do not prove authenticated gateway health.

## Dependencies

Upstream [gateway CLI](https://docs.openclaw.ai/cli/gateway) and npm package engines,
checked against installed2026.10.4. Server archive fallback pin remains the
repository-approved python-sdk35da216a300f1e2e84254a1cf4b4a7ea98681505.
Work reuses [Issue20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20).
The parent task owns the catalog update and cross-review/publishing workflow.

## Test Strategy

Regression tests cover missing token, typed/range/action rejection, owned stop,
idempotence, stale PID non-interference, false PID health and timeout cleanup.
Real installed CLI and HTTP runs cover authenticated readiness, persistent
background status, authenticated health and cleanup. A separate real CLI run
checks lan bind, wrong-token rejection and repeated start.

## Acceptance criteria

- Dedicated lifecycle commands and compatibility alias are implemented.
- Both READMEs document CLI, SDK, HTTP, full parameters/defaults/errors and limits.
- Template checker and behavior regressions pass.
- Real local gateway checks pass; no model call is inferred.
- Image build, Express acceptance and required review remain outstanding until
  actually executed; no merge or official-provider claim follows local passes.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-openclaw-owned-gateway.md).

Health-RPC cleanup follow-up: use the same Linux WNOWAIT/output-drain ownership runner for the short-lived probe only. Final group cleanup precedes leader reap on successful/nonzero completion and timeout, while the separately owned main gateway lifecycle remains unchanged. [Verification](../../../evidence/verify/2026-10-16-openclaw-health-process-cleanup.md).
