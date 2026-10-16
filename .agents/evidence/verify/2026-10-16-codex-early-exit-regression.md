# Codex verifier premature-exit review — 2026-10-16

Result: PARTIAL pending the hardened actual-model run and canonical deployment.
Initial reviewed source: `24a029e9e53a1dd624be1e2ee38e026d9cbe13e6`.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/97.

## Reproduced failure

An independent peer exercised the public HTTP controller's fake-remote fixture
with actual subprocesses. A source file printing a fake unittest count and then
calling sys.exit(0) passed the earlier controller without reaching assertions.
This is an acceptance-verifier defect, not evidence that the genuine prior model
run failed. That actual reviewed-image run passed 17 HTTP/model checks, a separate
existing-calculator task and owned sandbox/template cleanup. Its shared registry
image remains owned by the ongoing parent batch; final cleanup is still pending.

## Correction and executed checks

The current verifier uses Python -I to preload trusted standard-library modules,
compiles actual implementation and test source bytes rather than agent-provided
bytecode, catches BaseException, requires original tests=2, generated tests>=1,
all tests successful without skips/expected failures/unexpected successes, and
requires a fresh completion acknowledgement chosen only after the agent exits.
These completion checks do not claim isolation from hostile same-authority code.

Independent root run of the frozen scratch candidate: 11 tests PASS, 2.712 seconds;
peer final run: 11 PASS, 2.754 seconds. Twelve negative subcases cover changed
original tests, unchanged source, missing report, incorrect held-out results,
baseline import errors, sys.exit(0) with fake unittest output, os._exit(0), zero
generated tests, exit during test loading, expected failures, shadowed unittest
and stale valid bytecode. The bytecode control first proves a legacy import
actually loads cached good code while the actual source is bad; the new source
compiler rejects the bad implementation. No model/cloud run is claimed by these
synthetic fixture controls. The hardened public controller needs a new real run.

## Final scoped local verification

After applying the frozen candidate: 11 regression tests PASS in 2.686 seconds;
strict Codex checker PASS; updated Codex local HTTP suite PASS with its model task
explicitly SKIP. The available host CLI reports 0.159.2, so that local result is
not evidence for the image's pinned 0.162.1 CLI. The initial 24a029e head's two
complete remote local suites, image-build(codex) and plan all passed; these are
historical checks and must not stand in for the hardened head's new CI.

## Hardened actual-image model run

PASS: frozen controller `06071e48fb00aa6bdfe280c2b8f498c9afd41c8d`
against the unchanged, byte-reviewed image from parent `a361f49`:
17 HTTP/model checks, zero FAIL, zero SKIP; compatible qwen3.8-flash. The specific
existing Fibonacci baseline, actual CLI tool execution, original-test preservation,
report/exact marker artifact, isolated actual-source held-out assertions and the
trusted complete test rerun all passed. A separate existing-calculator task also
passed its original tests and six held-out cases using the hardened external
source verifier. Both actual verifier receipts require completion after agent exit.

Root independently compared the public controller SHA256 with the exact source
file and checked all nine external existing-source boolean flags and all four
owned sandbox/template cleanup flags. SDK sandbox absence and strict paginated
official exact-template-name absence passed. The borrowed registry image remains
owned by the ongoing 13-image batch and is not final registry cleanup acceptance.
Sanitized component evidence:
[codex image runtime](../../../codex/evidence/image-runtime-hardened-2026-10-16.json).
Full canonical deployment remains NOT RUN; the PR and provider status remain draft
and experimental. No express-*.json receipt or tested_on promotion is created.

The hardened product head `06071e4` subsequently completed all four actual remote
checks successfully: two full local HTTP/regression CI runs, image-build(codex)
and plan. The final documentation/evidence-only head gets its own CI; this
product-head result is not relabeled as that later head's checks. Final scoped
document checks: 25 existing local link targets, strict Codex checker and diff
whitespace pass.
