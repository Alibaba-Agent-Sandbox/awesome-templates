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
- [Actual fixed-source run](2026-10-27-codex-target-model/fixed-target-model-pass.json):
  PASS,18 checks, zero fail/skip/not-run. Public source22168cd80bfe143960e439ab59778301eb580f70,
  actual default Docker/Express, actual native Codex source repair, original tests
  preserved and independent original/held-out assertions passed. qwen3.8-flash was
  configured only on the target. Controller and adapter inputs unchanged.
- Own sandbox, prepared template and local/registry images independently absent;
  zero cleanup uncertainty or retained artifacts.
- check_docs.py: PASS,224 documents/zero failures; diff check PASS. Current-head CI,
  literal newcomer alternatives and complete provider qualification remain pending.
