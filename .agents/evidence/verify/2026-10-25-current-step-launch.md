# Native steps current-launch verification

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/223
Dependency: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/222

Current contract inspection used the actual installed public client/server 0.4.0a2. Native CLI deploy help supports build steps and explicit empty start/ready commands. Public launch has no steps-build flag. The maintained consumer uses public CLI template launch with the original manifest and owned native reference, then ProviderSandbox/application-client/HTTP; it is not recorded as a Python launch_template call.

Actual old process-monitor reproduction: ten flushed short log lines at 0.15-second intervals, idle 0.5 seconds and wall 5 seconds returned exit 124 after four lines. It was still producing output. The corrected monitor uses os.read plus incremental UTF-8 decoding; the strengthened existing progress test runs ten 0.2-second intervals with idle 0.5 seconds. Spec suite passes 38 tests, including this actual subprocess, hard wall deadline and idle descendant cleanup. Completed leader exit 0 and exit 7 both leave no delayed descendant artifact.

PASS: current native orchestration/process/prepare/image/archive/public-launch/shared-HTTP/assets/cache/batch regressions: 163 tests plus 2 subtests. These are local tooling/process checks, not a cloud matrix. Earlier first invocation failed collection after an obsolete helper fixture was removed; maintained tests were migrated to the current consumer and then passed. The old implementation-shaped SDK/create/deploy/retry/recovery tests were removed with code that has no remaining runtime callers; current public-launch and prepared-image ownership/controller/digest tests remain.

Calling search before deletion showed step_acceptance.py was referenced only by its own tests/manual entry and the corresponding e2e test-list item. It expected the retired receipt arguments instead of current hashed-argument calls. Delete that unused qualification path rather than adding compatibility or new status. Historical raw receipts remain unmodified. Source hashes, native readiness, original asset size/hash/wire bounds, complete controllers and independent owned cleanup are still enforced by the maintained runner.

PASS: catalog checker all 47 conformant; document checker 222 documents and zero failures. Current guides/readmes remove old native-binary installation, sandbox-create/http selectors and manual parallel startup examples. Declared runtime Dockerfiles and template versions are inherited from dependent PR222, not changed again by documentation/tooling cleanup.

NOT RUN: real current-package native step/cloud acceptance, current-head remote CI and final public-source matrix. No cloud resources or GitHub secrets were created by local verification. Failed cloud attempts must retain their separate private journals and sanitized receipts. Merging tooling alone cannot certify a new runtime/provider.

## Actual CLI process and file-transfer coverage

Actual public 0.5.3 help with explicit opensandbox provider confirms exec, top-level upload/download and sandbox files stat/rm (upload is not a files subcommand). The existing public-launch runner and prepared-template consumer now share a bounded assertion helper: real CLI exec JSON result, owned UTF-8 upload, independent SDK exact-byte readback, CLI stat/download byte comparison, CLI deletion and independent SDK absence, with finally cleanup for partial failures. No new runner, user option or PTY assumption is added. Corrupt download and partial-upload regressions both fail and clean only the owned file. Targeted public-launch/archive/steps suite: 55 PASS. Full real public-package runtime coverage remains pending; help or mocks are not a cloud pass.
