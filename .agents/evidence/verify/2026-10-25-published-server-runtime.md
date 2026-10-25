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

## First candidate CI failures and correction

Candidate ecead480736b2791f220d4c3f42fa8a128bacd1a L1 run 40202240809 failed on the base image's configured Alibaba PyPI mirror: its actual version list stopped at 0.4.0a1, so exact a2 installation failed for amp/codex/copilot-cli/crush. Official PyPI already has the package. Current Dockerfiles now explicitly select https://pypi.org/simple for this dependency, without a fallback or an older pin. This is a recipe change, so prior image successes do not qualify the correction.

The same candidate e2e run 40202240853 failed two external-provider boundary tests because it checked out obsolete provider manifests and called retired interpreter execute. Update the fixture checkout to published provider 48f09103380657ad7e5ea97422e50156cb01e1dc, import the public ProviderSandbox, and use current operations/run_code. Actual a2 rerun: both missing-provider-key-before-engine and unsupported-interpreter-before-transport tests PASS (2). Required boundary assertions remain.

## Prepared-image final digest gate

The adapted prepared-image consumer now reads the actual guest server package and requires it to equal the Dockerfile pin. Its final result additionally requires the after-runtime registry digest check to have completed. Previously an application PASS plus cleanup could set the final result PASS after the caught digest assertion; publication then rejected missing proof. Two real control-flow regressions now simulate unchanged/changed digests through the current consumer: changed digest returns FAIL, preserves successful application/cleanup scope and publishes no pass; unchanged digest passes. The combined archive/public-launch suite passes 47 tests.

## Explicit portable profile audit correction

Provider T4's real second (portable) run failed the guest a2 assertion. The initial directory-only audit missed python-hello/Dockerfile.portable, which still installed the old Git archive. Enumerating every declared build profile and all Dockerfile-named files found exactly one additional recipe (48 total including the skeleton). It now pins public a2 from the official index, and the dead codex source-helper comment is removed. Existing template checking now scans each declared profile and rejects missing/archive pins or package drift from the default recipe. A regression covers all three failures without weakening source/profile readiness gates. The earlier default-plus-proxy success is not a portable pass.

## Current public CLI and dependency integration

PR220 merged normally at 04e6b95a343811fec492dcc0994a1b696a5469f2 after 8 successful checks and its 2 existing image/canonical skips. A normal main merge retains its modern managed consumer, current authentication documentation and records. The prepared-image scripts keep the reviewed a2 proof/runtime/digest changes; current managed verification takes PR220's implementation.

Fresh official npm `@agent-sandbox/cli@0.5.3` installation succeeded. Its actual public template-launch and native deploy/delete/from-image help contracts passed without cloud mutation. The CI job retains its express-cli-contract name and now installs that public package instead of building a fixed obsolete source checkout. Current README wording uses template launch; Python's prepared-reference example calls launch_template with the original manifest, not a removed workflow selector. The unused legacy workflow-contract copies/sync helper were found only self-referencing and removed; current launch-v1 synchronization remains verified. No historical receipts were changed.

After the normal PR220 dependency merge and final documentation/public-CLI sweep: archive, managed lifecycle, shared HTTP, public launch and document regression suite 75 PASS; actual fresh public CLI 0.5.3 parser contract 1 PASS; document links 222/0 and launch contract lock PASS. The portable profile compliance suite passed 58 tests and all 47 manifests remain conformant. Current-head remote CI and final runtime matrix remain distinct gates.

## Hidden workflow reference correction

The final f630ecfe75f91de9b44c3f80fccc66030d2eaa5d CI run 40205022209 failed local-e2e because its .github/workflows/e2e.yml still invoked deleted sync_workflow_contracts.py. The earlier calling search omitted hidden directories, so the statement that only self-references remained was incomplete. An explicit hidden-directory search finds the historical CI byte-lock invocation; remove it with the retired copies. The same existing job retains adjacent sync_launch_contracts.py --check, current specification/catalog checks and real acceptance regressions. This is removal of an obsolete historical contract lock, not a skipped current launch gate. Original failure log is preserved.
