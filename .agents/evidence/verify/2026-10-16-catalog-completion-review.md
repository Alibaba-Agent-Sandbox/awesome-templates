# Verification: Existing catalog completion review

- Date: 2026-10-16
- Result: PARTIAL — implementation/local checks pass; required image, deployment,
  product/model and remote delivery gates are tracked separately.
- Scope: the 16 existing product directories, bilingual docs/designs, catalog,
  acceptance tooling/CI and the linked scoped records.
- Environment: Linux, Python 3.13.13; pinned real CLI installations; isolated
  Python test environment and Chromium 145.0.7632.6 / Playwright 1.58.0.
- [Decision](../../notes/proposed/feature/2026-10-16-catalog-completion-review.md).
- [PR 82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82).

## Local checks actually executed

- `python scripts/check_template.py --all --strict`: exit 0, all 16 products plus
  `_skeleton` conformant; zero legacy/nonconformant entries.
- `python scripts/run_local_e2e.py`: exit 0, 17 passed, 0 failed. The model flags
  are disabled; optional/model skips are not L3 acceptance.
- Per-template `python -m pytest -q` suites: 323 distinct tests pass. Independent
  subprocess runs isolated same-named modules; the last three-template combined
  rerun used `--import-mode=importlib` and passed 106 tests after its final edits.
- An initial diagnostic driver incorrectly used importlib mode for the legacy
  Python-hello import pattern and failed collection. Rerunning its actual CI
  command passed all 4 tests; this was not silently relabeled as a source failure.
- `python scripts/test_spec_tools.py`: exit 0, 21 tests, including catalog
  capability disagreement/invalid shape rejection and order-independent equality.
- `python scripts/test_express_runtime_socket.py`: exit 0, 3 tests.
- Record/link, diff and configured-secret scans are required before commit.

| Template | Distinct passing regression tests |
|---|---:|
| agents-cli | 10 |
| amp | 27 |
| claude-code | 10 (plus 9 unittest subtests) |
| codex | 10 (plus 15 unittest subtests) |
| codex-agent-api | 25 |
| deepseek-harness | 43 |
| droid | 31 |
| gemini | 28 |
| hermes-agent | 30 |
| openclaw | 22 |
| opencode | 24 |
| python-hello | 4 |
| qoder | 33 |
| qwen-code | 26 |

Browser and Node web behavior is exercised by their actual HTTP suites rather
than additional redundant unit wrappers. Coding verifier regressions run real
independent Python processes and reject marker-only output, test replacement,
held-out failures and writable startup/stdlib shadows.

## Reproduced process failure and fix

Normal/nonzero leaders could exit after starting redirected background descendants;
the wrappers returned without stopping those processes. The new Qwen regressions
failed twice on the previous runner. Independent review reproduced the same
failure in Amp, Droid and Gemini. The corrected runners use Linux `waitid(WNOWAIT)`
to retain the PID/group identity, drain both pipes and stop the group before
reaping. Timeout tests also cover descendants ignoring TERM. OpenClaw's short
health probe was brought under the same lifecycle without changing its separately
owned persistent gateway. Qoder/Hermes/DeepSeek have equivalent regressions.

Hermes's separately detached upstream authority/managed workers are beyond that
CLI process group. Its README explicitly states that a CLI timeout does not
prove accepted gateway work was cancelled; sandbox destruction is the documented
way to stop the whole isolated environment. Owned local validation homes/workers
were cleaned without stopping other gateways.

## Real Express source-runtime checks

- Current Qwen owned-process source: 17 HTTP checks pass with real model required;
  existing source repair, original test bytes, new downloaded artifacts,
  independent unittest and held-out calculations all verified.
- Current Droid owned-process source: 9 external HTTP checks pass, pinned CLI and
  read-only configuration inspected; no Factory model call was claimed.
- Both runs reported owned sandbox cleanup PASS. Reports preserve exact hashes in
  `qwen-code/evidence/runtime-express-2026-10-16-owned-processes.json` and the
  matching Droid path; neither is template-image provider acceptance.
- The pure-Python server wheel SHA256 is
  `a09a4846fef8b49f3a059d1c65e38d283986aa4fbf879dd09192100c30039fc9`.
  All 56 Python modules match tracked SDK revision
  `fbe506349693f9bb26c1755aa3d13ce855e1ab69` byte-for-byte.
- Earlier same-day source reports remain with their original hashes. A Qwen
  attempt failed when temporary disk space was exhausted; owned cleanup passed.
  Only task-created abandoned dependency/cache directories were removed, then
  a new output directory recorded the successful rerun.
- Browser retry installed actual pinned Chromium, then failed to launch because
  plain Express base lacks `libglib-2.0.so.0`. Owned cleanup passed. The Dockerfile
  dependency layer was not executed by that diagnostic; no browser cloud pass
  was recorded.

## Other real-component results

Scoped records retain actual OpenCode clean-wheel Express coding/resume, local
OpenClaw authenticated gateway lifecycle (11 checks), actual Qoder/Hermes versions,
and latest successful local-target compatible-model coding for DeepSeek and
Hermes. Earlier failed model attempts remain distinguished from later successful
runs. None of these is silently promoted to native-model/provider acceptance.

## Remaining gates

Actual Docker L1 CI results, changed-image Express deployment L2, missing model
credentials, other sandbox-provider environments, required latest remote CI/review,
release and remaining candidate/Skills/provider roadmap work remain open. The
new image workflow is an executable gate, not evidence of its own success.
The CLI SDK-wheel rewriting defect is owned by a separate CLI fix; image builds
from prepared contexts do not prove `abx template deploy` works.
No template acceptance Issue is closed and no provider metadata is promoted.
