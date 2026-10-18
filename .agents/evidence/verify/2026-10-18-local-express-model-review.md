# Verification: local Express first and strict model acceptance

Date:2026-10-18. Result:PARTIAL; real source-model outcomes below; image deploy BLOCKED.
User scope: locally initiated real deployment/model acceptance, Express first;
no Actions cloud/model acceptance or secret upload is required.

## Sources and environment

Linux x86_64, local Python3.13, paired client/server0.3.0 installed from clean
SDK421ee4da78a1014e4e925a42edb6d9c4bf00b2b5; `pip check` PASS, server wheel build PASS.
Template runtime sources initially from89a91e642be156cc6c62bebabc05766dcb3c589e.
Commands/config/Dockerfile/harness and wheel SHA256 are in the new receipts.
Cloud credentials and model keys were supplied only through process environments;
only public source/config/wheel payloads entered files. No Actions secret upload.

## Executed local real Express runs

`python scripts/express_runtime_e2e.py TEMPLATE --server-wheel BUILT_WHEEL
--output-dir PRIVATE_OUTPUT --sdk-source-commit 421ee4da... --model MODEL`
was called by a local controller with an owned-ID private journal and independent
SDK list/readback after cleanup; no Actions cloud run was dispatched.

- Qwen Code0.23.0, qwen3-coder-flash:9 checks PASS; external real-model suite17
  PASS/0FAIL, including actual source changes, original tests, downloaded artifacts
  and independent held-out assertions. Independent owned remaining0/listed0.
- Codex0.162.1, qwen3.8-flash:8 checks PASS; external real-model suite17 PASS/0FAIL.
  Independent owned remaining0/listed0.
- Codex API0.162.1, qwen3.8-flash:8 checks PASS; production loader/external real-model
  suite30 PASS/0FAIL. Independent owned remaining0/listed0.
- OpenCode1.19.0 original verifier: two attempts (qwen3-coder-flash, then configured
  dashscope/qwen3.8-flash), each external suite17 PASS/1FAIL at final response/session.
  Both instances destroyed and independently confirmed absent. The first independent
  controller audit initially used `SandboxInfo.id`; it was corrected to the actual
  `sandbox_id` field and repeated. This was a controller mistake, not an SDK defect.
  Diagnostic metadata for the configured model showed HTTP200, a session and two
  text events across multiple tool steps; no prompts/text/identifiers were recorded.
  Corrected real-model run:9 checks PASS; external strict real-model suite28
  PASS/0FAIL including actual source edits, independent original/held-out tests,
  exact-session resume and report hash/results verification. Independent owned
  remaining0/listed0. Do not relabel the two failed attempts; see
  [retained failed summaries](2026-10-18-opencode-model-failed-attempts.json).

Successful source-runtime receipts and sanitized logs are under the respective
`TEMPLATE/evidence/source-runtime-2026-10-18-local-model.{json,log}` paths. No provider
L2 receipt, `tested_on` badge, catalog status, Dockerfile or SDK/CLI contract changed.
Full local image build/deploy remains BLOCKED: no Docker executable, socket or
configured engine endpoint. This is an infrastructure prerequisite, not pending
Actions credential-storage consent. Existing Actions plan is optional and idle.

## Regression and merge review

OpenCode protocol regression: before fix valid one-step PASS, valid intermediate
commentary FAIL; after fix combined command/protocol56 PASS. Existing negative
fixtures still reject marker-only, tampered tests/artifacts, process early exits,
zero/skip tests, stale bytecode and incorrect resumed sessions. Six new cases reject
truncation, tool-only completion, wrong event session, error events, unfinished next
step and malformed JSON. Final completion requires stop in the exact session;
independent target code assertions are unchanged.

Accepted main e258fdc2 ordinarily merged. Resolve conflicts by preserving integrated
Node HTTP readiness/lifecycle, bilingual docs, all23 catalog entries and specialized
media/document checks; preserve independent immutable server input e2cb27e. Retain
main's delayed-real-Node regression with explicit temporary WORKSPACE and permit
its integrated ValueError form. Initial local test lacked WORKSPACE and hit a host
permission error before entry validation; corrected the fixture environment, not
runtime permissions. The integrated real HTTP protocol tests2 PASS; corrected
missing-entry regression1 PASS after setting its explicit temporary WORKSPACE.

Main repair113 merged4eb66f75 and cleanup111 mergede258fdc2, each after current-head
basic CI PASS. Main's local-e2e and dispatch checks both PASS. Failed cc69f1b9 push
and successful PR runs remain history; latest accepted heads have no failed checks.
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/114 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/109.

All four successful local Express source/model runs total92 external assertions,
0 failures on their passing attempts. Every owned instance was destroyed and
independently confirmed absent. OpenCode's two original failed attempts remain
separate. These facts do not prove new image deployment or all23 templates.
No additional registry/website change is necessary for these source-only receipts:
public command API, catalog fields, provider certification and shared UI are unchanged.

Final static verification: spec tooling35 PASS; strict checker23 products plus
skeleton,0 failures. Changed Markdown relative links, merge markers, secret-value
scan and all four receipts' source/config/verifier hashes PASS. The local source
HTTP Node protocol tests2 PASS plus corrected delayed-Node regression1 PASS.
