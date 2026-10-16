# Pi official CLI source and model verification

Date: 2026-10-16
Result: PARTIAL

## Scope and environment

Isolated branch `feat/pi-runtime-20261016`, based on 7cb0d9430768eec22f500ebb80b3fe9517ab1cbc. Scoped files: `pi/`, `docs/design/pi.md`, catalog, local/image CI and the separate image-selection scripts/tests. Existing PR 82 was not edited or triggered. References [Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41).

Official npm registry metadata confirmed package version 1.3.0, Node >=22.19.0 and `pi` binary. The exact package installed successfully with `--ignore-scripts` from the official registry under an isolated prefix; actual `pi --version` returned 1.3.0 and `--help` exposed all wrapper flags. Node was the existing verified official 24.16.0 installation; no duplicate Node/browser/runtime download was performed. Python uses the existing shared SDK/httpx/PyYAML/pytest environment.

Tagged upstream CLI/model docs and installed 1.3.0 source were inspected: `--no-approve` sets project trust false, while selected `--tools` determines available built-ins. `models.json` supports `openai-completions` and `$ENV` interpolation. Official references are in the design document.

## Executed checks

- `python scripts/check_template.py pi`: PASS.
- `python scripts/check_template.py --all --strict`: PASS, 18 conformant directories including skeleton and 17 products.
- `python scripts/test_spec_tools.py`: PASS, 22 tests, including real workflow preparation of every template context with byte-preserved Docker heredocs/SDK RUN and copied opaque wheel fixture. No Docker is invoked by that regression.
- `python -m pytest -q pi/test_commands.py pi/test_e2e_protocol.py pi/test_cli_protocol.py scripts/test_select_image_templates.py`: PASS, 68 distinct cases across Pi and selection after the final conservative-input correction. The Pi suites passed 45 distinct cases: 25 command/process/privacy/cancellation, 18 independent-verifier cases and 2 actual CLI/local SSE protocol cases. Protocol fixtures are not models.
- Targeted `run_local_e2e._run_one(pi, ...)` with shared venv/actual CLI: PASS, 9 HTTP checks, real pin 1.3.0, missing-key guard, explicit model SKIP.
- Real source-runtime `e2e_test.py` with required CLI/model, an authenticated local server, compatible endpoint and `qwen3.8-flash`: PASS, 17 checks, exit 0. The target reported configuration presence; controller did not infer it from its own environment. Baseline original source failed 3 unittest cases. Official Pi modified source and created report/exact artifact, original tests remained intact, independent isolated target unittest and direct-file held-out inputs passed. Owned project deletion and server teardown passed. This is source/model evidence, not image/cloud acceptance.

## Failed setup attempts and corrections

Two initial real-model setup attempts stopped before model invocation: target file upload/delete returned HTTP 403 because the local server's default allowed file root excluded the disposable project. Adding the existing local runner's `ABX_SERVER_BASE_DIR` fixed the precondition. Server bearer auth is separately supplied through `E2E_SERVER_TOKEN`; gateway auth uses `E2E_TOKEN`. These attempts do not count as model passes.

A system-Python `run_local_e2e.py --help` invocation unexpectedly ran the suite because that script has no argument parser; it failed on absent SDK/dependencies. This was an invocation/environment error. The targeted shared-venv run above passed. No global product pass is inferred from that failure or targeted rerun.

## Remaining gates and cleanup

Pi actual Docker image L1: NOT RUN locally; no Docker daemon. Pi changed-image Express L2 and image-backed model L3: NOT RUN. Catalog remains experimental, `tested_on: []`, with no provider evidence file. RPC/TUI are outside this wrapper. The npm transitive tree is not lockfile-frozen.

Temporary per-call model config and model coding project were removed. Test HTTP servers/process groups were stopped; real descendant-marker regressions cover success, nonzero, timeout and Python cancellation. Deliberate setsid escape is outside this Linux group boundary. Credentials were read only in memory, passed through process environment, never printed or committed.

Independent peer review of the final runtime/verifier/selector/workflow found no blocking issue. The reviewer confirmed owned cleanup, independent target verification, cumulative PR selection and archive provenance boundaries. Output remains buffered in memory without a byte cap; the execution deadline is enforced and this limit is documented.


Publication follow-up: draft [PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86) is stacked on PR 82. A scoped follow-up updates the current backlog Pi section and requests automatic Pi archive export so authorized image-backed L2 can use the actual runner image without depending on not-yet-verified workflow_dispatch availability. Pi image/cloud results remain pending.
