# Verification: canonical template runtime helpers

- Date: 2026-10-26
- Result: PASS for source-maintenance scope; remote CI/review pending
- Change: canonical helper sources, synchronization script, generated-source markers and CI check.
- Runtime: Python 3.13, source server/client 0.4.0a6; no real credentials supplied.

## Commands run

- `python scripts/sync_process_runners.py` — PASS: 15 placements; initial synchronization required identical executable ASTs.
- `python scripts/sync_process_runners.py --check` — PASS.
- A combined pytest invocation — collection failed because independent templates share the test_commands.py module name; rerun as separate processes.
- Individual affected template regressions — PASS: Qwen 11; Kimi 10; Aider 39; DeepSeek 22; Hermes 15; Pi 25; Qoder 15; OpenClaw 31; Amp 13; Gemini 12 with 1 conditional skip; QM 14; QM-Sandbox 26.
- apply-patch: 8 passed, 2 failed because the pinned executable is unavailable.
- code-server: 9 passed, 2 failed because the installed 4.127.0 differs from required 4.141.0.
- Goose: 6 passed, 3 failed because the pinned executable is unavailable.

## Final checks after installing the exact CI-pinned tools

- `npm ci --prefix apply-patch --omit=dev --ignore-scripts` plus the existing install_alias.py — PASS; apply-patch tests: 10 passed.
- Existing code-server/install_runtime.py — PASS, verified 4.141.0; code-server tests: 11 passed.
- Existing goose/install_runtime.py — PASS, official 1.54.0 fixed asset/SHA256; Goose tests: 9 passed.
- Complete commands.py AST comparison against the base commit — PASS for all 15 files, beyond just the synchronized functions.
- `python scripts/check_template.py --all` — PASS, no non-conformant templates.
- `python scripts/check_docs.py` — PASS: 222 documents, 0 link failures.
- `pytest scripts/test_check_docs.py -q` — PASS, 4 tests.
- Existing run_local_e2e._run_one over all 15 affected templates, with isolated pinned-tool paths — PASS: 15 actual local HTTP/server processes. Model-dependent and original external QM SDK environment scenarios report explicit SKIP; those tiers are not claimed.

## Integration with current main

Merged c6b59325cfa7c0f4b7f425c3489ebef5e2889740 (consumer setup guide update), preserving both CHANGELOG entries. Source helpers remain identical; spec/catalog validation and all 39 specification-tool regressions pass. An intermediate docs check traversed freshly installed untracked node_modules and reported 8 upstream-package links; generated install files were removed and the clean repository check was rerun. Latest-head PR checks are evaluated separately.

## Cleanup

Process tests stop their owned descendants. No cloud build, deployment or model request was performed.

## Not verified

Affected installed-tool regressions and local HTTP checks passed after prerequisites were installed. Fresh cloud images, Express/OpenSandbox source matrices and real models were not rerun: executable ASTs, recipes, manifests, dependencies and versions are unchanged. The migration changes source maintenance only; it does not extend any prior provider or model receipt.
