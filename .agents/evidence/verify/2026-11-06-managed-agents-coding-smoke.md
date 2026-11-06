# Verification: Existing-source managed Agent coding smoke

- Date: 2026-11-06
- Result: PARTIAL; scoped source/process/document checks pass, new image and real model acceptance remain pending.
- Base: `e4c6c1d8ee54d3f963e6b6a281442d7f018fea32` plus the scoped files in this change.
- Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295
- PR: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/296

## Reviewed change

Independent runtime and CLI reviewers agreed that the earlier Gateway smoke proved
correct CSV output but did not establish an existing-source edit with unchanged
original tests. The minimal correction preserves the public Gateway-only flow:

- Add a small, deliberately defective CSV starter and original tests under the
  explicitly named `/workspace/agents-api-demo` directory in the guest recipe.
- First turn repairs the existing source and publishes its source, summary and
  repair report; the second modifies the same program to add shares.
- Check decimal-valued downloaded output independently and retain each turn's
  immutable source artifact. Do not execute Agent-generated code on the host.
- Permit a trusted in-process engineering inspector after each published turn
  and before continuation/close. Provider-side source/test hash checks and held-out
  execution remain separate acceptance, with no new public exec route or business
  credential requirement.

The template contract becomes 0.1.1. Published SDK pins remain 0.4.0a6 until a real
compatible release exists; this change does not pretend that a6 contains the new
managed modules or silently replace pip installation with source artifacts.

## Executed checks

Using the task's existing Python test environment (pytest 9.2.0, httpx 0.28.1):

| Command / check | Result |
| --- | --- |
| `python -m pytest agents-api/test_smoke.py -q` | PASS: 7 tests. Includes real execution of the trusted starter/original tests to establish the two deliberate baseline failures; callback order; cleanup failure preservation; wrong/non-finite CSV rejection. |
| `python scripts/check_template.py agents-api` | PASS: conformant. |
| `python scripts/check_docs.py` | PASS: 232 documents, zero local link failures. |
| `git diff --check` | PASS. |
| Targeted `scripts/run_local_e2e.py` `_run_one(agents-api, shim)` with its own helper path and the active environment on PATH | PASS: actual private managed bridge readiness, authentication and closed route surface. This is only the managed template's local process check, not the full catalog L0 run. |

The first pytest attempt used the checker-only environment and failed before test
collection because pytest was absent. An initial direct L0 helper invocation lacked
its scripts import path; another used the system child Python without httpx. Both
were harness setup failures before successful bridge acceptance. The successful
targeted invocation used the existing SDK test environment and the normal active
environment PATH; no dependency or product behavior was weakened.

## Scope and cleanup

No image was built and no model or cloud API was called for this verification.
No Provider acceptance follows from these local checks. The exact new recipe,
source-candidate and eventual released-package image paths require fresh acceptance.
The independent controller must prove unchanged original test bytes, actual modified
source identity and held-out results inside the owned Sandbox before close.

Local fixture tests used temporary directories. The L0 runner stopped its owned
private bridge and removed its temporary Python shim in its normal teardown. No
cloud resource was created or deleted. Previous source/cloud receipts retain their
original sources and narrower scope; none is rewritten by this change.
