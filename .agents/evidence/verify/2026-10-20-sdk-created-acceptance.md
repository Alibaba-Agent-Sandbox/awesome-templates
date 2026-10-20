# Actual SDK creation controller validation

Status: PARTIAL; local route/ownership regressions PASS, new genuine cloud runs pending.

Before implementation, both added creation-route regressions failed because the explicit selector did not exist. After implementation,60 existing/new tests plus18 subtests passed. A third regression verifies that failure to close a local SDK client cannot lose the known owned cloud ID; its result follows below. Fixtures prove controller routing and ownership only and are not provider acceptance. Existing historical CLI-created receipts remain unchanged and are not reclassified.

Scope: express_e2e.py, run_ci_image_e2e.py, run_steps_e2e.py, test_sdk_creation.py, CI regression entry and bilingual platform/image guides. No template source/runtime/image changes. Real model runs will use exact reviewed images, actual SDK creation, unchanged strict controllers and independent owned cleanup before any new qualification/Issue closure claim.

Third known-ID/close-failure regression PASS; focused3 creation tests PASS,126 Markdown documents/0 broken links and whitespace check PASS. The preceding complete targeted run was60 tests plus18 subtests, before adding the third case. Genuine cloud/controller-source hashes follow separately.

## Actual SDK-created Express runs

PASS: DeepSeek1.1.1 and Qwen2.1.1 actual unchanged reviewed CI images reached official READY, were created through native Python Sandbox.create, passed CLI/SDK smoke and17 strict real-model checks each (0 FAIL/0 SKIP), then independently confirmed sandbox/template/registry cleanup and post-runtime digest. New exact-version receipts live in each template's evidence directory; compatible modelqwen3.8-flash was configured explicitly. Provider qualification retains the earlier step scope and adds this distinct image/model scope.

PASS: Python1.1.1, Node1.1.1 and Media1.0.0 genuine platform steps, actual Python Sandbox.create, CLI/SDK named smoke and independent cleanup. Public commands used --sandbox-create sdk --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a --timeout1200. Their earlier complete21/60/21 workflow receipts retain their own exact-version scope; basic smoke is not relabelled as a full-controller run.

For Issue98, all four current controller hashes now have real-image/model receipts: Pi18, Hermes17 (merged PR135), DeepSeek17 and Qwen17. The latest four actual-subprocess protocol suites passed209 tests, including premature exits, static markers, bytecode/shadow imports, original test identity/results and correct positive controls. [Machine summary](2026-10-20-four-coding-image-revalidation.json). Source runtimes/images were unchanged during those controller reruns; separate already-reviewed ownership correction is tracked in PR135. No fixtures or earlier template versions were promoted.

Publication/current-head CI and normal merge remain required before closing the related Issues.
