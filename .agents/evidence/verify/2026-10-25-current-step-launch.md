# Native steps current-launch verification

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/223
Dependency: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/222

Current contract inspection used the actual installed public client/server 0.4.0a2. Native CLI deploy help supports build steps and explicit empty start/ready commands. Public launch has no steps-build flag. The maintained consumer uses public CLI template launch with the original manifest and owned native reference, then ProviderSandbox/application-client/HTTP; it is not recorded as a Python launch_template call.

Actual old process-monitor reproduction: ten flushed short log lines at 0.15-second intervals, idle 0.5 seconds and wall 5 seconds returned exit 124 after four lines. It was still producing output. The corrected monitor uses os.read plus incremental UTF-8 decoding; the strengthened existing progress test runs ten 0.2-second intervals with idle 0.5 seconds. Spec suite passes 38 tests, including this actual subprocess, hard wall deadline and idle descendant cleanup. Completed leader exit 0 and exit 7 both leave no delayed descendant artifact.

PASS: current native orchestration/process/prepare/image/archive/public-launch/shared-HTTP/assets/cache/batch regressions: 163 tests plus 2 subtests. These are local tooling/process checks, not a cloud matrix. Earlier first invocation failed collection after an obsolete helper fixture was removed; maintained tests were migrated to the current consumer and then passed. The old implementation-shaped SDK/create/deploy/retry/recovery tests were removed with code that has no remaining runtime callers; current public-launch and prepared-image ownership/controller/digest tests remain.

The initial search missed the hidden CI test-list caller of step_acceptance.py. Subsequent explicit .github search identified that caller; it was removed together with the old manual/self-test auditor. The current schema/launch gates remain. It expected the retired receipt arguments instead of current hashed-argument calls. Delete that unused qualification path rather than adding compatibility or new status. Historical raw receipts remain unmodified. Source hashes, native readiness, original asset size/hash/wire bounds, complete controllers and independent owned cleanup are still enforced by the maintained runner.

PASS: catalog checker all 47 conformant; document checker 222 documents and zero failures. Current guides/readmes remove old native-binary installation, sandbox-create/http selectors and manual parallel startup examples. Declared runtime Dockerfiles and template versions are inherited from dependent PR222, not changed again by documentation/tooling cleanup.

The initial local-only verification did not run cloud acceptance. The later scoped native candidate experiments below did create and clean owned resources. No GitHub secrets were uploaded. Current-head remote CI and the final public-source matrix remain separate gates.

## CLI process and file verification

The existing public-source and prepared-image consumers share the same small CLI I/O check: standard CLI exec prints 42; an owned UTF-8 file uploads, is independently read through the SDK, is statted/downloaded with byte equality and is removed with SDK absence. Partial-upload/corrupt-download regressions preserve failure and clean the owned file. No PTY capability or new runner is introduced. The direct public-launch unittest entry point now includes these tests.

## Actual native candidate attempts

The first source/verifier 466f7b4a163298a9a654d20f0a98e3fb5b2e3987 attempt, python-hello/evidence/verification-steps-2026-10-25T150841Z.json, FAILED after 240.505 seconds. Native preparation, current CLI launch and two named CLI responses passed; the new helper mistakenly requested native-only --json on standard exec. This is a harness dispatch error, not a provider JSON capability defect. The guest server version was not read before that failure. The private failed stage was retained. Its wrapper read Git HEAD after execution; the starting runtime SHA and input hashes above, not that late wrapper label, identify the tested source.

The corrected source/verifier 84cd7b1f956e8fef886420c11353cdf9028645e1 attempt, python-hello/evidence/verification-steps-2026-10-25T152027Z.json, PASSED in 27.913 seconds with published CLI 0.5.3, PyPI client 0.4.0a2 and independently observed guest server 0.4.0a2. Two declared smoke commands passed via CLI/Python/host HTTP (6 calls), and the complete HTTP controller reported 21 PASS / 0 FAIL / 0 SKIP. Wrong app token rejection, runtime command bytes, SDK process/files and CLI exec/upload/stat/download/removal passed. Successful private staging was removed.

Both attempts verified sandbox absence independently. Their prepared-template cleanup evidence was successful native deletion plus exact alias inventory absence; it did **not** include per-ID typed GetTemplate 404. The immutable receipts retain their original booleans; this record narrows their interpretation rather than claiming stronger historical evidence. An additional read of the first attempt's known deleted ID on 2026-10-25 independently observed official GetTemplate TemplateNotFound/statusCode 404, but CLI 0.5.3 wrapped it as E5000; no raw IDs/request IDs or error payloads are published.

These are native-step candidate experiments, not public-main or default Express Docker acceptance. They do not certify future SDK a3 or CLI 0.5.4. The default source-Docker path remains unrun locally because Docker is absent.

## Unknown submission and exact journal ownership

Registration submitted without a returned identifier cannot be declared clean merely because the alias inventory is empty. The runner retains the private intent, reports unresolved owned cleanup and stops the existing serial batch before another case. Known identifiers are included even if the alias inventory omits them. Both current consumers use CLI.env HOME for the CLI journal directory, with an independent-home regression. No new recovery framework, state or user flag is added.

## Stronger per-ID cleanup candidate

The latest tooling adds one shared owned-template cleanup helper: delete all exact owned IDs, independently query every known ID until the current native CLI reports E2001 (TemplateNotFoundError), then require empty alias inventory. A successful delete or empty index alone cannot produce PASS. Still-existing IDs, authentication/network/server errors and unknown registration remain failures or unresolved cleanup. No legacy CLI message parsing or E5000 compatibility is accepted.

This stricter candidate depends on the CLI 0.5.4 typed official GetTemplate-404 fix. Local regressions exercise the current E2001 contract; published 0.5.4 actual readback and final remote CI are PENDING. The historical 0.5.3 candidate successes do not verify this new helper. Full two-provider matrices are held until public SDK a3 and CLI 0.5.4 are available and template runtime pins are updated.

## Final local verification

Before the per-ID cleanup delta, the integrated suite passed 191 tests plus 2 subtests; spec tools passed 38, actual published CLI 0.5.3 help contract passed 1, direct public-launch unittest passed 28, catalog checks passed all 47 and document checks passed 222 with zero failures. The restored engineering record replaces an accidental unmerged copy of test source; it preserves the actual earlier results and explicitly records the narrower historical cleanup scope.


After the per-ID cleanup candidate, the relevant current native/process/prepare/archive/public-launch/shared-HTTP/assets/cache/batch/managed/launch-contract suite passed 177 tests. The first command selected a nonexistent old test filename and collected no tests; it was corrected using actual tracked file names before this successful run. Targeted cleanup/public-launch tests passed 64 tests including still-present known ID despite missing inventory, unknown zero-ID registration and E5000/permission rejection; these are local regressions, not public CLI 0.5.4 cloud acceptance.
