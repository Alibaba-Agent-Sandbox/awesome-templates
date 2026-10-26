# codex

在 Agent Sandbox 里以非交互方式运行 [OpenAI Codex CLI](https://github.com/openai/codex)。镜像钉死 `@openai/codex@0.162.1`。

## 做什么

`agent-sandbox-server`（端口 9000）上的命名命令调用 `codex exec`。`codex_exec` 返回 JSONL 事件（`thread.started`、`turn.*`、`item.*`）、最后一条助手消息，以及用于续跑的 `thread_id`。`codex_version` 打印 CLI 版本。`codex_setup_check` 探测 Codex 自己的 Linux 沙箱；bubblewrap、seccomp 或遗留 landlock 路径起不来时，报告 `--dangerously-bypass-approvals-and-sandbox`。`codex_config_write` 为 OpenAI 兼容的 `base_url` 写入 `$CODEX_HOME/config.toml`（只接受 `wire_api = "responses"`）。`codex_agents_write` 写入 `AGENTS.md`，Codex 会从工作目录读取它。

Codex 0.162.1 不接受旧的 `codex -p ... --output-format json`，也会拒绝 `--full-auto`。

独立的 `apply_patch` 二进制是另一个模板（issue #60）。Agents API 的 HTTP 服务是 `codex-agent-api`（issue #23）。见 [docs/design/codex.md](../docs/design/codex.md)。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 `@openai/codex@0.162.1`、Node.js 20、Git、ripgrep 和 jq。CLI 包包含其 Linux 内层沙箱辅助程序。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

自定义服务必须支持 HTTP Responses API（`/responses`），只有 Chat Completions（`/chat/completions`）不够。填写 Responses 服务商提供的 endpoint/model，不能直接假定百炼 Chat endpoint 兼容。包装在 `CODEX_HOME` 写入提供方配置，并显式引用 `ABX_LLM_API_KEY`；此 API Key 路径不需要 ChatGPT 浏览器登录。默认 `sandbox="auto"` 在内层 Linux 沙箱不可用时可能选用 bypass，仅用于自己拥有的可丢弃外层沙箱。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_LLM_API_KEY='<your-model-or-vendor-key>'
export ABX_LLM_BASE_URL='https://api.openai.com/v1'
export CODEX_MODEL='<model-id-from-your-Responses-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//codex --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" codex_exec --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","sandbox":"auto","cwd":"/home/user/workspace","timeout_s":300}'
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
            print(await client.commands.run('codex_exec', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', sandbox='auto', cwd='/home/user/workspace', timeout_s=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/codex_exec`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "sandbox": "auto",
  "cwd": "/home/user/workspace",
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

| 命令 | 参数 | 返回 |
|---|---|---|
| `codex_version` | 无 | 字符串 `X.Y.Z` |
| `codex_setup_check` | 无 | 对象，探测结果和绕过标志 |
| `codex_exec` | 见下表 | 对象，事件和最后一条消息 |
| `codex_config_write` | `base_url`、`provider`、`env_key`、`model`、`wire_api`、`codex_home` | 对象，路径和 toml |
| `codex_agents_write` | `content`（必填）、`cwd` | 对象，`path` 和 `bytes` |

| 名称 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `prompt` | string | 是 | | 指令。放在 `--` 之后，不经过 shell。 |
| `model` | string | 否 | 空 | `--model`。空则用配置或 CLI 默认模型。 |
| `cwd` | string | 否 | `WORKSPACE` | `-C` 工作根目录。 |
| `sandbox` | string | 否 | `auto` | `auto`、`bypass`、`read-only`、`workspace-write`、`danger-full-access`。 |
| `approval` | string | 否 | `never` | `untrusted`、`on-request`、`never`。使用绕过标志时忽略。 |
| `json_events` | boolean | 否 | true | `--json`，stdout 为 JSONL。 |
| `resume` | string | 否 | 空 | 会话 id，或 `last`。 |
| `resume_all` | boolean | 否 | false | 与 `resume=last` 一起使用 `--all`。 |
| `skip_git_repo_check` | boolean | 否 | true | `--skip-git-repo-check`。 |
| `ephemeral` | boolean | 否 | false | 不把会话落盘。 |
| `output_schema` | string | 否 | 空 | JSON Schema 文件路径。 |
| `agents_md` | string | 否 | 空 | 执行前写入 `cwd/AGENTS.md`。 |
| `timeout_s` | integer | 否 | 300 | 进程超时，1–3600 秒。 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 必填 | 默认 | 作用 |
|---|---|---|---|
| `OPENAI_API_KEY` | 否 | 空 | 内置 OpenAI provider 的密钥，或兼容 provider 的 `env_key`。 |
| `CODEX_API_KEY` | 否 | 空 | Codex 自己的 API key 变量。仅在没有自定义 `base_url` 时，从 `OPENAI_API_KEY` 复制。 |
| `ABX_LLM_API_KEY` | 否 | 空 | 为 `ABX_LLM_BASE_URL` 写配置时优先使用的密钥变量名。 |
| `OPENAI_BASE_URL` | 否 | 空 | OpenAI 兼容基址，例如 DashScope 的 `/compatible-mode/v1`。 |
| `ABX_LLM_BASE_URL` | 否 | 空 | 与 `OPENAI_BASE_URL` 相同。两者都设置时用这个。 |
| `CODEX_MODEL` | 否 | 空 | 写入 `config.toml` 的 `model`；`codex_exec` 未传 `model` 时使用。 |
| `CODEX_HOME` | 否 | `/home/user/.codex` | `config.toml` 和会话目录。 |
| `WORKSPACE` | 否 | `/home/user/workspace` | 默认 `cwd`。镜像里有一份起始 `AGENTS.md`。 |
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

在 `template launch` 前安全导出清单中声明为空的秘密变量，让应用启动时读取；不要写入镜像、YAML 或日志。

设置了 base URL 且 `config.toml` 不存在时，`codex_exec` 会创建它。`codex_config_write` 会覆盖该文件。Codex 0.162.1 不会发送 Chat Completions；`wire_api = "chat"` 是硬错误。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/workspace`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/codex.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。
