# Template verification, 2026-10-16

The original business request is not complete. This page tracks the implementation
and review batch; per-template evidence preserves the exact source hashes of each
run. A source-runtime pass on an existing Express base is distinct from building
and deploying the changed Dockerfile.

## Implemented and reviewed

At checkpoint `a361f490555ead0ff67081ffb4874abf292a1b2f`, all 17 product directories
(the original 16 plus Pi) follow spec v2, have English and Chinese references
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
| Strict catalog/spec check | All 17 products plus skeleton: 18 conformant directories | Static verification at the Pi checkpoint |
| Local HTTP suite | The original batch passed 17 directories; the Pi follow-up passed its targeted 10-check suite | Models disabled; these scopes do not establish L3 |
| First actual image CI at `7289e69` | 13 images built and passed keyless container checks; 3 jobs failed | Historical first failure is retained: two preparation failures and one Droid install failure |
| Corrected original image matrix at `7cb0d94` | [Run 38850050144](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38850050144): 16/16 image jobs completed successfully | Actual Docker L1; no cloud or model acceptance |
| Pi/offline-tools image matrix at `a361f49` | [Run 38853293050](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38853293050): 17/17 image jobs and plan completed successfully; 17 image artifacts exported | Actual Docker L1 including fixed Pi offline tools; artifacts alone do not establish L2 |
| Coding/process/privacy/protocol regressions | Passed suites are recorded in repository evidence | Synthetic providers/CLIs are labeled; not cloud acceptance |
| Qwen current owned-process source on Express | 17 HTTP checks pass, including real source repair, preserved tests, downloaded artifacts and independent target tests | Existing base, no changed-image deployment |
| Droid current owned-process source on Express | 9 HTTP checks pass; owned instance cleaned | Keyless installation/contract only; Factory coding unverified |
| OpenCode clean-wheel source on Express | 28 HTTP/model/resume checks pass | Exact session and artifact verification; no image deployment |
| Python hello / Codex / Codex API / Node web source on Express | Historical batch passes retained with their hashes | These records do not cover unrelated later revisions |
| OpenClaw current local CLI | Authenticated start/health/stop lifecycle passes, 11 checks | Not model coding or Express deployment |
| Hermes current local CLI + compatible real model | Coding/artifact/independent-test acceptance passes | Local target, custom provider; not Express or all gateway cancellation |
| DeepSeek local compatible model | Successful coding runs, later failed attempt and final rerun recorded separately | Compatible provider is distinct from native DeepSeek credentials |
| Pi local source + compatible real model | 17-check coding/artifact/independent-test pass at `b285760`, recorded in [Pi evidence](../.agents/evidence/verify/2026-10-16-pi-runtime.md) | Local source L3; later offline-tool scope has separate evidence; image-backed/cloud L3 remains pending |
| Browser on plain Express base | Failed: Chromium cannot load libglib-2.0.so.0; owned sandbox cleaned | Dockerfile installs system dependencies; this run did not execute that layer |
| Python hello production-Builder image cloud attempt | Actual pushed image registered READY; hello/run_script passed SDK, CLI and HTTP (6 calls). Full HTTP suite then failed preflight `/health` (0 PASS, 1 FAIL, exit 2); sandbox, template, registry tag and repository were cleaned | FAIL retained; the controller omitted required network proxy settings. A correction or pending rerun is not a pass |

Latest source-runtime reports for Qwen and Droid are under each template's
`evidence/runtime-express-2026-10-16-owned-processes.*`. Earlier same-day reports
remain historical; their source hashes are not silently reassigned to current code.
The server wheel was built from the recorded SDK revision and compared byte-for-byte
against its tracked Python modules. The [source runner](express-source-runtime.md)
uses a random engine socket nonce to prevent native-exec PID collisions.

The exact image-job snapshots and this checkpoint's scope are recorded in
[image CI checkpoint evidence](../.agents/evidence/verify/2026-10-16-image-ci-checkpoint.md).
The first-run failure record and earlier Pi records remain unchanged.

## Cloud evidence and the canonical L2 gate

