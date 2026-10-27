# agents-cli

通过受限的本地 Agents HTTP API 调用固定版本的 Codex 和 Qwen Code。

## 做什么

安装 `@openai/codex@0.162.1`、`@qwen-code/qwen-code@0.23.0`，提供版本检查和六个
会话/运行时接口。客户端创建会话、提交消息并轮询输出。响应头
`X-Agent-Sandbox-Local: 1` 表示本地实现，不表示 OpenAI 托管 Agents 服务。

直接运行和模板配置的 canonical `serve` 启动方式都加载
[server-policy.json](./server-policy.json)。通用 shell、文件、进程、模型列表以及
其余 Agents 接口关闭。关闭 HTTP shell/文件接口不会移除上游 CLI 的工作区工具权限。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

Codex CLI `0.162.1`、Qwen Code `0.23.0`、Node.js `24.16.0` 及受限的本地 Agents API 策略。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

可选择 `qwen-code`（Chat Completions）或 `codex`（Responses）适配器。启动前显式配置 OPENAI_API_KEY、OPENAI_BASE_URL、OPENAI_MODEL，三者来自自己有权限的同一个模型服务。API Key 流程无需 OAuth 登录，也不继承本机账号。Codex 会话前调用 `agents_configure_codex`：将启动时的 endpoint 写入原生 Responses profile，密钥只保存环境变量名引用，关闭 WebSockets；不覆盖其他已有配置。Qwen 直接使用启动时的 Chat 配置。同一实例使用两个适配器时，上游需要同时支持两种协议，否则分别配置并启动实例。


先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。



所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_API_KEY='<your-model-or-vendor-key>'
export OPENAI_BASE_URL='<your-model-api-base-including-v1-if-required>'
export OPENAI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//agents-cli --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

命名命令提供版本诊断和显式 Codex 配置准备；真实编码使用后面的会话 API，配置完成或版本响应本身都不是编码结果。

```bash
abx run "$SANDBOX_ID" agents_version
# For Codex sessions, explicitly prepare the native Responses profile:
abx run "$SANDBOX_ID" agents_configure_codex
# Select the adapter for the complete Python example:
export AGENTS_ADAPTER=qwen-code
# Or: export AGENTS_ADAPTER=codex
```

任务要求在 `/home/user/workspace` 写出 `generated_hello.py` 和 `GENERATED_REPORT.md`。示例显式开放所需的编辑/工具权限，只在自己拥有的可丢弃沙箱中使用。下面的 SDK 和 HTTP 是同一任务的替代调用方式，选择一种即可。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

连接 launch 已启动的应用，并通过 SDK 解析真实网关地址；以下 Python 发起同一个编码任务，再有界轮询会话输出。应用的受限策略没有普通文件/shell HTTP 路由，最终产物通过提供方的 `abx exec`/`download` 检查。

