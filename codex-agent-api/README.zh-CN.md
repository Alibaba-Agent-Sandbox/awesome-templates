# codex-agent-api

## 做什么

这是由官方 Codex CLI 驱动的项目会话 HTTP 适配器。镜像与 [`codex`](../codex) 模板统一固定 `@openai/codex@0.162.1`，通过端口 9000 上的 `agent-sandbox-server` 提供命名命令和 `/v1/agents/*` 路由。此处只承诺下表所列接口，尚未验证对 OpenAI Agents API 所有功能或 SDK 方法的兼容性；不要假定存在某个 `client.beta.agents` SDK 接口。

每轮调用上游 `codex exec --json`。首轮创建新线程，后续轮次只恢复本会话捕获的确切线程 id。独立后台监视器并发消费 stdout/stderr；即使无人订阅也执行 300 秒期限，超时、删除会话或正常退出时清理进程组。多个订阅者共享有界回放缓冲，不竞争读取 stdout。

## 技术栈

Alibaba 平台基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，部署默认区域 `cn-hangzhou`、版本 `v0.0.49`。沿用镜像 Python 3.13、Node.js 20；Codex 固定 0.162.1；server SDK 固定 python-sdk commit `e2cb27e24fde0a67112f82b8d44af463445a5d1a`，已包含 dataclass 命令加载修复，见 [Dockerfile](Dockerfile)。以 `user` 运行，应用目录 `/home/user/app`，工作区 `/home/user/workspace`。Dockerfile 不设置 `CMD` 或 `ENTRYPOINT`。

## 解决的问题

围绕真实 Codex 提供 HTTP 会话管理、JSONL 到 SSE 映射、用量统计和确切线程恢复。模型推理、工具执行仍由 Codex 完成。会话和已保存的 agent 配置只在内存中保存，重启即丢失。同一部署的会话共享工作区和身份；互不信任的客户端应使用独立沙箱。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./codex-agent-api --workflow application --yes
abx run <sandbox-id> codex_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('codex_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/codex_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.162.1"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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
| `ABX_SERVER_PORT` | `9000`；服务端口 |
| `ABX_SERVER_TOKEN` | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

服务最多保留 200 个 agent 配置，每会话最多 100 轮。回放及保留 item 缓冲各限制为 1000 个事件 / 2 MB；单行 JSONL 超过 256000 字节时轮次失败。stderr 始终消费，只将有界且脱敏的尾部用于错误提示。环境秘密值、请求提供的 MCP header 值与 bearer token 从返回事件、配置、错误和文本 artifact 中脱敏。Artifact 拒绝 `.env`、`.aws`、`.codex`、`.ssh` 路径及指向工作区外的符号链接。标准 shell/files 接口仍需要受信任访问及 server policy；这些过滤不是租户隔离。

## 资源

2 vCPU、4096 MB；每个活动会话一个 CLI，受会话容量限制。模型和工具调用均计入期限。不要求容器内 Docker、KVM、额外权限或第二个 HTTP 服务。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## Express 源码运行验证

2026-10-16，改动后的源码在自有 Express base 实例中使用固定 Codex 0.162.1 与真实 Responses 兼容模型通过 30 项外部 HTTP 检查。正式 `serve --commands` 入口成功加载含 dataclass 的模块。验收修复已有故障源码，通过控制端持有的六项固定测试，核对新报告，再恢复同一上游线程并独立检查第二产物与报告 SHA-256。自有实例已销毁。[JSON 证据](evidence/runtime-express-2026-10-16.json)与[HTTP 结果](evidence/runtime-express-2026-10-16.log)包含源码、wheel 溯源信息。此结果不等于 Dockerfile L1 或新模板部署 L2，`tested_on` 保持为空；复现步骤见[共享诊断工具](../docs/express-source-runtime.md)。


固定测试重跑还要求全部六项真实完成且无跳过/预期失败后，输出本轮控制器独有的随机确认值；伪造 `Ran 6 tests`/`OK` 后提前退出不能通过。这是普通测试完成性检查，不是针对同用户恶意代码的隔离边界。`E2E_SERVER_TOKEN` 单独提供 generation2 Bearer 凭据，不混用旧 E2E_TOKEN 网关头。

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

### 2026-10-20完整 step 检查点：模板2.0.0

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154830Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，18 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
