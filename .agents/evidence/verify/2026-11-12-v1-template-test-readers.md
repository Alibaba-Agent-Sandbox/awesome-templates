# Verification: existing template protocol regressions read v1 resources

Date: 2026-11-12. Before revision:6f7aee8844a54e37ae251cf4020d77b8ce03a63b.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

FAIL preserved: actual latest-head Actions local-e2e job
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43290753694/job/131436058740
first fails at swe/test_e2e_protocol.py:55, KeyError env, after35 passes in that workflow group.
Local before control on the two protocol files reproduces4 failures/19 passes: the SWE root-env
read and three agents-cli canonical-startup cases reading root start_cmd. A scan of all template
owned test/e2e files finds these two template.yaml readers; unrelated subprocess env mappings
and independently owned YAML policies remain unchanged.

PASS: only those resource reads/imports move to shared load_source_document and current paths.
SWE still enforces max_steps30/command_timeout600 and finally cleanup. Agents-cli still tests
both actual HTTP startup forms, authentication, closed endpoint allowlist, repeated adapters,
missing-real-CLI diagnostics and explicit fixture isolation. No assertion is removed or skipped;
commands.py, e2e_test.py, images, SDK pins and workflow invocation are unchanged.

PASS in a fresh Python3.13.13 venv installed from public PyPI with CI's exact published
agent-sandbox-client0.4.0a7/server0.4.0a7, httpx0.28.1, pytest9.1.1 and requirements-spec:

- The same two protocol files:23 pass, zero skips,1.38s.
- Both full related workflow groups (SWE commands/protocol and agents-cli model setup/protocol/
  SDK verifier):89 pass, zero skips,9.63s.
- pip check, scoped Ruff --select F,238-document local link check and git diff --check pass.

Both distributions have no direct_url/editable metadata; this does not rely on the candidate
SDK checkout. A small [typed before/after receipt](2026-11-12-v1-template-test-readers.json)
retains actual job identity, original log hashes and exact dependency versions without raw
logs, credentials or workstation paths. No new image, model or cloud resource was used.

Commands: `E2E_RUN_LLM=0 python -m pytest -q swe/test_e2e_protocol.py agents-cli/test_protocol.py`
and `E2E_RUN_LLM=0 python -m pytest -q swe/test_commands.py swe/test_e2e_protocol.py
agents-cli/test_model_setup.py agents-cli/test_protocol.py agents-cli/test_sdk_verifier.py`.
The unchanged full latest-head remote local-e2e remains the acceptance gate for subsequent
template tests; this record does not claim that job is green before it actually completes.