```python
import asyncio
import os
import time
from pathlib import Path
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        occupied = {key.lower() for key in headers}
        token = os.environ["ABX_SERVER_TOKEN"]
        if "authorization" not in occupied:
            headers["Authorization"] = "Bearer " + token
        if "x-access-token" not in occupied:
            headers["X-Access-Token"] = token
        if {"authorization", "x-access-token"}.issubset(occupied):
            raise ValueError("Gateway occupies both application authentication headers")
        base = httpx.URL(endpoint)
        def url(path):
            return base.copy_with(path=base.path.rstrip("/") + path)
        async with httpx.AsyncClient(headers=headers, timeout=60) as http:
            adapter = os.environ.get("AGENTS_ADAPTER", "qwen-code")
            if adapter not in ("qwen-code", "codex"):
                raise ValueError("AGENTS_ADAPTER must be qwen-code or codex")
            if adapter == "codex":
                response = await http.post(url("/commands/agents_configure_codex"), json={})
                response.raise_for_status()
            response = await http.post(url("/v1/agents/sessions"), json={
                "adapter": adapter,
                "agent": {"model": os.environ["OPENAI_MODEL"], "permissions": "full_access"},
                "environment": {"type": "self_hosted",
                                "workspace_directory": "/home/user/workspace"},
            })
            response.raise_for_status()
            session = response.json()["id"]
            path = "/v1/agents/sessions/" + session
            response = await http.post(url(path + "/events"), json={
                "events": [{"type": "agent.session.input.message", "input": [
                    {"role": "user", "content": [{"type": "input_text", "text":
                     "Create generated_hello.py that prints exactly Hello from the sandbox, "
                     "and GENERATED_REPORT.md explaining the program. Preserve unrelated files."}]}]}]
            })
            response.raise_for_status()
            deadline = time.monotonic() + 420
            while time.monotonic() < deadline:
                response = await http.get(url(path))
                response.raise_for_status()
                state = response.json()
                if state.get("error") or state.get("status") == "failed":
                    raise RuntimeError("Agent session failed; inspect private diagnostics")
                response = await http.get(url(path + "/items"))
                response.raise_for_status()
                items = response.json()["data"]
                if state.get("status") == "idle" and items:
                    print(items)
                    Path("generated_hello.py").write_bytes(await sb.files.read_bytes("/home/user/workspace/generated_hello.py"))
                    Path("GENERATED_REPORT.md").write_bytes(await sb.files.read_bytes("/home/user/workspace/GENERATED_REPORT.md"))
                    break
                await asyncio.sleep(1)
            else:
                raise TimeoutError("Destroy your owned sandbox to stop the task")
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

命名命令的只读诊断是 `POST /commands/agents_version`，请求体 `{}`，响应 `{"result":"codex 0.162.1; qwen-code 0.23.0"}`。实际编码使用下面的 Agents 会话 API；它不是虚构的编码命名命令。

请求头设置 `Content-Type: application/json`。

按照[直接 HTTP 连接流程](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 9000 endpoint，保留网关 headers、URL path/query，并添加独立应用 token。下面是同一个任务的完整会话请求：

1. `POST /v1/agents/sessions`:

```json
{
  "adapter": "qwen-code",
  "agent": {
    "model": "<same-model-as-OPENAI_MODEL>",
    "permissions": "full_access"
  },
  "environment": {
    "type": "self_hosted",
    "workspace_directory": "/home/user/workspace"
  }
}
```

返回 `200`，保存响应 `id` 为 `<session-id>`。

2. `POST /v1/agents/sessions/<session-id>/events`:

```json
{
  "events": [
    {
      "type": "agent.session.input.message",
      "input": [
        {
          "role": "user",
          "content": [
            {
              "type": "input_text",
              "text": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files."
            }
          ]
        }
      ]
    }
  ]
}
```

返回 `202` 表示入队，尚未完成。轮询 `GET /v1/agents/sessions/<session-id>` 及 `GET /v1/agents/sessions/<session-id>/items?limit=100&order=asc`，最多等待 420 秒；发现 `error`/`failed` 立即停止。输出记录出现且状态回到 `idle` 后，仍应按下方命令检查真实产物；`idle` 本身不是文件成功保证。会话不支持取消/删除路由，结束或超时需销毁自己的沙箱。

### 导出产物与清理

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

程序预期输出 `Hello from the sandbox`。先读取产物并检查再使用；模型回答成功不代表文件一定存在。文件不会自动回写模板或你的本机，释放沙箱前必须导出。

`close()`/`aclose()` 仅关闭客户端连接，不释放沙箱。launch 日志中的已构建模板和镜像可能保留用于复用，不再需要时仅删除自己创建的那些资源。

### 继续会话与切换模型

向同一 session ID 再发送 input-message event，可以恢复原生对话；等待新的 output items 并回到 idle 后，独立检查实际文件，idle 本身不是成功证明。新 ID 用于独立对话。在同一 endpoint/Key 下切换有权限的模型时，为新 session 指定新的 agent.model。更换 endpoint 或 Key 时，修改启动变量并 launch 新实例，之后在本机 export 不会重配旧应用。已有不同 Codex 配置会保留，应该在 launch 前选择新的 CODEX_HOME，不覆盖旧配置。

HTTP 使用 Codex 前，先 `POST /commands/agents_configure_codex`，body 为 `{}`；实际返回 `{"result":{"configured":true,"wire_api":"responses","credential_written":false}}`。会话创建 JSON 的 adapter 改为 codex，其余相同；模型 ID 必须匹配所选协议。

## 命令参考

| 命令 | 参数 | 返回 | 执行 |
|---|---|---|---|
| `agents_configure_codex` | 无；`{}` | `{configured:true,wire_api:"responses",credential_written:false}` | 显式创建 CODEX_HOME/config.toml，权限0600；相同配置幂等，不同已有配置或符号链接拒绝覆盖。使用启动 endpoint 与密钥环境变量引用，不调用模型或登录。 |
| `agents_version` | 无，`{}` | 缓冲字符串 | 真实 `codex --version` 和 `qwen --version`，各最多 20 秒；缺 CLI 或版本不符返回错误，不输出原始 CLI 内容 |

| 开放接口 | 用途 |
|---|---|
| `GET /commands`、`POST /commands/agents_version` | 发现/执行版本检查 |
| `POST /v1/agents/sessions` | 创建会话；`adapter` 支持 `codex`、`qwen-code`，默认 Codex |
| `GET /v1/agents/sessions`、`GET /v1/agents/sessions/{id}` | 列表/重连 |
| `POST /v1/agents/sessions/{id}/events` | 消息入队 |
| `GET /v1/agents/sessions/{id}/items` | 轮询输出 |
| `GET /v1/agents/runtimes` | 检查声明、实现及已安装的运行时 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 必需 | 用途 |
|---|---|---|
| `ABX_SERVER_TOKEN` | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `OPENAI_API_KEY` | 兼容模型调用需要 | Qwen 及兼容 Codex 配置的模型凭据，清单中为空 |
| `CODEX_API_KEY` | Codex 可选替代项 | 清单中为空；实际支持取决于上游及提供方配置 |
| `OPENAI_BASE_URL`、`OPENAI_MODEL` | 取决于提供方 | 显式模型端点和模型 ID；Qwen 使用 Chat Completions，Codex 准备 profile 后使用 Responses |
| `ABX_AGENTS_STATE_DIR` | 否 | 原生本地会话存储目录 `/home/user/.agent-sandbox/agents`，随实例删除 |
| `CODEX_HOME` | 否 | Codex 状态目录，默认 `/home/user/.codex` |
| `WORKSPACE` | 否 | `/home/user/workspace`；会话请求应显式指定目标目录 |
| `ABX_SERVER_POLICY_FILE` | 镜像已设置 | 随附策略文件路径；canonical start_cmd 还显式传入 `--policy` |

修改策略会改变 HTTP 接口范围；本模板契约基于随附 allowlist。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/workspace`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/agents-cli.md)。

## 问题反馈

模板和策略集成：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
运行时/API：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。上游 CLI 保留各自许可证。
