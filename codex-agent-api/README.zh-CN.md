# codex-agent-api

## 做什么

这是由官方 Codex CLI 驱动的项目会话 HTTP 适配器。镜像与 [`codex`](../codex) 模板统一固定 `@openai/codex@0.162.1`，通过端口 9000 上的 `agent-sandbox-server` 提供命名命令和 `/v1/agents/*` 路由。此处只承诺下表所列接口，尚未验证对 OpenAI Agents API 所有功能或 SDK 方法的兼容性；不要假定存在某个 `client.beta.agents` SDK 接口。

每轮调用上游 `codex exec --json`。首轮创建新线程，后续轮次只恢复本会话捕获的确切线程 id。独立后台监视器并发消费 stdout/stderr；即使无人订阅也执行 300 秒期限，超时、删除会话或正常退出时清理进程组。多个订阅者共享有界回放缓冲，不竞争读取 stdout。

## 技术栈

Alibaba 平台基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，部署默认区域 `cn-hangzhou`、版本 `v0.0.49`。沿用镜像 Python 3.13、Node.js 20；Codex 固定 0.162.1；server SDK 固定 python-sdk commit `e2cb27e24fde0a67112f82b8d44af463445a5d1a`，已包含 dataclass 命令加载修复，见 [Dockerfile](Dockerfile)。以 `user` 运行，应用目录 `/home/user/app`，工作区 `/home/user/workspace`。Dockerfile 不设置 `CMD` 或 `ENTRYPOINT`。

## 解决的问题

围绕真实 Codex 提供 HTTP 会话管理、JSONL 到 SSE 映射、用量统计和确切线程恢复。模型推理、工具执行仍由 Codex 完成。会话和已保存的 agent 配置只在内存中保存，重启即丢失。同一部署的会话共享工作区和身份；互不信任的客户端应使用独立沙箱。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在仓库根目录，使用已有的提供方配置：

```bash
abx template deploy ./codex-agent-api -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> codex_version
abx run <sandbox-id> agent_status
abx run <sandbox-id> codex --arg prompt='Reply with hello' --arg timeout_s=120
```

模型调用需要在创建沙箱时通过秘密注入机制提供密钥和模型，不要将秘密写入源文件或 shell 历史。默认 `CODEX_SANDBOX=workspace-write`。Express 可能不允许 Linux 用户命名空间；只有确认容器提供所需隔离时，才在创建环境中明确设置 `CODEX_SANDBOX=bypass`。适配器不自动更改隔离选择。

## 快速开始（Python SDK）

使用 `agent-sandbox-client`（导入名 `agent_sandbox`），不要安装无关的 PyPI `agent-sandbox`：

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    runtime_env = {name: os.environ[name] for name in (
        "OPENAI_API_KEY", "CODEX_API_KEY", "ABX_LLM_API_KEY", "OPENAI_BASE_URL",
        "ABX_LLM_BASE_URL", "CODEX_MODEL", "CODEX_SANDBOX",
    ) if os.environ.get(name)}
    sb = await Sandbox.create(template="<template-id>", envs=runtime_env)
    try:
        print(await sb.run("codex_version"))
        result = await sb.run("codex", prompt="Reply with hello", timeout_s=120, timeout=150)
        print(result["status"])
    finally:
        await sb.kill()

asyncio.run(main())
```

模型调用需要配置下表中的运行时提供方环境。SDK 命名命令直接返回命令结果。

## 快速开始（HTTP POST）

使用沙箱端口 9000 的经过认证的 URL，并保留提供方要求的认证头。配置 `ABX_SERVER_TOKEN` 后，服务端另要求 `Authorization: Bearer <token>`。

```bash
curl -X POST "$SANDBOX_URL/commands/codex" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Reply with hello","model":"your-model","timeout_s":120}'
curl -X POST "$SANDBOX_URL/v1/agents/sessions" \
  -H 'Content-Type: application/json' \
  -d '{"agent":{"model":"your-model","instructions":"Be concise"},"input":"Reply with hello","background":true}'
curl "$SANDBOX_URL/v1/agents/sessions/<session-id>"
curl -N -X POST "$SANDBOX_URL/v1/agents/sessions/<session-id>/events" \
  -H 'Content-Type: application/json' \
  -d '{"input":"Continue","stream":true}'
