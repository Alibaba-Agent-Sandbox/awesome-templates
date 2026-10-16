# Qoder, DeepSeek and Hermes completion review

Date: 2026-10-16 UTC

Result: PARTIAL

Base revision: `2acb53481739e9585803076dd4c05ce5c2048219` plus the scoped working-tree files:
`qoder/`, `deepseek-harness/`, `hermes-agent/`, their `docs/design/` documents, and this
engineering note/evidence pair. Other pre-existing changes were preserved.

## Environment

Python 3.13 test/server environment with the local paired Agent Sandbox SDKs, pytest 9.1.1,
httpx 0.28.1 and PyYAML 6.0.3. Qoder 1.1.72 was installed with npm 10 into an isolated prefix.
Hermes source v0.22.1 resolved through the annotated tag to commit
`297552a9d646119871391d202509822cd86330df`; its frozen uv.lock installed 67 packages into
an isolated Python 3.14.6 environment, including OpenAI SDK 2.24.0. The source project
metadata says 0.0.0; upstream's install-stamp writer supplies the verified release provenance.

## PASS: static and local behavior

- `python3 scripts/check_template.py qoder`: exit 0, conformant.
- `python3 scripts/check_template.py deepseek-harness`: exit 0, conformant.
- `python3 scripts/check_template.py hermes-agent`: exit 0, conformant.
- `python3 -m pytest --import-mode=importlib -q qoder/test_commands.py qoder/test_e2e_protocol.py deepseek-harness/test_commands.py deepseek-harness/test_e2e_protocol.py hermes-agent/test_commands.py hermes-agent/test_e2e_protocol.py`: exit 0, 106 passed after the final code changes, including public worker HTTP tool round trips, byte-limited file tools, safe failure classification and configurable model acceptance budgets.
- Scoped execution of `scripts/run_local_e2e.py`'s `_run_one` for these three directories,
  using its real `_child_env`, health, subprocess, cleanup and Python-shim paths: all 3 pass.
  Model execution was disabled as required by L0. Every HTTP smoke completed with zero failures.
- Independent temporary-workspace HTTP runs of all three `e2e_test.py` files also exited 0.
- Real `qodercli --version`: `1.1.72`.
- Real `hermes --version`: v0.22.1, upstream revision `297552a9`, Python 3.14.6,
  OpenAI SDK 2.24.0. Real `hermes chat --help` confirms all wrapped flags.
- Markdown relative links in the six READMEs and three design documents resolve.
- Configured credential-value scan over all scoped source/docs/records: pass, no values found.
- `git diff --check -- qoder deepseek-harness hermes-agent docs/design/qoder.md docs/design/deepseek-harness.md docs/design/hermes-agent.md`: exit 0.

The regressions cover target credential decisions, forced-off/required-model conflict,
real file-tool execution, path/symlink traversal rejection, secret-filtered shell environments,
argument quoting, error propagation, redaction, model round-trip tool results and bounded turns.
Descendants within the owned process group are stopped on success, nonzero exit and deadline cancellation. Hermes authority/managed-worker groups are outside that scope; see the limitation below. The Linux runner drains both pipes concurrently and observes the leader with waitid(WNOWAIT), retaining its PID/PGID identity until group cleanup; only then does it reap. DeepSeek worker cancellation uses a nonrecoverable signal exception to unwind the active tool runner and clean its separate shell group before bounded forced shutdown. Real fake-provider HTTP/worker/shell regressions exercise both the internal deadline and the outer owner deadline. Acceptance cannot pass
from a response marker, modified tests or incorrect held-out calculations. Actual `python3 -I`
verification processes ignore writable `unittest.py` and `sitecustomize.py` shadows.

Early validation caught default pytest module-name collisions, literal-private-text in a test's
own traceback source, and a local-runner PATH ordering mistake that selected Hermes Python
instead of the server environment. Final runs use importlib collection, dynamically constructed
private test text, and the server test environment first on PATH. An intermediate generated budget test also misnamed its configuration attribute; that was corrected before the final 106-test pass. These intermediate failures were not counted as passes.

