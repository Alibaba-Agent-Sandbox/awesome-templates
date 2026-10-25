# CLI exec output contract verification

Date: 2026-10-25
Result: PARTIAL — local regression PASS; current-head CI/review/merge and new public cloud matrix pending.

Source base: public templates389302f5dc9429a4b215801dbd4025d4dba95f7e. Official CLI0.5.5 and paired SDK0.4.0a6 were used by the original workflow. Root and an independent peer reviewed the installed CLI generic exec formatter and current verifier; CI automatically selects JSON. The original small amp/agents-cli/chrome reports all fail only at cli-process-and-files / CLI exec result, after successful source launch, three-consumer application smoke, wrong-token rejection, source identity and SDK process/files. Their original cleanup independently records sandbox and prepared artifacts absent. The [unaltered amp report](2026-10-25-ci-cli-exec-initial-fail.json) is retained; no raw private logs or native IDs are introduced.

The new CI-output regression against unchanged source failed once with31 passing tests. The corrected helper passed32 tests in1.76seconds, including nonzero/wrong-output rejection, Unicode transfers, corrupted downloads and partial-upload cleanup. This is an existing-helper regression, not a product CLI change or a cloud pass. The original GitHub Actions attempt remains https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40233330458.

The helper continues the standard provider-selected exec route; it adds no native flag or new runner. Existing managed acceptance separately exercised explicit JSON and ordinary non-CI text on the public CLI. Further exact-head results are appended after execution, rather than changing this original scope.
