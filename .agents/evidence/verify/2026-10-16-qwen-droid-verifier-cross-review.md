# Qwen / Droid verifier cross-review — 2026-10-16

Result: PARTIAL

Scope: Qwen target-key authority correction in `qwen-code/e2e_test.py` and `qwen-code/test_e2e_protocol.py`; independent review of Droid runtime, Dockerfile, template metadata, bilingual documentation, design, acceptance and regression files; scoped Droid disabled-model correction in `droid/e2e_test.py` and `droid/test_e2e_protocol.py`. Tested current uncommitted scoped files. Other contributors' changes, including Droid deadline type/float validation, are preserved.

## Findings and changes

- Qwen previously decided whether a remote target could call a model from the controller's `OPENAI_API_KEY` / `DASHSCOPE_API_KEY`. Corrected the verifier to use the actual target `qwen_setup_check` `api_key_set is True` value. Controller credentials neither authorize a keyless target nor block a keyed target. The controller does not need the target model key.
- Qwen's explicit disabled-model mode returns before any diagnostic or agent HTTP request from `coding()`. Required-model plus disabled-model is a failure. Regression cases cover both controller/target key mismatches, no-request disabled mode and successful target-keyed/controller-keyless coding.
- Droid's missing-key probe preceded its disabled-model check. Reordered `check_model_call()` so disabled mode sends no execution requests for keyed or keyless targets; required-model plus disabled-model fails. Required, enabled acceptance on a keyless target retains the guard assertion and fails L3.
- Droid independent review found parameter range/type guards, literal argv, root/symlink cwd enforcement, key-before-spawn behavior, secret redaction and process-group cleanup consistent with the documented contracts. The remote coding verifier seeds a genuine failure, retrieves source and new artifacts, preserves original tests and independently executes fixed/held-out tests. Factory-key absence and Docker absence remain explicit blockers; mocked protocol results are not Factory acceptance.

## Executed

- PASS: `python -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py qwen-code/test_commands.py qwen-code/test_e2e_protocol.py --import-mode=importlib` — exit 0; 38 passed (Droid 21, Qwen 17). The Droid source/runtime fixes from its owner are included in that test scope.
- PASS: `python scripts/check_template.py droid` and `python scripts/check_template.py qwen-code` — both exit 0, conformant.
- PASS: Qwen real local model acceptance rerun with Qwen Code 0.23.0 and `qwen3.8-flash`; the server receives the authorized compatible endpoint/key, while the separate HTTP verifier explicitly has both `OPENAI_API_KEY` and `DASHSCOPE_API_KEY` removed. Required CLI/model flags are enabled. Exit 0, 17 passed checks and 0 failed: real pin, failing seeded baseline, real headless coding, source change, original tests preserved, new report/exact artifact retrieved, independent three-test rerun and held-out calculations, and owned-project cleanup.
- PASS: scoped `git diff --check` — exit 0.

## Limits and cleanup

This run proves local real-model Qwen behavior and independent review/regressions; it is not an image build or a cloud/provider pass. Docker-dependent L1/L2 and genuine Factory L3 remain blocked as recorded in [Qwen verification](2026-10-16-qwen-code-v2.md) and [Droid verification](2026-10-16-droid-headless-runtime.md). The integrating agent owns subsequent real Express source-runtime checks and their separate evidence. No cloud resources were created here. The local Qwen server was stopped, its unique target project was removed and its temporary HOME/workspace cleaned. Credentials and raw model/CLI output are excluded from records.
