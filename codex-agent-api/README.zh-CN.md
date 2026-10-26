# codex-agent-api

## 做什么

这是由官方 Codex CLI 驱动的项目会话 HTTP 适配器。镜像与 [`codex`](../codex) 模板统一固定 `@openai/codex@0.162.1`，通过端口 9000 上的 `agent-sandbox-server` 提供命名命令和 `/v1/agents/*` 路由。此处只承诺下表所列接口，尚未验证对 OpenAI Agents API 所有功能或 SDK 方法的兼容性；不要假定存在某个 `client.beta.agents` SDK 接口。

每轮调用上游 `codex exec --json`。首轮创建新线程，后续轮次只恢复本会话捕获的确切线程 id。独立后台监视器并发消费 stdout/stderr；即使无人订阅也执行 300 秒期限，超时、删除会话或正常退出时清理进程组。多个订阅者共享有界回放缓冲，不竞争读取 stdout。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 Codex CLI `0.162.1`、Node.js 20，以及 9000 端口上的模板会话 API。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

模型服务必须实现 HTTP Responses，仅提供 Chat Completions 不够。`ABX_LLM_API_KEY` 用作自定义服务密钥；启动环境不要同时保留冲突的 `OPENAI_BASE_URL`，本模板该 URL 优先。API Key 方式无需交互登录。`CODEX_SANDBOX` 默认为 `workspace-write`；只有平台不支持内层 Codex 沙箱且你接受外层沙箱为隔离边界时，才使用现有 `bypass` 选项。

编码前须确认平台能运行 Codex 内层 Linux 沙箱。平台拒绝时，公共配方中固定的 `CODEX_SANDBOX=workspace-write` 不能通过 host export 修改。如果你明确选择以外层沙箱作为隔离边界，clone 仓库，将 `codex-agent-api/template.yaml` 的 `env.CODEX_SANDBOX` 改为 `bypass`，使用 `abx template launch ./codex-agent-api --sandbox-timeout 1800 --yes` 替换下面的公共配方命令。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_LLM_API_KEY='<your-model-or-vendor-key>'
export ABX_LLM_BASE_URL='https://api.openai.com/v1'
export CODEX_MODEL='<model-id-from-your-Responses-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//codex-agent-api --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" codex --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","timeout_s":300}'
```

任务要求在 `/home/user/workspace` 写出 `generated_hello.py` 和 `GENERATED_REPORT.md`。示例显式开放所需的编辑/工具权限，只在自己拥有的可丢弃沙箱中使用。下面的 SDK 和 HTTP 是同一任务的替代调用方式，选择一种即可。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('codex', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', timeout_s=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/codex`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "timeout_s": 300
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 420 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

### 导出产物与清理

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

程序预期输出 `Hello from the sandbox`。先读取产物并检查再使用；模型回答成功不代表文件一定存在。文件不会自动回写模板或你的本机，释放沙箱前必须导出。

`close()`/`aclose()` 仅关闭客户端连接，不释放沙箱。launch 日志中的已构建模板和镜像可能保留用于复用，不再需要时仅删除自己创建的那些资源。

## 命令参考

| 命令 | 参数（类型；必填/默认值） | 返回值 | 上游 argv |
|---|---|---|---|
| `codex_version` | 无 | 版本字符串 | `codex --version` |
| `agent_status` | 无 | 包含会话 id/status/model 的 JSON 字符串 | 无 |
| `codex` | `prompt` str 必填；`model` str `""`；`timeout_s` int `300`，范围 1–3600 | `{thread_id, events, status, events_truncated}`；上游失败抛 RuntimeError | `codex exec --json --color never --skip-git-repo-check [提供方/隔离/模型配置] -- <prompt>` |

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

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

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
| `ABX_SERVER_TOKEN` | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

服务最多保留 200 个 agent 配置，每会话最多 100 轮。回放及保留 item 缓冲各限制为 1000 个事件 / 2 MB；单行 JSONL 超过 256000 字节时轮次失败。stderr 始终消费，只将有界且脱敏的尾部用于错误提示。环境秘密值、请求提供的 MCP header 值与 bearer token 从返回事件、配置、错误和文本 artifact 中脱敏。Artifact 拒绝 `.env`、`.aws`、`.codex`、`.ssh` 路径及指向工作区外的符号链接。标准 shell/files 接口仍需要受信任访问及 server policy；这些过滤不是租户隔离。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/workspace`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/codex-agent-api.md)。

## 问题反馈

[模板 issue #23](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/23)。SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI/deploy 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题加 `[templates]`。

## 许可证

Apache-2.0。Codex 和依赖沿用各自上游许可证。
