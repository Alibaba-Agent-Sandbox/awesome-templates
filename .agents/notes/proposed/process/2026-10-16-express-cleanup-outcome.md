# Canonical Express evidence requires successful owned cleanup

Date: 2026-10-16
Status: proposed

## Problem

[Issue 90](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/90):
the canonical harness wrote provider-pass evidence before cleanup, and ignored
nonzero kill/delete exits. A failed cleanup could therefore return 0. Lost
deploy/create responses also left no persistent ownership context.

## Decision

Publish provider-pass evidence only after CLI/SDK smoke and owned sandbox/template
cleanup succeed. A cleanup error remains a failed attempt even if recovery later
succeeds. Record private owned intent before irreversible operations, refuse an
already registered alias, and reconcile only exact owned resources. Preserve
failed/ambiguous intents outside the checkout; do not publish them as evidence.

## API Design

Existing template/timeout/smoke arguments remain. Add
`express_e2e.py --recover-intent PRIVATE_PATH`, requiring a private regular file
owned by the invoking user. Use actual `abx --json template list --official-api`,
`abx template delete`, and SDK `Sandbox.list`/`kill_by_id`. No endpoint or platform
capability is invented. Default intents are in a random mode-0700 temporary
directory with mode-0600 JSON; secrets and raw logs are excluded. Successful
canonical acceptance removes its intent. Failure retains it for recovery.

An unknown response plus empty inventory stays unresolved. Recovery does not
grant acceptance to a failed attempt. Registry-image retention is separate from
the runner's sandbox/template cleanup contract. Linux process monitoring keeps
the owned leader unreaped until group cleanup on successful/nonzero exit too.

## Alternatives considered

- Fix only a new CI wrapper: rejected; leaves the canonical product falsely green.
- Ignore cleanup failures after smoke: rejected; publishes misleading evidence.
- Delete by generic resource prefix: rejected; cannot establish ownership.
- Treat empty inventory as cancellation: rejected; accepted work may appear later.

## Dependencies

Base: `a361f490555ead0ff67081ffb4874abf292a1b2f`. Official CLI JSON field/flag
contracts were inspected at reviewed CLI `37b6d276bdca875811ce7fb0ae88aca64882fcaa`.
SDK recovery uses existing documented APIs; native providers beyond Express are
outside this runner. No credential storage/upload or cloud run is authorized by
this implementation record.

## Test Strategy

Exercise the actual harness with explicitly synthetic CLI/SDK callbacks for
success, kill/delete nonzero/exception, pre-existing alias refusal, exact recovery,
pagination and unrelated-resource protection. Real Linux descendant processes
cover normal/nonzero completion alongside existing idle/wall tests. Keep the
existing `python scripts/test_spec_tools.py` CI entry point; it loads the new
standard-library unittest slice without a new dependency or workflow change.

## Acceptance criteria

- Failed/uncertain cleanup never returns 0 or publishes provider-pass evidence.
- Successful evidence appears only after cleanup; failed intent stays private.
- Existing resource aliases are not updated/deleted by this harness.
- Recovery uses only real APIs and exact recorded ownership; no empty-list pass.
- Regressions, strict checker, bilingual docs, owner records and scoped checks pass.
- Actual Docker/cloud acceptance remains separately BLOCKED until authorized.
