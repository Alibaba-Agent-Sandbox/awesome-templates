# Local Express acceptance: 2026-10-18

The current task prioritizes Alibaba Express. Real deployment and model runs are
initiated locally; Actions cloud/model acceptance is not required and no cloud
credentials were uploaded to Actions. Existing basic PR/main checks remain.

| Template | Local real Express/model outcome | Exact scope |
| --- | --- | --- |
| Qwen Code0.23.0 | PASS,17 HTTP/model assertions, independent owned cleanup0 | Existing Express base, qwen3-coder-flash, actual code edit and held-out assertions |
| Codex0.162.1 | PASS,17 HTTP/model assertions, independent owned cleanup0 | Existing Express base, qwen3.8-flash, actual code edit and held-out assertions |
| Codex Agent API0.162.1 | PASS,30 HTTP/model assertions, independent owned cleanup0 | Production server command loader on existing Express base, qwen3.8-flash |
| OpenCode1.19.0 | PASS,28 HTTP/model assertions after verifier repair; independent owned cleanup0 | Existing Express base, dashscope/qwen3.8-flash; actual edit, held-out assertions and exact-session resume. Two pre-fix failures retained |

Paired controller/server sources: SDK421ee4da78a1014e4e925a42edb6d9c4bf00b2b5.
The corresponding source was merged in
https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/65.
Successful receipts and sanitized HTTP assertions live under each template's
`evidence/source-runtime-2026-10-18-local-model.{json,log}`. They record source and
wheel hashes and independent cleanup readback. This validates the named sources
in real Express instances, not deployment of each Dockerfile as a new image.

The controller has no Docker executable, daemon socket or configured engine
endpoint. Full local image build and `abx template deploy` remain BLOCKED by
that prerequisite. No `tested_on` or catalog certification changed. Source model
success and earlier hosted image builds do not substitute for canonical L2.
See [local canonical entry point](canonical-express-review.md#current-task-local-express-acceptance)
and [runtime instructions](express-source-runtime.md).

The old orphan-registry PR had one failed push run and one passing PR run on the
same reported head. A real delayed-Node regression established the startup race;
[repair113](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/113)
merged after its current-head basic check passed. The orphan
[cleanup111](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/111)
then ordinarily integrated the repair, passed the new-head check and merged.
Both old failed runs and evidence remain history. Required current checks must
pass; historical failed runs need not be erased or relabeled.

OpenCode's `text` result intentionally concatenates all assistant steps. Its old
L3 check compared that aggregate with a final marker, rejecting intermediate
commentary. The corrected verifier reads the last completed stop step in the
same session and still requires the actual source edit, unchanged original
tests, retrieved artifacts, independent assertions and exact-session resume.
The command API stays unchanged. Fixture tests alone establish no model pass.

## 中文

本轮优先极速版，真实部署与模型验收在本地发起，不要求 Actions 云端验收，也不
上传凭据；正常 PR／main 基础检查保留。Qwen Code、Codex、Codex API 的真实
模型源码运行分别通过17、17、30项检查，独立读回确认各自实例残留为0。
OpenCode 的前两次失败保留；最后完成步骤解析修复后的严格验收已通过28项，包含实际改码、独立断言和指定会话续接，独立读回确认自有实例残留为0。
所有结果均为已有 Express base 上的源码运行，不能代替新镜像构建、完整模板
部署或 provider 认证。当前本地缺少 Docker Engine，完整镜像部署仍受此前置
条件阻塞，不再等待 Actions Secret 授权。
