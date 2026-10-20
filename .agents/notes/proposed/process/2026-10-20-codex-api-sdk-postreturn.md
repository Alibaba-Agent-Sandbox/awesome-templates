# Decision: Require completed independent Codex API tests and real SDK acceptance

Status: proposed

## Problem

[Issue23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23) requires an actually useful native Codex session API with current Express/SDK proof. Review reproduced a false green in its fixed-test controller: a fixed authored source printed Ran6tests/OK and exited0during import, so no six-test suite ran but the old exit/log predicate accepted it. Historical source-runtime/model results are separate from current canonical template acceptance.

## Decision

Keep the six controller-owned assertions and require their real complete unittest result plus a fresh controller-only post-return completion ACK on every successful independent rerun. Reject skip/expected/unexpected failures and premature exit, even with forged summary text. Add explicit generation2 E2E_SERVER_TOKEN Bearer support separately from the legacy gateway token header. Preserve public product API/runtime/dependency/version/default permissions; actual model SDK acceptance runs only in a fresh owned cloud sandbox with documented explicit model/profile configuration.

## API Design

Only acceptance helpers change: _fixed_tests adds verification_complete based on exact fresh ACK and zero exit; both post-agent and final resumed checks require it. The baseline remains the original deliberately failing six tests. Fixed assertions never become model-editable files. New E2E_SERVER_TOKEN is independent of existing E2E_TOKEN/ABX_SERVER_TOKEN legacy behavior. A provider/model key never becomes a gateway token. Controller CLI remains source compatible; no new public session or native command schema.

## Alternatives considered

Zero exit or familiar unittest summary text cannot prove the tests reached completion. Editing original tests or accepting assistant markers/artifact labels would weaken the contract. Host execution of model-generated code is excluded. A random ACK catches premature exit but does not isolate adversarial same-UID code that can inspect its own execution; no stronger security claim is made. Default workspace-write is not silently replaced: any Express bypass profile stays an explicit documented per-server configuration.

## Dependencies

Unchanged template2.0.0, actual native Codex0.162.1, servere2cb27e24fde0a67112f82b8d44af463445a5d1a and approved explicit Responses-compatible model base/key. Operator SDK exact sourced4d93e8cbb986f33a8868f7a4139ed0edb49eaba. Existing declared container-isolation/bypass option if required; no fabricated vendor capability or endpoint. Canonical build/source proof and model proof remain separate.

## Test Strategy

A fixed authored local negative fixture proves the old predicate accepts forged summary/early exit with no tests. The fake remote controller now includes this failure case and must reject it, while genuine six-test repair/resume positive control passes. Existing real authored process/HTTP/SSE/resource/deadline/redaction regressions remain. Verify new Bearer/gateway header separation. Then actual current native L1 and SDK-created Express canonical smoke/model edit/report/artifact/exact-session-resume/original-six-tests/cleanup must pass with exact current controller/source hashes.

## Acceptance criteria

Relevant source/spec/docs/record/latest CI pass; the false test completion no longer passes. Actual SDK-created current-source Express and native model/source/artifact/six-test/exact-thread resume proof with independent owned cleanup, using explicit profile configuration. Complete bilingual docs/design/current records and normal merge before Issue23closure. Historical source-only, model-off, failure and missing backend scopes remain distinct.

[Verification](../../../evidence/verify/2026-10-20-codex-api-sdk-postreturn.md).
