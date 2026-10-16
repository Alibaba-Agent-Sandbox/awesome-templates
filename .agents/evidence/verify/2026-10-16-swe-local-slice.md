# SWE single-instance verification — 2026-10-16

Result: PARTIAL

Scope: new `swe/`, design, catalog/README/backlog, scoped workflow regression row and owner records. Independent branch based on Aider final9bcc1a1; no Pi/Aider runtime changes.

- PASS: official mini-swe-agent2.4.6 PyPI metadata/wheel115037bytes SHA256 a35463c553ac825c7773b03cfa69cd44958e3af20155dcc5711fdf9e4c67cd54 inspected, genuine CLI and local environment extension confirmed. Python>=3.10, no Node requirement.
- PASS: original Verified instance from pinned dataset revision, one FAIL_TO_PASS and59 PASS_TO_PASS; no gold solution included. Official base archive692792bytes SHA256 b1a4c83b7d12981b81e5f8d2028a73eacfbd153f4e425504c254a6f177b99997 checked. Original environment saysPython3.11.10; the initial explicitly separatePython3.13 run failed; the new eval runtime is fixed to originalPython3.11.10 without altering tests/filters.
- PASS:33 scoped command/process/privacy/HTTP-protocol tests. Actual Linux subprocess cleanup on leader exit and deadline, bounded stdout/stderr, opaque paths/symlink storage/locks/default refusal; missing/duplicate/skipped/error/wrong-identity and missing-target-model controls. HTTP fixture tests are harness regressions, not real-model proof.
- PASS: scoped `scripts/check_template.py swe`, all20spec directories strict conformance,22spec regression tests; scoped actual HTTP L0 has5PASS and explicit real-modelSKIP. Initial bool fixture `yes` was accepted by the server coercion contract; changing the negative to an unparseable boolean produced the required400.
- FAIL retained: source attempt1 installed pinned dependencies but default base lacked the server executable; no baseline/model run. Exact owned instance kill and independent scoped list absence verified. A stream cleanup exception initially interrupted report serialization; sanitized failure was recovered from its exact private journal.
- PASS: pinned server wheel216310bytes SHA256 a09a4846fef8b49f3a059d1c65e38d283986aa4fbf879dd09192100c30039fc9, all56server modules match sourcee2cb27e24fde0a67112f82b8d44af463445a5d1a.
- PASS: actual installed official CLI controls in source attempt2: Unicode stdout/stderr and exit7 reach trajectory observation; action timeout propagates through the real DefaultAgent/CLI, only one model-fixture call, no following action, ordinary child absent/exited after owned cleanup. This uses the official deterministic model, not a real external model.
- FAIL retained: source attempt2 reaches real-instance preparation but strict exact baseline precondition fails; no real-model call. Owned sandbox kill and list absence PASS. [Attempt2](../../../swe/evidence/source-runtime-2026-10-16-attempt2.json) preserves hashes/results; its input hash map includes local harness files as well as uploaded modules. Later import-only module loading adaptation does not promote this failed source run to current-head acceptance.
- PASS: initial actual L1 image build for bb37790 (run38862469952/job116847731833), artifact12030220694; archiveSHA256 0d3ffd2da9f32094622e033b500c7ad91c89750d250e2dec2d05aa1b0bdc64e4, tar1212359680bytes. Manifest provenance inspected with858host bytes, no bulk host image download. Actual image diagnostics completed:2PASS/0FAIL/58ERROR/0SKIP onPython3.13.13, unique FAIL_TO_PASS node is ERROR, controlled categories identify pkgutil.get_loader deprecation and original warning-as-error policy. No model call. [Immutable initial image failure](../../../swe/evidence/image-runtime-2026-10-16-initial.json). All10owned helper/instances/template/tag/repository cleanup and absence flags TRUE.
- PARTIAL: bb37790 PR local-e2e passes but push local-e2e fails exact test `test_process_leader_exit_and_timeout_cleanup_descendants[False]`: child disappears between `/proc` exists/read. Test and actual-CLI verifier now read directly, accepting FileNotFound as successful absence; test uses bounded wait for exited/absent. Local33tests pass after correction; latest-head remote CI pending.
- NOT RUN: real model repair, full canonical `scripts/express_e2e.py swe`→local `abx template deploy` wrapper, other providers, official Docker harness/benchmark score, full datasets/SWE-agent/SWE-rebench.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35. Catalog remains experimental and `tested_on: []`. Supplementary acceptance will use separate evidence files and exact source hashes, without private resource IDs or raw model logs.

PR: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/96 (draft; no merge claim). Scoped16Markdown links and2Python examples parse/check PASS.

## Original Python evaluation runtime correction

- Official python-build-standalone release20241016 asset metadata and65-byte SHA files checked: CPython3.11.10 x86 stripped21205300bytes SHA25603f15e19e2452641b6375b59ba094ff6cf2fc118315d24a6ca63ce60e4d4a6e0; aarch64 stripped19963074bytes SHA2569d124604ffdea4fbaabb10b343c5a36b636a3e7b94dfc1cccd4531f33fceae5e. No host runtime/dependency download performed.
- Docker now installs that SHA-checked standalone interpreter only for the evaluation venv; base server and mini agent retain nativePython3.13/Node20. Instance archive, original test patch and all60nodeIDs remain unchanged.
- Reports probe the actual evaluation interpreter and reject version drift before tests. They no longer infer evaluation Python from the server's sys.version.
- New runtime actual image CI and model repair are pending. Earlier failures remain FAIL; no official Docker score, provider promotion, canonical deploy or merge claim.
