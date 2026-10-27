# SWE default protocol correction

Result: PARTIAL

Date: 2026-10-27. Manifest1.1.2 real Express launch with published CLI0.5.7 and
client/server0.4.0a6 failed required-model acceptance after5 passes/1 failure:
setup.native_tool_calls=false. Sandbox and prepared image/template independently
absent, no uncertainty. Original source/receipt will be retained with the rerun.

SWE1.2.0 changes only default protocol, docs, and regression linkage; package pins,
image recipe and method signatures stay unchanged. Legacy text is explicit.

- python -m pytest -q swe/test_e2e_protocol.py swe/test_commands.py: PASS,36 tests.
- New manifest-driven flow regression fails with old text default and passes with
  toolcall; actual old-default check returned pytest exit1 as expected.
- python scripts/check_template.py swe: PASS, conformant.
- python scripts/check_docs.py: PASS,224 documents, zero failures.
- [Changed source native core](2026-10-27-swe-default-tool-protocol/native-repair-pass.json):
  PASS,14 assertions/zero fail/skip/not-run. Actual default Docker source991856c77809bbad0217cc0cadc66417e322254c,
  genuine mini CLI with qwen3.8-flash, exact1FAIL59PASS original baseline, changed
  supported Flask source, fresh60 exact original test identities passed, patch and
  report retrieved. Inputs unchanged; provider and prepared artifacts independently absent.
- [Literal documented alternatives](2026-10-27-swe-default-tool-protocol/all-documented-interfaces.json):
  PASS,7 grouped checks. Three actual separate CLI/unchanged complete SDK/HTTP repair
  flows used qwen3.8-max, exported actual reports and patches and each passed all60
  original identities in a fresh evaluator. Each owned run directory independently
  absent before the next alternative; outer sandbox/image/template independently absent.
  All seven named methods exercised, including actual swe_report through CLI/HTTP.
- [Original default failure](2026-10-27-swe-default-tool-protocol/original-default-failure.json)
  retained. [Operator mismatch](2026-10-27-swe-default-tool-protocol/operator-verifier-mismatch.json)
  also retained: a launch of the new source was compared against the old local manifest;
  the identity guard correctly refused before command use. This was not a failed model
  run of the fixed recipe. Repeating with the exact matching verifier produced the pass.
- Actual [CLI report](2026-10-27-swe-default-tool-protocol/cli-report.json) and
  [source patch](2026-10-27-swe-default-tool-protocol/cli-repair.patch) retained.
  Python evaluation3.11.10; official_benchmark_score=false in every report. These
  portability-slice results are not an official SWE-bench score.
- Current-head CI, practical article and Registry review pending.

After the actual runs, two leftover prose sentences were corrected to agree with
the shipped toolcall default. All executable README blocks in both languages are
byte-identical to executed revision991856c; runtime/manifest/Docker/controller files
are unchanged. [Documentation-only review](2026-10-27-swe-default-tool-protocol/documentation-only-review.json)
records both full document digests and identical code-block digests. This is local
prose review, not a claim that a changed runtime was deployed.
