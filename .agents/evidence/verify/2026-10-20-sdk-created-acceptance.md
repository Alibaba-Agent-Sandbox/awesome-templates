# Actual SDK creation controller validation

Status: PARTIAL; local route/ownership regressions PASS, new genuine cloud runs pending.

Before implementation, both added creation-route regressions failed because the explicit selector did not exist. After implementation,60 existing/new tests plus18 subtests passed. A third regression verifies that failure to close a local SDK client cannot lose the known owned cloud ID; its result follows below. Fixtures prove controller routing and ownership only and are not provider acceptance. Existing historical CLI-created receipts remain unchanged and are not reclassified.

Scope: express_e2e.py, run_ci_image_e2e.py, run_steps_e2e.py, test_sdk_creation.py, CI regression entry and bilingual platform/image guides. No template source/runtime/image changes. Real model runs will use exact reviewed images, actual SDK creation, unchanged strict controllers and independent owned cleanup before any new qualification/Issue closure claim.

Third known-ID/close-failure regression PASS; focused3 creation tests PASS,126 Markdown documents/0 broken links and whitespace check PASS. The preceding complete targeted run was60 tests plus18 subtests, before adding the third case. Genuine cloud/controller-source hashes follow separately.
