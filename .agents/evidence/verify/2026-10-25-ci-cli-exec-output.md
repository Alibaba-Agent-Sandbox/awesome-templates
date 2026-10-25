# CLI exec output contract verification

Date: 2026-10-25
Result: PARTIAL — local regression PASS; current-head CI/review/merge and new public cloud matrix pending.

Source base: public templates389302f5dc9429a4b215801dbd4025d4dba95f7e. Official CLI0.5.5 and paired SDK0.4.0a6 were used by the original workflow. Root and an independent peer reviewed the installed CLI generic exec formatter and current verifier; CI automatically selects JSON. The original small amp/agents-cli/chrome reports all fail only at cli-process-and-files / CLI exec result, after successful source launch, three-consumer application smoke, wrong-token rejection, source identity and SDK process/files. Their original cleanup independently records sandbox and prepared artifacts absent. The [unaltered amp report](2026-10-25-ci-cli-exec-initial-fail.json) is retained; no raw private logs or native IDs are introduced.

The new CI-output regression against unchanged source failed once with31 passing tests. The initial generic-JSON candidate passed32 simulated tests in1.76seconds, including nonzero/wrong-output rejection, Unicode transfers, corrupted downloads and partial-upload cleanup. This is an existing-helper regression, not a product CLI change or a cloud pass. The original GitHub Actions attempt remains https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40233330458.

The helper continues the standard provider-selected exec route; it adds no native flag or new runner. Existing managed acceptance separately exercised explicit JSON and ordinary non-CI text on the public CLI. Further exact-head results are appended after execution, rather than changing this original scope.

## Actual Express dispatch correction

The first candidate dbe0559b84a42cb61aecde02f0e84e3c10c8a72d incorrectly generalized the generic formatter to Express. Independent actual official CLI 0.5.5 execution in a fresh HOME, with CI=true and no backend credentials, rejected global --json for Express standard exec before any cloud access. The earlier simulated pass did not cover this dispatch. This failed candidate scope is retained here.

The corrected helper keeps Express standard exec text, rejects nonzero process exits through the existing CLI adapter and checks stdout42. OpenSandbox uses explicit global JSON and checks both process status and stdout. No --native flag, fallback parser or CI environment mutation is added. The existing installed-CLI contract suite now executes both provider parse paths with an intentionally invalid fixture ID and no credentials: Express+JSON must be rejected; Express text and OpenSandbox JSON must pass parsing and fail only at the nonconfigured backend boundary. Those negative controls create no resources.

PASS: corrected public-launch plus actual installed-CLI contract suites completed 36 tests in 4.05 seconds with the official 0.5.5 binary. The independent [original parser rejection](2026-10-25-express-exec-json-rejected.json) is preserved. Fresh cloud matrix verification remains pending.
