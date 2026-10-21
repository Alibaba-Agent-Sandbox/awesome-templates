# Verification: comprehensive template review

Result: PARTIAL. Date: 2026-10-21. Tested main revision `d758184ad67ebaa0b3c7169efb3f254534c1a5cb`.

The original64 Issue cohort is52 closed/12 open; PR173/174 are still drafts at the inventory read. All44 installable templates were tested again locally. The skeleton is an additional local HTTP target. Existing current-version Express evidence was independently re-audited, not rerun or relabelled. Missing credentials do not exempt program/API tests; vendor-authentication omissions stay explicit.

## Executed checks

- `python scripts/test_spec_tools.py`:57 tests PASS,13.902seconds.
- `python scripts/check_template.py --all --strict`:0 claimed-spec failures.
- `python scripts/check_docs.py`:200 public Markdown documents,0local-link failures; no network/cloud claim.
- `python scripts/step_acceptance.py --require-http`:44/44 current runtime receipts and44/44 current full external HTTP controller receipts PASS; each binds runtime inputs/current controller/owned cleanup. This does not certify every product/model or Docker image.
- `python scripts/run_local_e2e.py`:35PASS10FAIL out of45 including skeleton. Failures retained; the local environment lacks several exact native/browser/document/frontend prerequisites. After installing declared Pillow11.3.0, OCR rerun PASS7checks/1explicit native-engineSKIP. The initial incorrect local Pillow version is not a product failure or a native OCR pass.
- Separate existing regression suites in44 isolated subprocesses:33suitesPASS/11FAIL;1347testsPASS55FAIL8SKIP. These include real native-engine cases, so do not describe this as a passing local full suite. No model/cloud credentials forwarded.
- The exact main revision hosted CI:51completedSUCCESS, including all44image builds, mandatory offline engine jobs and full local-e2e. Its actual completed job log confirms45PASS0FAIL HTTP targets with prerequisites installed. Hosted success and incomplete-operator failures remain different execution records.

## Per-template results

Local columns retain the initial execution. OCR has the successful dependency-corrected rerun above. A PASS suite can contain explicit native/model skips; consult its summary. The hosted CI column applies to the completed exact-main job, with44image builds and45HTTP targets.

