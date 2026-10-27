# Codex target-only model prerequisite

Result: PARTIAL

Date: 2026-10-27. [Original failed public run](2026-10-27-codex-target-model/original-host-check-failure.json):
14 passes,1 failure,1 skip; target received its declared model configuration,
controller correctly received no model credential. Own sandbox/prepared image and
template independently absent. No model task was accepted from this attempt.

- python -m pytest -q codex/test_commands.py: PASS,12 tests plus27 subtests.
- Two target-configuration regressions explicitly rerun against the original
  controller: expected pytest failure. Fixed controller passes both.
- Existing remote-source tamper, original/held-out tests remain active.
- No runtime/version/API change; model credential values stay target-owned.
- Actual fixed-source default Docker/model run, docs checks and CI pending.
