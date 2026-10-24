# Source application quick-start verification — 2026-10-24

Status: PASS for the local checks and scoped Qwen public-entry repetition below. Final PR checks/review and public documentation deployment are separate gates.

## Inputs and scope

Base: `ba17fbd32da188a2e4452f5946fa72135fc41c8e`. Documentation-only changes to
46 source-template README pairs and `_skeleton`; no source runtime, Dockerfile,
manifest, model dependency or historical receipt changes. The shared guide already
uses public CLI0.4.16 and Python client0.3.1a5. This record does not requalify the
original 92-case matrix under new README/source digests.

Before editing, a scoped scan of active quick-start text found create examples in
46/46 source templates, implicit `sb.run` in 38/46, URL-only `network.get_url` in
27/46, detached create environment injection in 8/46, and stale Stack
requalification text in 13/46. These are matched documentation patterns, not 46
independent runtime failures. `_skeleton` shared the obsolete examples.

## Local checks

- PASS: `python scripts/check_docs.py`: 222 documents, zero link/fragment failures.
- PASS: `python scripts/check_template.py --all`: zero claimed spec failures.
- PASS: 98 Python fenced blocks parsed with `ast.parse`; snippets using `await`
  retain their documented enclosing async context. This is syntax, not execution.
- PASS: all 47 bilingual entries retain an actual manifest smoke command; each
  matches a registered command and satisfies its required arguments. The two Qwen
  Python blocks are identical across languages. An
  active-text scan before Verified finds no `sb.run`, `Sandbox.create`, `abx create`
  or URL-only `network.get_url` examples.
- PASS: `python -m pytest -q qwen-code/test_commands.py`: 11 passed in the existing
  SDK development environment. Initial execution in the checker-only environment
  FAILED collection because `agent_sandbox` was absent; the correctly provisioned
  environment rerun passed. No model or cloud was called by these unit tests.
- PASS: `git diff --check`; all current changed files are README pairs.

## API review

Compared published CLI source/help: positional upload/download, `template launch`
with workflow and sandbox timeout, named command discovery/run and owned kill.
CLI0.4.16 `requestApplication` defaults to 30 seconds and `runCommand` does not
forward a configurable deadline: long Qwen calls are documented through Python
and HTTP with 330-second waits, separately from 300-second task deadlines.
Qwen manifest empty secret values inherit the launching shell; nonempty defaults
win over shell values, so endpoint/workspace changes explicitly edit the manifest
before launch. No late export is claimed to reconfigure an application.

## Public Qwen repetition

PASS: [Actions run40120874641](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40120874641), test harness commit
`6bb4d7538e636333259224e51a0075bcb56664f6`, with
[the unchanged sanitized report](2026-10-24-qwen-public-application.json).

- Remote Git source: `alibaba-agent-sandbox/awesome-templates//qwen-code@98ab49fc390ab6b29700aa86d819ece8dc1273fc`.
- CLI installed from npm: `@agent-sandbox/cli@0.4.16`; host client/server installed
  from PyPI: `0.3.1a5`. The Qwen image keeps its original pinned server source.
- Express adapter is built into those packages. The report's fixture provider
  SHA is explicitly not an installed third-party plugin revision.
- `qwen_version` and `qwen_setup_check` succeeded through host CLI, Python and
  HTTP. Setup asserted installed=true, version=0.23.0, api_key_set=false on each.
- Incorrect application token returned401. Runtime commands.py bytes matched;
  SDK process execution and file round-trip succeeded.
- Owned sandbox, registered template and ACR image tag independently confirmed
  absent: zero cleanup failures, retained artifacts or uncertain resources.
- This reused the existing harness with the same documented API calls. It did
  not execute the README Python fences verbatim and did not call a real model.

Input identities remain exactly as recorded: manifest
`6a8e7a2206df27ea7657be1cb6f5619f3891e21fa99c9681d194a35709b515c8`, source
`c6ba7ab821bfb8a5a22324036a3dcb9bd025d4bb4b7cb4107e51fa9eb2ca1c6a`, default
profile. The later merge of managed-doc main131aec7 and configuration-table
corrections through c9c5552 did not change the Qwen directory (Git diff empty).
The final docs additionally set `ABX_PROVIDER` before all CLI calls to keep the
selected provider consistent with the explicit Python connection. The harness
already selected Express on every CLI request. This final prose/example change
changes the README/source digest; the receipt still belongs to98ab49f, not the
new final source digest. Runtime, manifest and calling APIs remain unchanged.
This report is not a claim that all46 final README source digests ran in the
separate original matrix, nor an OpenSandbox Qwen or real-model pass.

## Delivery gates

Current-head CI and cross-review are required before merge. Source documentation
publication needs the Website/Registry final aggregation; it is not claimed by
this repository check. Historical receipts remain unchanged. The original
full matrix stays independently tracked in Issue203.
