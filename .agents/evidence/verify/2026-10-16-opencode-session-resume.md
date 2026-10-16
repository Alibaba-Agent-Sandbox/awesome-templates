# OpenCode exact-session continuation verification

Date: 2026-10-16

Result: PARTIAL

The exact-session source-runtime acceptance passed. Required Dockerfile L1 and newly deployed template L2 gates remain unverified because Docker is unavailable in this environment. The template remains experimental with `tested_on: []`; [issue #17](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/17) remains open and [PR #82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) remains an open draft.

## Scope and environment

Files: `opencode/e2e_test.py`, `opencode/test_e2e_protocol.py`, both OpenCode READMEs and `docs/design/opencode.md`. Runtime commands remain unchanged. Python 3.13 with the existing Agent Sandbox client/server development environment; pinned OpenCode `opencode-ai@1.19.0`; Express existing `base` template; model `dashscope/qwen3.8-flash`. Credentials were injected in memory and are excluded from files/output.

Tested runtime source hashes:

| File | SHA-256 |
|---|---|
| `opencode/commands.py` | `e49f601544443658b517f14b60027e7f58dab71cbb38b8572139ea0a13802768` |
| `opencode/e2e_test.py` | `f235aec266b5f6db97e68e6738f264df9cae0116edc306d852c9cfa47b15b5f8` |
| `opencode/Dockerfile` | `f155b1ac054074414268221cc906e1d364ffde5558782fe511f4250ade07cd9a` |
| `opencode/template.yaml` | `eb4a138df2893d502f0665ebe47bfd637023f12f29ee157441deab5d43bf0cb1` |
| `scripts/express_runtime_e2e.py` | `dfbc3513928d5037d844f78602dc00ec6d2964544822dd58318c9761b8629cf2` |
| `opencode/opencode.json` | `80f3c55ef5170410b30fa94f810e4e3fd4d9291fe45f300e94fbbbca45a76bd9` |

## Commands and results

- `python -m pytest opencode/test_commands.py opencode/test_e2e_protocol.py -q`: exit 0, 24 passed. Protocol tests use a fake remote model and real subprocesses; they establish harness regression behavior only.
- `python scripts/check_template.py opencode`: exit 0, conformant.
- `python scripts/express_runtime_e2e.py opencode --server-wheel <built-server-wheel> --output-dir <artifact-directory> --model dashscope/qwen3.8-flash`: exit 0. Owned Express base sandbox creation, source/configuration upload, dependency installation, command-server startup, external SDK health, pinned CLI version and configuration checks all passed. Complete HTTP verifier: 28 PASS, 0 FAIL, 0 SKIP, real model required.
- `git diff --check`: exit 0 for scoped files. Configured-secret value scan passed for changed OpenCode source/tests/design; a final scan accompanies staging.

The real model repaired an existing broken source file while preserving fixed tests. The controller reran the fixed tests and held-out assertions. A second call used exactly the returned session id, required a new `resume.json`, independently verified its original-report SHA-256 and computed sums, checked unchanged source/tests/report/acceptance bytes and reran independent assertions. Wrong-session replies, wrong hashes/calculations, missing resume artifacts and source/report/test mutations are covered by negative protocol cases.

The verifier removed its unique project directory. The owning runner killed its created sandbox in `finally`, and both cleanup checks passed. No other sandbox or template was deleted.

## Provenance limits

The server wheel was reused from the recovered development environment; its SHA-256 is `e8e7943da6dfb61a4832c18a3edcb6aa698b7b13679cd712fd58a1c37534291f`. The client was loaded from the SDK checkout at `bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea`. Comparing every wheel Python module with archived SDK source at `e2cb27e24fde0a67112f82b8d44af463445a5d1a` found 55 of 56 identical files; `agent_sandbox/server/__main__.py` differed. The recovered wheel is therefore identified by its hash rather than claimed to be an exact build of that commit. Uploaded template hashes are independent of this provenance limitation. This source-runtime run does not verify image layers, build instructions, new-template readiness or a public port proxy for a newly deployed image. It does not establish another provider's compatibility.
