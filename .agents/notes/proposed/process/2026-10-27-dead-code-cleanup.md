# Decision: Remove verified unused code and record candidate dispositions

Status: proposed

## Problem

The older fifteen reported test paths were replaced upstream. A new scan identifies unused imports in current tests and acceptance tooling, plus separate runtime-file candidates.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/240.

## Decision

Remove 131 unused imports from 69 test/acceptance files. Keep template runtime implementations, generated process runners, model/provider claims, manifests, Dockerfiles and dependency pins unchanged. Imports with registration, availability-probe or callback effects must not be deleted merely because a name has no lexical read.

## API Design

No supported command, option, public export or runtime protocol is removed. This is scoped maintenance; scanner reachability is not an external-usage proof.

## Alternatives considered

- Delete every scanner finding: rejected because callbacks, dynamic registration, public exports and side-effectful expressions need semantic review.
- Patch the old workspace checkout: rejected because accepted main already resolves some findings and unrelated local changes must remain intact.
- Keep all unused private bindings: retains unnecessary code and, for TypeScript, lets new unused declarations accumulate.

## Dependencies

No runtime dependency or version changes.
Each owning repository has its own Issue, branch, record and validation. No package release or manual deployment is part of this task.

## Test Strategy

Check changed-file imports and Python syntax, affected template regressions, spec tools, all-template checker, document links, canonical process-runner synchronization, local L0 where prerequisites exist and applicable remote CI.
Initial failures, missing prerequisites and later reruns remain separate evidence. Existing behavior tests are reused for deletion-only cleanup; no tests merely assert that source text disappeared.

## Acceptance criteria

- Verified unused bindings are removed while initialization and observable behavior remain.
- Public interfaces, attribution, generated-source ownership and historical evidence are preserved.
- The candidate review below distinguishes removed, upstream-resolved and retained cases.
- Applicable verification and current-head remote CI/review gates pass before merge.

## Consequences

The wider scan has 55 additional F401 import findings in runtime/support files and four F841 findings; they are outside this test-only change. The canonical runner synchronizer covers functions in 15 commands.py files; it does not establish provenance for the separate process.py/tool_process.py helpers. Those similar helpers require owner-by-owner review rather than an assumed generation rule. Any actual generated function must be changed through its canonical source and synchronization. Runtime assignments may perform validation or artifact reads even if their binding is not read. Ruff 0.17.3 reports a parser error on a semicolon followed by the variable name match in browser-use/test_commands.py; the same source compiles in Python, so this is not treated as a verified syntax defect. Dynamic command decorators and hidden commands remain used. ApplicationContractTest is retained and annotated because unittest discovers imported TestCase classes through module globals; lexical F401 is a false positive. The review also found a pre-existing default SDK factory NameError, tracked separately at https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/241; injected-factory tests do not exercise it. This import-only change does not claim to fix that verifier bug. The four F841 candidates are package=copy_private_package(...) (copy side effect), port=u.port (URL validation), pixel=image.getpixel(...) (image access), and runtime=git(...) (fixture revision read); none is removed in this import-only patch.

## Evidence

- [Verification](../../../evidence/verify/2026-10-27-dead-code-cleanup.md)