## Real compatible-model coding acceptance on a local target

Both runs started the repository server in a temporary workspace, required real model execution
with `E2E_RUN_LLM=1` and `E2E_REQUIRE_LLM=1`, and ran each committed `e2e_test.py` unchanged.
Credentials, endpoint and model selection were injected into child environments and are omitted.

- **DeepSeek harness:** actual Chat Completions requests and tool execution, rather than a
  mock. The supplied model belongs to an OpenAI-compatible service; this does not establish
  acceptance of the native DeepSeek endpoint. HTTP suite exited 0.
- **Hermes:** actual pinned upstream v0.22.1 CLI, custom provider, local terminal/file toolsets
  and real compatible-model requests. HTTP suite exited 0.

Each run first reproduced the seeded source defect with three failing unittest cases, then
verified a changed calculator source, byte-identical original tests, a nonempty REPORT.md and
an exact new ABX_E2E_OK artifact through the target files API. An independent isolated unittest
process passed all three cases and a separate isolated process passed held-out integer/float
inputs. The model response alone was not used as acceptance. Both owned project directories
were deleted; the temporary server/workspace resources were stopped and removed.

The first complete DeepSeek and Hermes successes preceded the owned-process follow-up.
After that follow-up, Hermes was independently rerun with the actual pinned CLI and again
passed every artifact, unchanged-test, independent unittest and held-out assertion; exit 0.
A DeepSeek repeat with the older 300-second coding budget failed before model completion,
while reproducing the seeded defect and cleaning its owned project successfully. That run
omitted the error body and did not record a safe category, so its cause is not asserted.
A separate real compatible-model request through the latest public DeepSeek worker completed
successfully. An actual local HTTP provider/worker/file-tool round trip also passes as a
regression. The final bounded DeepSeek coding repeat used the public command's 600-second
default and safe fixed error categories. It passed every source/artifact/unchanged-test assertion,
independent unittest and held-out checks, plus owned project cleanup; exit 0. This final
repeat establishes compatible-model coding behavior on the latest worker implementation.

These are local target + real remote model results. They are not image builds, Express L2,
Express model acceptance, or evidence for any additional sandbox provider.

## BLOCKED / not claimed

- Hermes whole-workload cancellation is not implemented. The pinned upstream CLI submits
  work to a detached canonical gateway and separate managed workers. Its owned CLI group
  cleanup is verified; accepted authority work can continue after the CLI deadline. No
  per-session gateway interrupt is claimed. Destroying the sandbox is the whole-workload
  stop boundary. The upstream idle-exit path has a default 600-second idle window and does
  not exit while work remains active. The successful coding checks do not prove cancellation.
- Post-run Hermes cleanup inspected process identities using pidfds and matched only expired
  temporary HERMES_HOME roots created by these tests, plus the expected gateway/managed-worker
  argv. Zero remaining process identities matched that strict condition; no unrelated gateway
  was stopped. This observation is not proof that arbitrary detached authority work is cancelled
  by the template's process-group deadline.
- Qoder real-model acceptance: QODER_PERSONAL_ACCESS_TOKEN is unavailable. The missing-key
  guard was tested; an unrelated OpenAI API key cannot authenticate Qoder.
- Native DeepSeek acceptance: DEEPSEEK_API_KEY is unavailable. The separate compatible-model
  success above does not remove this limitation.
- L1 image builds and L2 template deployment: no usable Docker executable/daemon in this
  environment. Installing the real CLI locally does not validate an image or deployment.
- Optional Hermes browser/desktop/messaging/backend integration and L4: not run, outside the
  explicit local coding slice.
- Whole-repository local suite integration, shared catalog/CI updates and required remote CI/review/PR merge: no merge claim is made by this local verification.

No provider evidence JSON was fabricated, and `tested_on` remains empty in all three templates.
