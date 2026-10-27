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
- Actual changed-source default Docker/model/evaluator and current-head CI pending.
