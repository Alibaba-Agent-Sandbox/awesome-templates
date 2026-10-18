# Explicitly authorized canonical Express CI

Date: 2026-10-16
Status: proposed

## Problem

Local Docker is unavailable. Supplementary Docker-artifact transfer and official
registration do not execute the canonical deploy command required for L2.
Credentials must not be copied into a new Actions secret store without explicit
approval of a concrete reviewed workflow.

## Decision

Prepare a separate, default-disabled stacked workflow. Require same-repository
source, an explicit opt-in secret and exact approved workflow head before cloud
execution. Begin with one reviewed template; permit an explicit 17-template
whitelist matrix only through the documented selection. Run serially, stop on
failure and forbid overlapping batches. No secrets are uploaded by this change.

## API Design

Invoke the actual cleanup-fixed canonical `scripts/express_e2e.py`, not a copied
builder or alternate registration path. Template/Docker source remains a361f49;
the independently pinned harness is 3572927, CLI 37b6d27, controller SDK 666657b,
and server wheel source e2cb27e. Existing flags bound READY/idle/deploy time and
disable automatic push retries. Public npm installs use the CLI lockfile.

Two temporary authorization secrets plus six prefixed cloud configuration
secrets are documented in English and Chinese. No model key or entire .env is
forwarded. Missing authorization/configuration is BLOCKED, never L2 PASS.
Only exit-zero canonical smoke, fresh validated receipt and successful exact
owned compute/registry cleanup permit provider-pass artifact upload. No evidence
is auto-committed and no catalog/provider status is promoted.

## Alternatives considered

- Upload keys before preparing code: rejected; approval must cover a concrete result.
- Treat supplemental image registration as canonical L2: rejected by existing rules.
- Use a361's old cleanup runner: rejected; it could falsely accept failed cleanup.
- Broad janitor/prefix deletion: rejected; cleanup is exact to the owned alias.

## Dependencies

[Cleanup PR 91](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/91),
[Issue 90](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/90),
[production CLI PR 37](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/37).
The operator must separately approve temporary Actions credential storage and
the final workflow SHA. Workflow dispatch is unavailable before default-branch
registration; an explicitly opted-in same-repository PR edited event is supported.

## Test Strategy

Use synthetic/no-network tests for authorization, exact SHA/fork rejection,
selection, missing credentials, stale receipt, failed compute/registry cleanup
and final publication. Validate YAML/source pins/relative docs and configured
secret exclusion. No cloud or credential upload is performed during preparation.
Actual canonical Docker/Express behavior remains unaccepted until authorized CI.

## Acceptance criteria

- Prepared files are independently reviewable; default path performs no cloud calls.
- All public source pins and real harness flags are recorded.
- Exact authorization, missing-key and cleanup/evidence gates are tested.
- Private journals/auth/raw logs never enter upload paths; only sanitized status
  and successful canonical receipts can be artifacts.
- English/Chinese instructions cover triggering, approval, cleanup, cancellation
  limits, artifact review and removal of temporary secrets after the batch.
- Keep this PR draft/unmerged; no secret upload or cloud dispatch without approval.
