# Public OpenSandbox developer rerun

Date: 2026-10-25
Result: PARTIAL

Scope: current 46 source catalog entries and four provider-owned native identities. This is a new run; historical receipts remain unchanged.

Fresh PyPI client/server 0.4.0a1 installed with no cache from the official index; pip check passed. Initial runner unit invocation lacked httpx before package installation; this prerequisite failure remains recorded. No cloud pass is inferred from local tests.

Local checks passed: focused runner 23 tests; `check_template.py --all` (47 source directories including skeleton); `test_spec_tools.py` (58 tests). These are local contract checks, not cloud proof.

Pending: real published CLI/provider installs and 46-entry Docker-backed matrix, native OpenSandbox case, foreign identity rejection, receipts and UX assessment.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/215
