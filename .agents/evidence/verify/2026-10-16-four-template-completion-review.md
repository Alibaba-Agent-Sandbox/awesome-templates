# Independent completion review: Amp, Droid, Gemini and OpenClaw

Date: 2026-10-16
Result: PARTIAL

## Scope and environment

Reviewed the existing uncommitted changes under `amp/`, `droid/`, `gemini/`,
`openclaw/`, their design/usage documents and existing engineering records.
Base HEAD: `2acb53481739e9585803076dd4c05ce5c2048219`.
New follow-up changes are limited to Amp coding verification and bilingual
instructions, Droid held-out verification, their protocol regressions, and these
owner records. Shared catalog, workflow and runner integration belongs to the
coordinating task and was not edited here.

Linux x86_64; Python 3.13.13; clean temporary virtual environment with locally built
agent-sandbox-server 0.3.0, pytest 9.1.1, httpx 0.28.1 and pyyaml 6.0.3.
Node 22.22.2 ran the actual pinned Amp/Droid/Gemini CLIs. OpenClaw used official
Node 24.16.0 x64 archive, whose SHA256 was verified against the Dockerfile pin.
Temporary prefixes and synthetic tokens were used; no model credentials were
forwarded into the local HTTP targets. Commands below normalize only temporary
installation paths as `<venv>`, `<npm10>`, `<cli-prefix>` and `<node24>`.

## Review findings and fixes

- Amp still accepted a response marker as real-model success. Its opt-in verifier
  now creates a unique remote project, proves seeded source fails three tests,
  explicitly enables editing for that task, downloads changed source and new
  report/acceptance artifacts, checks original tests were preserved, and reruns
  isolated original and held-out assertions through the target shell API.
  Cleanup only deletes the unique project created by the verifier.
- Droid's held-out stage imported through the project path. It now loads the
  exact source file by absolute path under isolated Python and covers all
  original cases as well as additional cases.
- Both receive six real subprocess regressions combining correct/incorrect code
  with `unittest.py`, `sitecustomize.py`, or no shadow. Actual emitted verifier
  commands execute; only HTTP transport/model edits are simulated. Incorrect
  source cannot pass, correct source passes, and startup hooks never execute.
- Amp also receives five protocol scenarios proving marker-only results,
  changed tests, failed original tests and failed held-out checks cannot pass.
- OpenClaw review retained the existing ownership safeguards: unreaped leader
  anchors group identity, waitid does not reap status observations, shutdown
  kills the owned group before reaping, and authenticated RPC defines health.

## Executed validation

- PASS: isolated npm 10.9.4 exact-version install of
  `@ampcode/cli@0.0.1792022479-ge66e24 @factory/cli@0.241.1 @google/gemini-cli@0.64.0`;
  actual `amp version`, `droid --version`, `gemini --version` all exit 0 and match
  their pins. Node24 npm installed `openclaw@2026.10.4` (exit 0).
- PASS: `python scripts/check_template.py amp`, `droid`, `gemini`, `openclaw`
  (each separate invocation, each exit 0 / conformant).
- PASS: `python -m pytest --import-mode=importlib -q amp/test_commands.py amp/test_e2e_protocol.py droid/test_commands.py droid/test_e2e_protocol.py gemini/test_commands.py gemini/test_e2e_protocol.py openclaw/test_commands.py`
  with the real pinned Gemini binary on PATH: 89 passed, exit 0.
- PASS: final protocol-only rerun,
  `python -m pytest --import-mode=importlib -q amp/test_e2e_protocol.py droid/test_e2e_protocol.py`:
  26 passed, exit 0.
- PASS: existing `scripts/run_local_e2e.py::_run_one` invoked for each of the four
  directories with its ordinary credential-sanitized child environment and real
  pinned CLIs on PATH. Amp 7 PASS/1 model SKIP; Droid 9 PASS/L3 NOT RUN;
  Gemini 9 PASS/model SKIP; OpenClaw 6 PASS/real-gateway and model SKIP.
  All four target runner results were `pass` and driver exited 0.
- PASS of a negative guard, not L3: repeated actual HTTP target startup for
  Amp/Droid/Gemini, changing only `E2E_REQUIRE_LLM=1 E2E_RUN_LLM=1` in the sanitized
  child environment. Each actual e2e_test.py exited 1 for missing target product
  key. The driver asserted all three expected failures and exited 0. No model
  request or coding project was created in these negative runs.
- PASS: separate actual OpenClaw HTTP target used unique localhost ports and
  independent randomly generated server/gateway tokens. Actual e2e_test.py:
  exit 0, 11 PASS, model/coding explicitly SKIP. Authenticated readiness, RPC
  health, continued process after start response, owned stop, failed health after
  stop, and server shell all passed. The driver terminated/reaped its HTTP server.
- PASS: scoped `git diff --check` and relative document-link validation, exit 0.

## Failed attempts retained as limitations

The restored historical npm10 artifact was incomplete (`package.json` absent),
and system npm12 install failed with `Class extends value undefined`. A fresh
exact npm10 tarball was extracted to a temporary prefix and installed the pins
successfully. A first combined pytest command without `--import-mode=importlib`
failed collection because templates use the same test filenames. The corrected
command avoids module-name collisions; neither failure is represented as a pass.
An initial regression run skipped the optional real-Gemini diagnostic before CLI
installation; the later combined run includes that actual diagnostic.

The integration owner independently reviewed the final Amp/Droid verifiers and
confirmed the baseline, isolated imports, artifacts, preserved tests and direct-file
held-out checks. Copy/paste-only protocol fixture route/key remnants were removed.

## Remaining required gates

- L1 BLOCKED: Docker executable is unavailable; host CLI installation is not an
  image build or a non-root container verification.
- L2 BLOCKED by image/engine prerequisite; no current-source image/template
  deployment was created by this follow-up. Historical source-runtime/provider
  evidence remains unchanged and does not prove the current image.
- L3 NOT PASSED: no compatible product key was injected into these targets.
  Real Amp/Droid/Gemini coding remains unverified. OpenClaw lifecycle success
  establishes gateway functionality only; this command set does not run a model.
- L4 NOT RUN. Full-repository/shared-CI/catalog integration, owner Issues/PRs,
  required remote review/checks and verified merge remain integration work.
  Nothing in this record claims the overall project is complete or merged.

## Final verifier hashes

| File | SHA256 |
|---|---|
| `amp/e2e_test.py` | `99e02740374cbac666e7fcc0691d66e1ecc56fb3483de3f169953cf5f6efe845` |
| `amp/test_e2e_protocol.py` | `7745ad12f2217f10ec9ba402e89ba55824ec32bb58eda370a40fcc3ada0222b0` |
| `droid/e2e_test.py` | `1cf103b08e663b8c43fe42e82fbf30529a581b4854ef2332a1dd5f6337dec4e4` |
| `droid/test_e2e_protocol.py` | `85c041881b6d8aab52e723c88b2c6be540c3a3862a06f6a90808d2f5f11c9237` |

No provider pass file or tested_on provider was added. Local HTTP servers were
stopped, owned gateways/projects were cleaned, and no cloud resource was created.
Temporary dependency prefixes remain outside the repository for integration.