```

命名命令返回 `{"result": ...}`，会话路由直接返回 JSON，`stream=true` 时返回 SSE。HTTP 200 的 JSON 中若 `status=failed`，仍表示模型调用失败。`background=true` 立即返回，之后轮询至 `idle`、`failed` 或 `cancelled`；不能同时将 `stream`、`background` 设为 true。

## 命令参考

| 命令 | 参数（类型；必填/默认值） | 返回值 | 上游 argv |
|---|---|---|---|
| `codex_version` | 无 | 版本字符串 | `codex --version` |
| `agent_status` | 无 | 包含会话 id/status/model 的 JSON 字符串 | 无 |
| `codex` | `prompt` str 必填；`model` str `""`；`timeout_s` int `300`，范围 1–3600 | `{thread_id, events, status, events_truncated}`；上游失败抛 RuntimeError | `codex exec --json --color never --skip-git-repo-check [提供方/隔离/模型配置] -- <prompt>` |

以下是本项目的 HTTP 约定。成功 CRUD 返回 HTTP 200；对象不存在 404，参数错误 400，已有活动轮次 409，超出容量 429。

| 方法与路径 | 参数 / 行为 |
|---|---|
| `POST /v1/agents` | `model` str `""`，`instructions` str `""`，`tools` list `[]`，`name` str `""`，`metadata` object `{}`；返回带 `agent_*` id 的配置 |
| `GET /v1/agents` | `{object:"list",data:[...]}` |
| `GET /v1/agents/{id}` | 返回配置 |
| `POST /v1/agents/{id}` | 更新上述配置字段 |
| `DELETE /v1/agents/{id}` | `{id,object,deleted:true}` |
| `POST /v1/agents/sessions` | `agent` 内联 `{model,instructions,tools}` 或已保存 id，默认 `{}`；`input` 可选字符串或 `[{type:"input_text",text:...}]`；`stream` bool false；`background` bool false |
| `GET /v1/agents/sessions` | 会话列表 |
| `GET /v1/agents/sessions/{id}` | 状态、配置、最近五条保留输出项、累计 input/output token 用量 |
| `POST /v1/agents/sessions/{id}` | 更新 `model` / `instructions` |
| `DELETE /v1/agents/sessions/{id}` | 删除并终止活动 CLI 及工具进程组 |
| `POST /v1/agents/sessions/{id}/events` | 必填 `input`（同上），或 `{type:"agent.session.input.message",content:[{type:"input_text",text:...}]}`；`stream` bool 默认 true；`background` bool false，开启后台时默认关闭流式 |
| `GET /v1/agents/sessions/{id}/events` | 活动时回放保留事件并订阅；空闲时返回 JSON 状态 |
| `GET /v1/agents/sessions/{id}/items` | 保留的 Codex item 事件 |
| `GET /v1/agents/sessions/{id}/artifacts/{artifact_id}` | 最大 1 MB 的 UTF-8 文本文件；id 为工作区相对路径的 URL-safe base64 |
| `DELETE /v1/agents/sessions/{id}/artifacts/{artifact_id}` | 删除工作区内文件 |

内容数组只使用首个 `input_text`，不实现图片/音频输入。工具只接受 URL 型 MCP：`{type:"mcp",server_label:"name",server_url:"https://host/mcp",headers:{...}}`，也支持嵌套 `transport` 的 URL/headers。函数工具、托管 connector、HTTP 审批、webhook、持久化及每会话独立文件系统不在当前约定内。MCP 通过 `-c mcp_servers.<label>.*` 交给 Codex，秘密只应由受信任的运行时配置注入。

SSE 包括 `agent.session.created`、`agent.session.turn.started`、`agent.session.turn.completed`、`agent.session.turn.failed`、`agent.session.output_item.added`、`agent.session.output_item.done`。未知类型使用 `agent.session.<type>` 前缀。`agent.session.events.truncated` 表示旧回放记录已丢弃。token 用量仅从上游 `turn.completed` 累加一次，不随订阅者数量重复。

## 配置

| 环境变量 | 默认值 / 含义 |
|---|---|
| `OPENAI_API_KEY`、`CODEX_API_KEY`、`ABX_LLM_API_KEY` | 空；运行时秘密。ABX key 仅在 OPENAI key 未设置时补齐；直连 OpenAI 使用 CODEX key，并可从 OPENAI key 补齐 |
| `OPENAI_BASE_URL`、`ABX_LLM_BASE_URL` | 空；OPENAI URL 优先。自定义提供方使用 HTTP Responses API，`wire_api="responses"`，关闭 websocket |
| `CODEX_MODEL`、`ABX_LLM_MODEL` | 空；CODEX 优先，否则使用上游配置模型 |
| `CODEX_SANDBOX` | `workspace-write`；可选 `read-only`、`workspace-write`、`danger-full-access`、`bypass` |
| `CODEX_HOME` | 镜像设置 `/home/user/.codex`；应位于工作区和 artifacts 之外 |
| `WORKSPACE` | `/home/user/workspace` |
| `AGENT_MAX_SESSIONS` | `20` |
| `AGENT_SESSION_TTL` | `1800` 秒；每 60 秒 GC |
| `ABX_SERVER_PORT`、`ABX_SERVER_TOKEN` | `9000`、空；端口和服务认证 |

服务最多保留 200 个 agent 配置，每会话最多 100 轮。回放及保留 item 缓冲各限制为 1000 个事件 / 2 MB；单行 JSONL 超过 256000 字节时轮次失败。stderr 始终消费，只将有界且脱敏的尾部用于错误提示。环境秘密值、请求提供的 MCP header 值与 bearer token 从返回事件、配置、错误和文本 artifact 中脱敏。Artifact 拒绝 `.env`、`.aws`、`.codex`、`.ssh` 路径及指向工作区外的符号链接。标准 shell/files 接口仍需要受信任访问及 server policy；这些过滤不是租户隔离。

## 资源

2 vCPU、4096 MB；每个活动会话一个 CLI，受会话容量限制。模型和工具调用均计入期限。不要求容器内 Docker、KVM、额外权限或第二个 HTTP 服务。

## 已验证

尚未记录任何通过的提供方测试。

本地真实子进程回归覆盖静默 stdout 超时、大量 stderr、进程组清理、无人订阅后台到期、秘密脱敏、回放边界及多订阅用量统计。HTTP 冒烟覆盖 CRUD 和参数拒绝。`test_http_runtime.py` 用明确的合成 CLI fixture 验证真实 HTTP/后台/SSE/取消及 MCP header 隔离，不冒充上游执行验证。静态检查或 L0 不代表镜像、云提供方或真实模型验收。本机已执行固定版本 CLI 的 version/help；本次恢复尚无 L1 镜像构建或 L2 提供方部署通过结果。

```bash
python3 scripts/check_template.py codex-agent-api
python3 codex-agent-api/test_commands.py
python3 codex-agent-api/test_http_runtime.py
python3 -m pytest codex-agent-api/test_e2e_protocol.py -q
E2E_BASE_URL=http://127.0.0.1:9000 python3 codex-agent-api/e2e_test.py
# 仅在运行时已配置授权凭据时进行真实模型验证：
E2E_REQUIRE_LLM=1 E2E_MODEL=your-model E2E_BASE_URL=https://your-sandbox \
  python3 codex-agent-api/e2e_test.py
