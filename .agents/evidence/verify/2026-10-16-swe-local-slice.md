# SWE single-instance verification — 2026-10-16

Result: PARTIAL

Scope: new `swe/`, design, catalog/README/backlog, scoped workflow regression row and owner records. Independent branch based on Aider final9bcc1a1; no Pi/Aider runtime changes.

- PASS: official mini-swe-agent2.4.6 PyPI metadata/wheel115037bytes SHA256 a35463c553ac825c7773b03cfa69cd44958e3af20155dcc5711fdf9e4c67cd54 inspected, genuine CLI and local environment extension confirmed. Python>=3.10, no Node requirement.
- PASS: original Verified instance from pinned dataset revision, one FAIL_TO_PASS and59 PASS_TO_PASS; no gold solution included. Official base archive692792bytes SHA256 b1a4c83b7d12981b81e5f8d2028a73eacfbd153f4e425504c254a6f177b99997 checked. Original environment saysPython3.11.10; this is an explicitly separatePython3.13 portability run.
- PASS:32 scoped command/process/privacy/HTTP-protocol tests. Actual Linux subprocess cleanup on leader exit and deadline, bounded stdout/stderr, opaque paths/symlink storage/locks/default refusal; missing/duplicate/skipped/error/wrong-identity and missing-target-model controls. HTTP fixture tests are harness regressions, not real-model proof.
- PASS: scoped `scripts/check_template.py swe`, all20spec directories strict conformance,22spec regression tests; scoped actual HTTP L0 has5PASS and explicit real-modelSKIP. Initial bool fixture `yes` was accepted by the server coercion contract; changing the negative to an unparseable boolean produced the required400.
- FAIL retained: source attempt1 installed pinned dependencies but default base lacked the server executable; no baseline/model run. Exact owned instance kill and independent scoped list absence verified. A stream cleanup exception initially interrupted report serialization; sanitized failure was recovered from its exact private journal.
- PASS: pinned server wheel216310bytes SHA256 a09a4846fef8b49f3a059d1c65e38d283986aa4fbf879dd09192100c30039fc9, all56server modules match sourcee2cb27e24fde0a67112f82b8d44af463445a5d1a.
- RUNNING: owned Express source-runtime pinned dependencies and real instance compatibility/model/evaluation. No pass claim before actual results.
- NOT RUN: actual new image build, full canonical `scripts/express_e2e.py swe`→local `abx template deploy` wrapper, other providers, official Docker harness/benchmark score, full datasets/SWE-agent/SWE-rebench.

Issue: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35. Catalog remains experimental and `tested_on: []`. Supplementary acceptance will use separate evidence files and exact source hashes, without private resource IDs or raw model logs.
