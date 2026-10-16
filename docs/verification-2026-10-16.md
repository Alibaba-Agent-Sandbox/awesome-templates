# Template verification, 2026-10-16

The original business request is not complete. This page tracks the implementation
and review batch; per-template evidence preserves the exact source hashes of each
run. A source-runtime pass on an existing Express base is distinct from building
and deploying the changed Dockerfile.

## Implemented and reviewed

All 16 product directories now follow spec v2, have English and Chinese references
for CLI/Python SDK/HTTP POST, command arguments, authentication, errors, extension,
contribution and issue routing, and have a design document. The strict checker
also checks catalog/template capability agreement. All changed entries remain
`experimental`, with empty current-version provider acceptance metadata.

The batch fixes process/output/privacy contracts and real coding acceptance for
Python hello, browser automation, Claude Code, Codex, Codex API, Node web, OpenCode,
Amp, Droid, Gemini, Qwen Code, Qoder, DeepSeek and Hermes. Agents CLI now installs
actual pinned Codex/Qwen CLIs and applies the same explicit endpoint policy through
both direct and production startup. Its synthetic CLIs are test-only fixtures.

Amp/Droid/Gemini/Qwen/Qoder/Hermes command workers and the OpenClaw health probe
retain the owned Linux session leader until process-group cleanup; normal and
nonzero completion clean up redirected background descendants too. OpenClaw's
long-running gateway has separate owned, authenticated lifecycle control.

Hermes has an additional upstream boundary: the CLI viewer can submit to a detached
authority/managed worker. Its CLI process deadline is not proof that accepted
upstream work was cancelled. See its README and scoped verification record; do not
claim gateway cancellation is implemented.

## Verified results and boundaries

| Scope | Actual result | Boundary |
|---|---|---|
| Strict catalog/spec check | All 16 products plus skeleton conformant | Static verification |
| Local HTTP suite | All 17 directories pass | Models disabled; not L3 |
| First actual image CI at `7289e69` | 13 images built and passed keyless container checks; 3 jobs failed | Two context-preparation failures and one Droid install failure; fixes await the next run |
| Coding/process/privacy/protocol regressions | Passed suites are recorded in repository evidence | Synthetic providers/CLIs are labeled; not cloud acceptance |
| Qwen current owned-process source on Express | 17 HTTP checks pass, including real source repair, preserved tests, downloaded artifacts and independent target tests | Existing base, no changed-image deployment |
| Droid current owned-process source on Express | 9 HTTP checks pass; owned instance cleaned | Keyless installation/contract only; Factory coding unverified |
| OpenCode clean-wheel source on Express | 28 HTTP/model/resume checks pass | Exact session and artifact verification; no image deployment |
| Python hello / Codex / Codex API / Node web source on Express | Historical batch passes retained with their hashes | These records do not cover unrelated later revisions |
| OpenClaw current local CLI | Authenticated start/health/stop lifecycle passes, 11 checks | Not model coding or Express deployment |
| Hermes current local CLI + compatible real model | Coding/artifact/independent-test acceptance passes | Local target, custom provider; not Express or all gateway cancellation |
| DeepSeek local compatible model | Successful coding runs, later failed attempt and final rerun recorded separately | Compatible provider is distinct from native DeepSeek credentials |
| Browser on plain Express base | Failed: Chromium cannot load libglib-2.0.so.0; owned sandbox cleaned | Dockerfile installs system dependencies; this run did not execute that layer |

Latest source-runtime reports for Qwen and Droid are under each template's
`evidence/runtime-express-2026-10-16-owned-processes.*`. Earlier same-day reports
remain historical; their source hashes are not silently reassigned to current code.
The server wheel was built from the recorded SDK revision and compared byte-for-byte
against its tracked Python modules. The [source runner](express-source-runtime.md)
uses a random engine socket nonce to prevent native-exec PID collisions.

## Open acceptance and roadmap

- The first actual L1 matrix passed 13 images and failed 3 jobs. The follow-up
  fixes exact Dockerfile FROM matching and Droid's native package install. See the
  [first-run evidence](../.agents/evidence/verify/2026-10-16-image-build-first-ci.md).
  All 16 images still need to pass at the corrected head; a queued run is not a
  successful build. The workflow also exports only the already built Python hello
  image for a separate local registry transfer and L2 attempt.
- New-image Express deployment (L2), current-version provider acceptance, release
  and promotion remain unverified. Source upload does not replace these gates.
- Claude, Amp, Droid, Gemini and Qoder need their compatible authorized credentials
  for real coding acceptance. Agents CLI needs an out-of-band artifact verifier;
  its intentionally closed shell/files HTTP routes are not opened just for a test.
- Native DeepSeek and other sandbox providers require their actual credentialed
  environments; compatible-model tests do not establish those integrations.
- SWE/OSWorld, conditional Windows/phone/Android workloads, market-derived new
  templates, remaining provider build paths and the complete Skills/MCP P0–P2
  roadmap are unfinished. Existing [backlog](backlog.md) Issues remain authoritative.
- Template PR remains draft until mandatory image/cloud/model/CI/review gates pass.
  No acceptance Issue is closed merely because local tests pass.

## 中文

原业务需求尚未全部完成。现有 16 个模板已统一到 v2 规范并补齐中英文
CLI、SDK、HTTP POST、参数、认证、错误、贡献与二次开发文档；含骨架的
17 个目录严格检查及本地 HTTP 套件通过。多种命令生命周期已修复正常结束后
遗留后台后代的问题，并用真实进程回归验证。

Qwen 当前源码在真实极速版通过 17 项含真实编程、产物和独立测试的检查；
Droid 当前源码通过 9 项无模型检查。OpenClaw 真实本地认证生命周期通过。
Hermes/DeepSeek 的兼容模型结果属于本地目标服务，不能当作原生提供方或
极速版部署验收；Hermes CLI 超时也不能保证取消独立 authority 已接受的任务。
浏览器在普通 Express base 中缺少 libglib，复验失败且实例已清理。

首轮实际镜像 CI 有 13 个通过、3 个失败；FROM 匹配和 Droid 原生包安装的修复
正在复验，并准备导出 Python hello 镜像以继续 L2。新镜像部署、模型专属凭据、其他提供方、
后续模板及完整 Skills/MCP 路线图仍有未完成项。所有改动模板保持 experimental，
不填未通过的 provider，不把计划、SKIP、排队 CI 或源码运行称为全部交付。
