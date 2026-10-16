# OpenCode exact-session continuation: clean-wheel repeat

Date: 2026-10-16

Result: PARTIAL

The independently rebuilt-wheel Express source-runtime acceptance passed: 28 HTTP checks, 0 failures, 0 skips, real model required. Dockerfile L1 and newly deployed image L2 remain unverified because Docker is unavailable. The catalog remains experimental and `tested_on` remains empty. [Issue #17](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/17) stays open; [PR #82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) is an open draft.

## Problem and repeat scope

The [earlier recovered-wheel run](2026-10-16-opencode-session-resume.md) passed but used a recovered server wheel with an older `__main__` command loader. That loader lacked stable realpath/SHA-256 module naming, normal `sys.modules` registration, repeat-import deduplication and import-failure rollback. This repeat rebuilds from the current clean server source rather than relabeling that artifact. The earlier run remains a separate historical record.

## Build provenance

- `python -m build --wheel --no-isolation --outdir <clean-output> python-sdk/server-sdk`: exit 0.
- SDK source commit: `bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea`; `server-sdk/src` had no changes against HEAD.
- Every packaged Python file was compared byte-for-byte with `git archive` of that commit: **56/56 identical**, zero mismatches.
- Server wheel SHA-256: `a09a4846fef8b49f3a059d1c65e38d283986aa4fbf879dd09192100c30039fc9`.

## Real-backend validation

`python scripts/express_runtime_e2e.py opencode --server-wheel <clean-wheel> --output-dir <new-artifact-directory> --model dashscope/qwen3.8-flash --sdk-source-commit bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea`: exit 0.

Environment: Python 3.13, current Agent Sandbox client checkout, pinned OpenCode `opencode-ai@1.19.0`, existing Express `base` template, real `dashscope/qwen3.8-flash` endpoint. All model/cloud configuration stayed in process environments. Only public source/configuration and the server wheel were uploaded.

Owned sandbox creation, public upload, dependency installation, startup, external SDK health, pinned CLI version and public configuration smoke all passed. The HTTP verifier passed all 28 checks: existing-code repair, preserved fixed tests, downloaded report/acceptance artifacts, independent test/held-out reruns, previously absent resume artifact, exact returned session-id reuse, independently computed report digest and ordered calculation results, preserved original four files, and post-resume held-out assertions.

| Tested source/configuration | SHA-256 |
|---|---|
| `opencode/commands.py` | `e49f601544443658b517f14b60027e7f58dab71cbb38b8572139ea0a13802768` |
| `opencode/e2e_test.py` | `f235aec266b5f6db97e68e6738f264df9cae0116edc306d852c9cfa47b15b5f8` |
| `opencode/Dockerfile` | `f155b1ac054074414268221cc906e1d364ffde5558782fe511f4250ade07cd9a` |
| `opencode/template.yaml` | `eb4a138df2893d502f0665ebe47bfd637023f12f29ee157441deab5d43bf0cb1` |
| `scripts/express_runtime_e2e.py` | `5dd158257b43c9888f688a20d57a4c25a49aa7dc08ec6e51a7ad015ad6ee54b5` |
| `opencode/opencode.json` | `80f3c55ef5170410b30fa94f810e4e3fd4d9291fe45f300e94fbbbca45a76bd9` |

The verifier deleted its unique project directory; the owning runner killed its created sandbox in `finally`. Both cleanup checks passed. No unrelated sandbox/template was changed or deleted.

## Local checks and scope limits

The unchanged command/protocol regression suite previously passed 24 tests, and the OpenCode checker was conformant. Protocol fixtures are not real-model evidence.

A separate local real pinned OpenCode process used a temporary port and a synthetic password: the command wrapper authenticated its target-side `/global/health` successfully with version 1.19.0, anonymous access returned HTTP 401, and owned-process cleanup passed in `finally`. The synthetic value was omitted from output. The Express run authenticated the command server with Bearer auth; no OpenCode serve password was injected there, so that run does not separately establish cloud Basic-auth behavior despite the legacy test-label wording.

This source-runtime repeat does not build the Dockerfile, deploy a new image/template, prove a new image's public port proxy, or verify another provider. Image acceptance evidence remains empty. This record supplements the decision [note](../../notes/proposed/feature/2026-10-16-opencode-session-resume.md).