| Template | Local existing regressions | Initial local HTTP | Current Express HTTP | Hosted complete environment |
| --- | --- | --- | --- | --- |
| agents-cli | PASS: 45 passed in 6.47s | FAIL | [PASS](../../../agents-cli/evidence/verification-steps-2026-10-20T154625Z.json) | PASS |
| aider | PASS: 72 passed in 10.53s | PASS | [PASS](../../../aider/evidence/verification-steps-2026-10-20T135354Z.json) | PASS |
| amp | PASS: 27 passed in 8.70s | PASS | [PASS](../../../amp/evidence/verification-steps-2026-10-20T154625Z.json) | PASS |
| apply-patch | FAIL: 2 failed, 8 passed in 1.09s | FAIL | [PASS](../../../apply-patch/evidence/verification-steps-2026-10-20T154625Z.json) | PASS |
| appworld | PASS: 33 passed in 0.37s | PASS | [PASS](../../../appworld/evidence/verification-steps-2026-10-21T000253Z.json) | PASS |
| browser-automation | FAIL: 5 failed, 8 passed in 1.93s | FAIL | [PASS](../../../browser-automation/evidence/full-http-steps-2026-10-20T103410Z.json) | PASS |
| browser-use | FAIL: 5 failed, 9 passed in 22.87s | PASS | [PASS](../../../browser-use/evidence/verification-steps-2026-10-20T153859Z.json) | PASS |
| chrome | PASS: 22 passed in 0.38s | PASS | [PASS](../../../chrome/evidence/verification-steps-2026-10-20T230349Z.json) | PASS |
| claude-code | PASS: 10 passed, 9 subtests passed in 0.29s | PASS | [PASS](../../../claude-code/evidence/verification-steps-2026-10-20T154625Z.json) | PASS |
| cline | PASS: 30 passed in 0.83s | PASS | [PASS](../../../cline/evidence/verification-steps-2026-10-20T201959Z.json) | PASS |
| code-server | FAIL: 7 failed, 9 passed in 2.77s | FAIL | [PASS](../../../code-server/evidence/verification-steps-2026-10-20T135352Z.json) | PASS |
| codex | PASS: 11 passed, 27 subtests passed in 2.35s | PASS | [PASS](../../../codex/evidence/verification-steps-2026-10-20T154825Z.json) | PASS |
| codex-agent-api | PASS: 27 passed in 3.06s | PASS | [PASS](../../../codex-agent-api/evidence/native-model-sdk-steps-2026-10-20T175340Z.json) | PASS |
| copilot-cli | PASS: 24 passed in 1.22s | PASS | [PASS](../../../copilot-cli/evidence/verification-steps-2026-10-20T171425Z.json) | PASS |
| crush | FAIL: 3 failed, 11 passed in 5.79s | PASS | [PASS](../../../crush/evidence/verification-steps-2026-10-20T131749Z.json) | PASS |
| deepagents | FAIL: 4 failed, 7 passed in 4.29s | PASS | [PASS](../../../deepagents/evidence/verification-steps-2026-10-20T141151Z.json) | PASS |
| deepseek-harness | PASS: 72 passed in 19.34s | PASS | [PASS](../../../deepseek-harness/evidence/verification-steps-2026-10-20T154957Z.json) | PASS |
| dev-services | FAIL: 5 failed, 7 passed in 0.20s | PASS | [PASS](../../../dev-services/evidence/full-http-steps-2026-10-20T130648Z.json) | PASS |
| document-tools | FAIL: 14 failed, 47 passed, 1 skipped in 1.89s | FAIL | [PASS](../../../document-tools/evidence/full-http-steps-2026-10-20T143722Z.json) | PASS |
| droid | PASS: 59 passed in 9.46s | PASS | [PASS](../../../droid/evidence/verification-steps-2026-10-20T212811Z.json) | PASS |
| gemini | PASS: 27 passed, 1 skipped in 8.70s | PASS | [PASS](../../../gemini/evidence/verification-steps-2026-10-20T155048Z.json) | PASS |
| goose | FAIL: 3 failed, 10 passed in 2.67s | PASS | [PASS](../../../goose/evidence/verification-steps-2026-10-20T135350Z.json) | PASS |
| grok | PASS: 26 passed in 0.84s | PASS | [PASS](../../../grok/evidence/verification-steps-2026-10-20T201501Z.json) | PASS |
| hermes-agent | PASS: 65 passed in 13.06s | PASS | [PASS](../../../hermes-agent/evidence/verification-steps-2026-10-20T151019Z.json) | PASS |
| kimi-code | PASS: 10 passed in 1.08s | PASS | [PASS](../../../kimi-code/evidence/verification-steps-2026-10-20T155159Z.json) | PASS |
| media-tools | PASS: 59 passed in 9.92s | PASS | [PASS](../../../media-tools/evidence/full-http-steps-2026-10-20T131812Z.json) | PASS |
| muse | PASS: 57 passed in 2.98s | PASS | [PASS](../../../muse/evidence/verification-steps-2026-10-21T031347Z.json) | PASS |
| next-app | FAIL: 4 failed, 13 passed in 0.48s | FAIL | [PASS](../../../next-app/evidence/full-http-steps-2026-10-20T130712Z.json) | PASS |
| node-web | PASS: 5 passed in 4.83s | PASS | [PASS](../../../node-web/evidence/full-http-steps-2026-10-19T183324Z.json) | PASS |
| ocr | PASS: 26 passed, 1 skipped in 2.40s | FAIL | [PASS](../../../ocr/evidence/full-http-steps-2026-10-20T061143Z.json) | PASS |
| openclaw | PASS: 43 passed in 16.82s | PASS | [PASS](../../../openclaw/evidence/verification-steps-2026-10-20T170739Z.json) | PASS |
| opencode | PASS: 57 passed in 7.42s | FAIL | [PASS](../../../opencode/evidence/verification-steps-2026-10-20T160725Z.json) | PASS |
| osworld | PASS: 43 passed in 2.96s | PASS | [PASS](../../../osworld/evidence/verification-steps-2026-10-20T171144Z.json) | PASS |
| pi | PASS: 77 passed, 5 skipped in 14.75s | PASS | [PASS](../../../pi/evidence/verification-steps-2026-10-20T155246Z.json) | PASS |
| polyglot-toolchain | PASS: 6 passed in 1.41s | PASS | [PASS](../../../polyglot-toolchain/evidence/verification-steps-2026-10-20T135358Z.json) | PASS |
| prime-agent | PASS: 35 passed in 0.19s | PASS | [PASS](../../../prime-agent/evidence/verification-steps-2026-10-21T000126Z.json) | PASS |
| python-hello | PASS: 4 passed in 0.22s | PASS | [PASS](../../../python-hello/evidence/full-http-steps-2026-10-19T183219Z.json) | PASS |
| qm | PASS: 14 passed in 0.06s | PASS | [PASS](../../../qm/evidence/verification-steps-2026-10-21T021039Z.json) | PASS |
| qm-sandbox | PASS: 37 passed in 1.31s | PASS | [PASS](../../../qm-sandbox/evidence/verification-steps-2026-10-21T021037Z.json) | PASS |
| qoder | PASS: 33 passed in 9.80s | FAIL | [PASS](../../../qoder/evidence/verification-steps-2026-10-20T155408Z.json) | PASS |
| qwen-code | PASS: 70 passed in 10.84s | FAIL | [PASS](../../../qwen-code/evidence/verification-steps-2026-10-20T155502Z.json) | PASS |
| stagehand | FAIL: 3 failed, 21 passed in 1.47s | PASS | [PASS](../../../stagehand/evidence/verification-steps-2026-10-20T190109Z.json) | PASS |
| swe | PASS: 36 passed in 1.45s | PASS | [PASS](../../../swe/evidence/verification-steps-2026-10-20T143844Z.json) | PASS |
| tau2-bench | PASS: 35 passed in 0.87s | PASS | [PASS](../../../tau2-bench/evidence/verification-steps-2026-10-20T212600Z.json) | PASS |

