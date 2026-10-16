# Codex existing-source acceptance review — 2026-10-16

Result: PARTIAL. Scope: Codex HTTP acceptance controller, its regression tests,
English/Chinese usage and design, plus these engineering records. Runtime commands,
Dockerfile, catalog, provider evidence and tested_on are unchanged. Parent source:
`a361f490555ead0ff67081ffb4874abf292a1b2f`.

## Executed checks

- PASS: `python -m unittest discover -s codex -p test_commands.py -q`:
  11 tests, including actual direct-exec positive control and twelve invalid baseline/agent
  artifact cases. These controls use synthetic model responses, not a cloud model.
- PASS: `python3 scripts/check_template.py codex --strict`.
- FAIL (environment): invoking the local runner with an unsupported `--help`
  argument started all 18 suites with system python3. They failed to import the
  in-sandbox server (plus httpx for one template); this is not a runtime pass.
  The runner uses PATH's python3, not the controller's interpreter. The corrected
  PATH-based rerun is recorded separately below when complete.

- PARTIAL: corrected `PATH=<paired venv>/bin:$PATH python scripts/run_local_e2e.py`:
  12 PASS / 6 FAIL across 18 suites. Codex PASS with its paid model task SKIP.
  Existing agents-cli, browser-automation, droid, opencode, qoder and qwen-code
  suites require their actual installed CLIs/browser, unavailable in this local
  controller environment. No fake CLI, model result or passing baseline is used.
- PASS: paired-venv `python scripts/check_template.py codex --strict`:
  conformant. A system-python invocation initially lacked PyYAML; the actual
  successful command used the pinned review environment.
- PASS: paired-venv `python scripts/test_spec_tools.py`: 22 tests with existing
  subtests, 8.559 seconds. `git diff --check` passes.

## Independent unchanged-image model evidence

The frozen parent image from successful image run 38853293050 was pushed and
registered through the official generation-2 API. Its original HTTP real-model
suite passed 16 checks without skips using the authorized compatible model.
A separate external verifier then seeded a broken existing calculator with
original tests, observed the failing baseline, required actual Codex command
execution, verified changed source, unchanged original tests, a nonempty report,
exact artifact, the original test rerun and six held-out cases. All passed; its
owned project was removed, and the target sandbox was killed and template deleted.
Registry cleanup is deferred to the same owned batch; do not claim final cleanup
until independently read back. This external verifier is supplemental and is NOT
an executed model result for this PR's updated public Fibonacci controller.

## Outstanding gates

The initial public controller at `24a029e` passed 17 actual model checks, and its independently owned target sandbox/template were confirmed absent. A later peer review reproduced a false positive from `sys.exit(0)` before assertions, with fake unittest output. That initial run remains historical evidence and does not establish acceptance for the hardened controller. The hardened current public controller has not yet executed against a real model. Actual
image/cloud deployment through the canonical runner, normal remote CI, parent
landing and complete owned batch cleanup remain separate gates. This patch stays
draft and makes no official/tested-provider claim. Refs
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/16.
