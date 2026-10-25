# Published server runtime verification

Date: 2026-10-25
Result: PARTIAL
Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221
Scope: pending branch based on ecaacebd1582c033049ff9f32038e0249f80f82a, all 46 source recipes and skeleton plus current acceptance tooling.

The official PyPI client/server 0.4.0a2 distributions were installed into an isolated Python environment using the public index; metadata reads back 0.4.0a2 for both. The owner independently confirmed wheel/sdist availability and official publish workflow 40198182884 attempt 2 SUCCESS. Attempt 1's propagation-check failure remains historical.

PASS: focused CI-image/archive/prepare/asset/batch/authorization/cleanup/SDK/preview/steps/public-launch regressions: 212 tests and 30 subtests. An initial command named nonexistent test_gateway_headers.py and collected zero tests; corrected invocation above is the executed suite. After moving the retired runner's bounded controller diagnostic sanitizer into public_launch_e2e, the complete public-launch regression file passed again: 25 tests.

PASS: `python scripts/test_spec_tools.py`: 57 tests. This includes executing actual image workflow context preparation for all 46 source directories, proving unchanged Dockerfile bytes except supported base resolution, no injected wheel and the exact declared published package.

PASS: `python scripts/check_template.py --all`: all 47 conformant. `python scripts/check_docs.py`: 222 documents, zero link failures. Initial default Python YAML inspection lacked PyYAML; workflow inspection uses the isolated environment with declared checker dependencies.

The earlier complete public OpenSandbox matrix remains 45 PASS / 1 Chrome FAIL at its own old inputs, with 610 passing assertions, 1 failure and 18 explicit skips. Chrome's narrow fix merged in PR218 and its separate fresh public-source run 40197940825 passed 30 assertions with independent cleanup. The new receipt is copied unchanged to chrome/evidence/public-opensandbox-prefix-2026-10-25.json. Neither run establishes acceptance of these new server pins.

NOT RUN: local Docker image builds (Docker unavailable), new candidate cloud matrix, new public-source post-merge matrix, and current-head remote CI. No new cloud resources or GitHub secrets were created by these local checks. Existing historical receipts were not rewritten. Final merge remains gated on applicable CI/review and real runtime evidence.
