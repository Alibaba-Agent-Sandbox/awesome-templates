# Native controller entry verification — 2026-10-19

Scope: five changed Python files listed in this PR, based on templates `e664f7c63501ca8bc970cccefbc2d061db089baf`; Python 3.11.15, current source-installed SDK from https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47 .

- PASS: regression demonstrated failure before entry migration; corrected `python -m unittest discover -s scripts -p test_express_cleanup.py` runs 14 tests, including synchronous-root rejection, native named-command arguments and local close.
- PASS: `python -m pytest agents-cli/test_sdk_verifier.py agents-cli/test_protocol.py -q`: 41 passed.
- PASS: `python scripts/test_spec_tools.py`: 36 passed.
- PASS: `python scripts/check_template.py --all --strict`: 23 products plus skeleton conformant, zero failures.
- Not acceptance: initial unittest discovery for pytest-style agents-cli files collected zero tests; the actual pytest run above replaces it.

- BLOCKED: an optional real `python-hello` named-command probe received HTTP 502, including on the creator client, after successful server health. This is not counted as native cloud acceptance or a passing template revision. Owned sandbox deletion and independent inventory checks succeeded for completed probes. Two initial probe setup mistakes used `.sandbox_id` rather than native `.id`; those short-lived owned instances expired and final inventory is checked separately.
- FAIL (environment): initial local acceptance child processes selected system Python rather than the SDK virtualenv. Rerun with the virtualenv on PATH is separate; upstream CLI/image dependencies are not all installed locally.

No optional probe results are used to promote acceptance. Core real pause/snapshot results belong to the SDK/CLI records, not this import regression. No runtime images, catalog status or provider badges change. Existing template cloud/model evidence is not promoted by import changes.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/116 . Hosted checks must pass for the final head before merge.

## Final local scope

- PASS: `python -m pytest -q scripts/test_express_cleanup.py scripts/test_express_runtime_socket.py agents-cli/test_sdk_verifier.py agents-cli/test_protocol.py`: 58 passed, 18 subtests passed.
- PASS: compileall for all four executable/example source files.
- PARTIAL: `PATH=<venv>/bin:$PATH E2E_RUN_LLM=0 python scripts/run_local_e2e.py`: 17 passed, 7 failed (agents-cli, browser-automation, droid, ocr, opencode, qoder, qwen-code); local upstream CLI/browser/engine prerequisites are incomplete. Full hosted offline matrix remains required; no local full-suite pass claimed.
- PASS: independent final cloud inventory after all optional probes: owned fixture GET 404; conditional-owned sandboxes 0, controller-tagged sandboxes 0, snapshots 0. Initial unjournaled probe sandboxes had bounded 300-second TTL and are independently absent.
- No cloud/model Actions dispatched. No production template rebuild or provider badge promotion is justified by these host-entry checks.
