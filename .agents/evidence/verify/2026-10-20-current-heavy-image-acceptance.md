# Current-version heavy image acceptance

Status: PARTIAL for the whole batch; PASS for the four exact profiles below.

All images were exported by successful exact-source CI at 58e8e79b641766982fe579d3b623900513ea5d30, validated against Docker context, artifact/archive/config/commands hashes, transferred only after registry privacy readback, and registered with the native CLI. Model settings were injected into a separately owned server, without cloud/GitHub secrets. Each accepted run independently confirms sandbox/template/registry cleanup and unchanged registry digest after execution. No older receipt was relabelled.

- browser-automation 2.0.2: complete Chromium screenshot/PDF/independent artifact HTTP 24 PASS / 0 FAIL / 0 SKIP; [canonical receipt](../../../browser-automation/evidence/express-2026-10-20.json).
- pi 1.0.1: 18 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion; [canonical receipt](../../../pi/evidence/express-2026-10-20.json).
- hermes-agent 1.1.1: 17 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion; [canonical receipt](../../../hermes-agent/evidence/express-2026-10-20.json).
- aider 1.0.1: 21 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion; [canonical receipt](../../../aider/evidence/express-2026-10-20.json).

Browser step attempt remains FAIL: no READY within1200 seconds, last official state building, independent cleanup true. This does not invalidate its separately passed real-image scope or establish step success. The browser Docker contract includes both bounded RUN separation and non-root writable workspace; version2.0.2 resolves the two branches' independent2.0.1 proposals.

SWE1.0.1 real image strict model attempt remains FAIL (8 PASS/1 FAIL/0 SKIP), before agent submission/evaluation; independent sandbox/template/registry cleanup passed. A diagnostic replay is in progress. Its tested_on remains empty and no benchmark/model qualification is inferred. DeepSeek/Qwen model reruns are also still pending. Existing native-service-key blockers remain explicit.

Integration with current main preserves the OCR resource validator and same-day exact-version/cleanup receipt regression; both conflicting checker tests remain. No cloud/model fixture is promoted to acceptance.

Post-integration verification:39 specification/controller unit tests PASS;58 targeted materializer/image/archive/cleanup tests plus18 subtests PASS; strict25 catalog templates plus skeleton PASS;126 local Markdown documents checked with0 broken links; git diff whitespace check PASS. The initial unittest-discovery invocation matched0 pytest functions and is not counted as validation; the actual pytest suites above then ran. Latest-head CI remains required.