The separate CI-image → daemonless registry transfer → official CreateTemplate →
new sandbox → SDK/CLI/HTTP acceptance exercises real cloud components. Report it
as supplementary changed-image cloud verification with its exact outcomes. It
does not execute the full `abx template deploy` path and does not, by itself,
fulfil this repository's L2 definition. No running batch result is counted here.

[The specification](template-spec.md#test-levels) requires `abx template deploy`
to reach READY. [CONTRIBUTING.md](../CONTRIBUTING.md) and the specification's
contribution checklist additionally require `scripts/express_e2e.py <dir>` to exit
0 before committing `evidence/express-<date>.json`. Until that gate passes, do not
write a canonical provider-pass file, populate `tested_on`/Verified or promote a
catalog entry on the strength of the supplementary path. Failed diagnostics
belong in engineering records, not a template provider-pass evidence file.

## Open acceptance and roadmap

- The first actual L1 matrix passed 13 images and failed 3 jobs. The corrected
  `7cb0d94` matrix passed all 16; the later `a361f49` matrix passed all 17 including
  Pi. See the
  [first-run evidence](../.agents/evidence/verify/2026-10-16-image-build-first-ci.md).
  The later run exported the already built selected 17 images for an authorized
  cloud batch. Export does not imply transfer, deployment or acceptance.
- Canonical new-image Express deployment (L2), current-version provider acceptance,
  release and promotion remain unverified. Supplementary image-cloud checks and
  source uploads do not replace the canonical runner gate above.
- Pi is implemented on the stacked [PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86);
  its cloud/image-backed L3 is pending. [Aider PR 88](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88)
  remains under development and is outside this 17-product checkpoint. The
  [OSWorld issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36)
  is an active implementation slice, not a delivered benchmark template.
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

原业务需求尚未全部完成。检查点 `a361f49` 包含原 16 个模板与新增 Pi，共
17 个产品、含骨架 18 个目录，严格规范检查通过，并补齐中英文 CLI、SDK、
HTTP POST、参数、认证、错误、贡献与二次开发文档。原批次本地 HTTP 套件及
Pi 后续定向套件分别通过，均不代表云部署。多种命令生命周期已修复正常结束后
遗留后台后代的问题，并用真实进程回归验证。

Qwen 当前源码在真实极速版通过 17 项含真实编程、产物和独立测试的检查；
Droid 当前源码通过 9 项无模型检查。OpenClaw 真实本地认证生命周期通过。
Hermes/DeepSeek 的兼容模型结果属于本地目标服务，不能当作原生提供方或
极速版部署验收；Hermes CLI 超时也不能保证取消独立 authority 已接受的任务。
浏览器在普通 Express base 中缺少 libglib，复验失败且实例已清理。

首轮实际镜像 CI 的 13 通过、3 失败保留为历史。修复后 `7cb0d94` 的实际 run
38850050144 全部 16 个镜像通过；`a361f49` 的 run 38853293050 全部 17 个镜像
及 plan 通过，并导出 17 份镜像归档。它们证明 L1，不证明 L2 或模型调用。
Pi 在 `b285760` 有本地兼容模型编程与独立测试通过记录，后续工具修改有独立证据，
云端／镜像内 L3 尚未通过。Aider PR 88 仍在开发，OSWorld Issue 36 仍属实现中的
切片，均不计入本检查点交付。

Python hello 生产 Builder 镜像已真实注册 READY，SDK／CLI／HTTP 六次烟测通过，
随后完整 HTTP 套件因控制器遗漏所需代理配置而在 `/health` 预检失败；实例、模板、
镜像 tag 与仓库已清理。本次失败保留，修正及正在进行的复验不当作通过。
CI 镜像转移加官方注册属于补充云端验证；规范仍要求 `abx template deploy` READY，
且仅 `scripts/express_e2e.py` 退出 0 后才能提交标准 provider 通过记录及填写
`tested_on`／Verified。新镜像完整部署、模型专属凭据、其他提供方、后续模板及
完整 Skills/MCP 路线图仍有未完成项。所有改动模板保持 experimental，
不填未通过的 provider，不把计划、SKIP、排队 CI 或源码运行称为全部交付。
