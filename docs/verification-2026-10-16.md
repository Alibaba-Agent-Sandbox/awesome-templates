# Template verification, 2026-10-16

This batch implements changes; it does not complete the full catalog roadmap.
The new `experimental` entries remain unqualified for provider deployment until
image-build and deployment gates pass. Existing historical evidence is retained,
but evidence for another template version cannot qualify the changed version.

| Scope | Actual result | Limit |
|---|---|---|
| Local HTTP runtime, all 17 directories | PASS | Optional model cases explicitly skipped; L0 only |
| Process/privacy/acceptance-harness regressions | 66 PASS | Synthetic CLI/protocol fixtures are explicitly synthetic |
| Spec tooling | 20 PASS | Simulated deployment fixtures are not real cloud runs |
| Catalog conformance | 9 conformant including skeleton; 8 legacy; v2 failures 0 | Existing legacy violations remain open |
| Python hello, patched source on real Express base | 21 HTTP checks PASS | Pinned pytest 8.4.2; no Dockerfile build/deployment |
| Codex, patched source on real Express base | 16 HTTP checks PASS including real coding task | Pinned Codex 0.162.1; no Dockerfile build/deployment |
| Codex API, patched source on real Express base | 30 HTTP checks PASS including real background coding and exact-thread resume | Production serve loader, Codex 0.162.1; no Dockerfile build/deployment |
| Browser automation | 24 real Chromium local checks PASS | Playwright 1.58.0; no cloud image validation |
| Node web | 60 local assertions and 60 real Express source-runtime HTTP checks PASS | Includes real HTTP/build/log/process lifecycle; no Dockerfile build/deployment |
| OpenCode | 17 process/ownership regressions and 15 local HTTP checks PASS | Real 1.19.0 binary; model task not run |
| Claude Code | 10 regressions and 19 local checks PASS | Actual pinned 2.0.76 version/help checked; model credential absent |

The successful source-runtime runs have per-template JSON/log evidence with source and
server-wheel hashes. Every created cloud sandbox was owned by the run and destroyed.
The shared [Express source runner](express-source-runtime.md) can reproduce these
checks. A source-runtime pass is not a substitute for L1/L2; `tested_on: []`
remains accurate for changed templates lacking those gates.

## Changes covered

- Python hello, browser automation, Claude Code, Node web and Codex API now follow
  the v2 image/entrypoint/resource/smoke/document contract with bilingual references.
- Coding-agent tests validate source changes, new artifacts and independently
  executed assertions. Marker-only responses fail required model acceptance.
- Codex sandbox selection fails before workspace mutation unless an authorized
  mode permits fallback; successful output is redacted too.
- OpenCode stop/restart uses an owned live process handle, interpreter and process
  group identity. A stale PID file cannot authorize killing an unrelated process.
- Codex API bounds/reaps upstream processes, checks deadlines during busy output,
  separates subscriber replay from execution accounting, and redacts nested object
  keys as well as values. REST support is the documented project subset.
- HTTP POST examples are part of the bilingual template contract. CI installs the
  pinned CLIs/browser and executes the regression suites; remote CI results must
  be checked separately after pushing.

## CI and additional cloud findings

One remote CI run failed because an immediate equal-size rewrite of the Python
negative test reused pytest assertion bytecode within the same timestamp tick.
A real controlled reproduction confirmed the stale pass. The verifier now uses a
fresh negative-control module; real Express revalidation passes all 21 checks.
The original CI failure is retained, and the corrected push must pass remote CI.

Node web additionally passed all 60 external checks on a real owned Express base.
OpenCode passed a first real-model coding task with 23 checks; exact-session
continuation is being strengthened and will be recorded after its own run.
Browser source-runtime dependency setup failed with `UNAVAILABLE: Stream removed
(Socket closed)`; its owned instance was destroyed. That run is not a pass.

## Remaining work

Docker is not available in this execution workspace. No L1 Docker build or L2 new
image deployment has passed for this batch. Do not promote changed templates or
close their acceptance issues until these gates and required model tests pass.
Claude model acceptance needs its authorized provider key. OpenCode's real model
coding/resume acceptance remains to run. Other providers require their actual
credentialed environments; no provider compatibility is inferred from Express.

Eight legacy templates still need migration: agents-cli, deepseek-harness, droid,
gemini, hermes-agent, openclaw, qoder and qwen-code. Candidate templates and benchmark
runtimes in [the backlog](backlog.md), provider build hooks, package publication and
the complete MCP/Skills roadmap remain separate unfinished work. Refer to the
existing catalog issues; this batch does not close them as completed.

## 中文

本批已落地七个模板及共享规范/CI 的实现与修复，但完整目录路线图尚未完成。
17 个目录本地 HTTP 运行通过；66 项回归、20 项规范工具测试通过。
规范检查有 9 个合规目录（含 skeleton），8 个旧目录仍待迁移。
Codex、Python hello、Codex API 分别在真实 Express base 中通过 16、21、30 项
源码运行检查；Codex 两项包含真实模型编程任务，API 另验同线程恢复及产物哈希。
所有本次创建的实例已销毁。各模板 JSON/log 保留源码和 server wheel 哈希。

这些结果不等于 Docker 镜像构建和新镜像部署。当前环境无 Docker，L1/L2 未通过，
因此改动模板保持 experimental，未通过的提供方不写入 `tested_on`。
Claude 缺少授权模型 key；OpenCode 真模型 coding/resume、其他提供方的真实环境、
八个旧目录迁移、候选模板/基准环境、provider 构建接口、包发布和完整 MCP/Skills
均仍是未完成事项。静态审查、合成 fixture 或计划不记作这些事项已经完成。
