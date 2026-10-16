# Four coding verifier completion guards — 2026-10-16

Result: PARTIAL

Scope: Pi, DeepSeek harness, Hermes and Qwen host acceptance controllers/tests and bilingual acceptance/design documentation. Base a361f490555ead0ff67081ffb4874abf292a1b2f. Runtime commands, Dockerfiles, template manifests and workflows are unchanged. Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/98 .

## Reproduction and fix

Actual old verifier subprocesses with synthetic HTTP/model edits passed all four controllers despite incorrect held-out arithmetic: ordinary calculator import passes only the three original inputs; the held-out module import prints static INDEPENDENT_OK then exits0. Baseline/original/heldout process exits are1/0/0, every controller FAILED==0. No external model or cloud call is part of this reproduction. A trivial unconditional sys.exit originally failed the unittest loader and is not claimed as a full counterexample.

The new isolated verifier imports stdlib first, directly compiles actual source bytes, catches BaseException, checks exact original-suite/test-run count3 plus failure/error/skip/expected-failure/unexpected-success state, and requires a per-process ACK minted after the model response. Output from imported code is captured. os._exit0 lacks the ACK even when its exit status is0. Each template remains standalone. This is acceptance for ordinary premature-exit/cache errors, not an OS isolation boundary against arbitrary hostile Python sharing the verifier's authority.

## Actual local checks

- PASS: four acceptance/protocol files,209tests in32.67s; actual subprocess controls include the original conditional static-marker counterexample, sys.exit/os._exit, wrong held-out values, syntax errors, stale actual unchecked-hash pyc, trusted unittest/sitecustomize import isolation, suite counts0/2, loader exit, skips, expected failures and unexpected successes. Stale-cache fixtures first prove normal import consumes the good cache after source becomes wrong; the new verifier rejects the actual bad bytes.
- PASS: broader four-template process/privacy/HTTP/protocol/install regression command,284PASS/5SKIP in62.69s. The5Pi actual-CLI cases initially skipped because the binary was outside PATH; a separate actual pinned-CLI run is recorded below.
- PASS: strict checker all18directories (17products+noncatalog skeleton), no violations.
- PASS:22spec tests,8.546s. CLI/cloud objects in those tests are synthetic fixtures, not Express acceptance.
- Local HTTP: Pi10PASS including actual1.3.0+offline read/find/grep/ls; DeepSeek9PASS; Hermes9PASS with missing real-CLI version explicitlySKIP; model disabled in all three. Qwen9checks included a real version FAIL because host globalqwen is0.19.3 rather than pinned0.23.0. No product version check was relaxed; pinned-binary resolution/recheck is pending.
- Initial check attempts with bare system Python failed before spec execution because PyYAML was absent. Re-running with the existing prepared dependency environment passed as above.
- Intermediate regressions exposed stale Qwen synthetic ACK fixtures and two negative-fixture expected-value mistakes; these were corrected. They did not establish an accepted product failure or a model pass.

## Boundaries and cleanup

No new model/cloud execution was performed by this local change. Historical local/source/image compatible-model runs keep their original hashes and cannot qualify the new controller gate. Parent will separately run exact new host controller hashes against unchanged reviewed image commands, preserving source-image provenance. Native DeepSeek provider credentials are not inferred from compatible Qwen tests. Canonical scripts/express_e2e.py full local abx deploy remains unrun, so no tested_on/provider promotion or merge is claimed.

Local test workers, HTTP servers and disposable projects were cleaned by existing owner runners/temporary-directory fixtures. No cloud resource, credential store, raw model log or private identifier is introduced. Latest-head CI and independent review remain pending at this record's first publication. PR must remain draft until its required actual acceptance gates pass.