```

真实 coding 验证先上传已有故障 `normalizer.py`，通过 `/shell` 执行控制端持有的六项固定测试并确认失败，再要求后台 agent 修复原源码并创建 `normalization-report.json`。控制端下载源码，分别用 files/artifact API 读取并核对新产物，再运行同样六项固定测试，必须 exit 0。测试一直留在控制端，不上传为模型可修改的文件。随后通过同会话 SSE 确切线程恢复，生成包含报告真实 SHA-256 和输出数量的第二产物；核对原源码/报告未变并再次运行固定测试。仅回复 `ABX_E2E_OK`、`ABX_RESUME_OK` 不能通过。`E2E_REQUIRE_LLM=1` 强制执行，远端缺少凭据、上游错误或显式关闭执行均失败；只有未请求模型的可选 L0 会报告 SKIP。`E2E_TOKEN` 优先、兼容 `ABX_SERVER_TOKEN`，用于服务认证；工作区不为 `/home/user/workspace` 时设置 `E2E_WORKSPACE`，可用 `E2E_LLM_TIMEOUT` 调整控制端轮询期限。最后只删除本次唯一探针目录和会话。fake-remote 协议回归覆盖成功分支，并拒绝仅 marker、错误报告及错误恢复产物；它们不属于真实模型/提供方证据。固定 archive 已支持 `agent-sandbox-server serve --commands` 加载带延迟注解的 dataclass；若注入 server wheel，应从相同的已修复 commit 构建。

## Express 源码运行验证

2026-10-16，改动后的源码在自有 Express base 实例中使用固定 Codex 0.162.1 与真实 Responses 兼容模型通过 30 项外部 HTTP 检查。正式 `serve --commands` 入口成功加载含 dataclass 的模块。验收修复已有故障源码，通过控制端持有的六项固定测试，核对新报告，再恢复同一上游线程并独立检查第二产物与报告 SHA-256。自有实例已销毁。[JSON 证据](evidence/runtime-express-2026-10-16.json)与[HTTP 结果](evidence/runtime-express-2026-10-16.log)包含源码、wheel 溯源信息。此结果不等于 Dockerfile L1 或新模板部署 L2，`tested_on` 保持为空；复现步骤见[共享诊断工具](../docs/express-source-runtime.md)。

## 二次开发

先读[设计说明](../docs/design/codex-agent-api.md)、[贡献规范](../CONTRIBUTING.md)和[模板规范](../docs/template-spec.zh-CN.md)。围绕 Codex JSONL 扩展适配，不另写 agent 循环。CLI pin 与 `codex` 保持一致。[OpenAI 官方 CLI 文档](https://developers.openai.com/codex/cli/reference/)。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py codex-agent-api`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

评审前运行 checker 和本地回归，在 PR 中准确说明 L1/L2/L3 的真实结果和限制。仅保存通过的提供方 evidence。禁止提交 `.env`、认证头、秘密值或生成的凭据/配置文件。

## 问题反馈

[模板 issue #23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23)。SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI/deploy 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题加 `[templates]`。

## 许可证

Apache-2.0。Codex 和依赖沿用各自上游许可证。