## Evidence and limits

[Regression results](2026-10-21-comprehensive-template-review-regressions.json), [local HTTP results](2026-10-21-comprehensive-template-review-local-http.json), [current receipt audit](2026-10-21-comprehensive-template-review-steps.json), [51 CI checks](2026-10-21-comprehensive-template-review-ci.json), [actual hosted HTTP summary](2026-10-21-comprehensive-template-review-hosted-http.json).

The fresh [Gemini PR174](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/174) separately fixes a reproduced second-turn native function-call placeholder defect. Its published runtime393c5cc has actual original CLI0.64.0 two-turn read_file API fixture2completed/0failed/1tool-result and a separate actual approved-compatible-model19PASS0FAIL0SKIP source-edit/original3tests/report/nonce/held-outs/post-returnACK run. Both canonical outer resources and secondary fixtures/listeners have independent cleanup confirmation. Google-hosted account/model authentication is NOT_RUN. These candidate results do not retroactively certify main Gemini2.0.1 or Claude candidate1.3.0.

Claude PR173 remains blocked on a failed native stream delivery. Cursor/Devin and the remaining hardware/provider/account-specific work are not delivered by this review. New unavailable templates have no source tests yet; they cannot be counted among the44 installables or marked completed. No Issues are closed by this evidence PR.

Owned cloud resources for Gemini are already independently absent. Temporary recovery logs stay private until evidence/merge review finishes. Historical merged evidence and unrelated artifacts are preserved. The original dirty checkout is untouched; this record uses an isolated branch.
