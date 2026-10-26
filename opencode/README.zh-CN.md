# OpenCode 沙箱

[English](README.md)

在隔离工作目录中运行 OpenCode 编码任务，通过 CLI、Python 或 HTTP 调用，并下载生成的文件。

## 做什么

`opencode_run` 以非交互方式调用沙箱内的 OpenCode，完成代码编写、修改与重构，返回文本、JSON 事件和会话 ID。后续传入该 ID 可以继续同一任务。`opencode_serve_start` 可按需启动 OpenCode 自身的 HTTP 服务，普通编码任务不需要额外启动它。

## 技术栈

- OpenCode `opencode-ai@1.19.0`、Git、ripgrep。
- 平台基础镜像提供 Python 3.13、Node.js 20 和 Bash。
- 模板命令应用使用 9000 端口；可选 OpenCode 原生服务使用 4096。
- 默认非 root 用户为 `user`；模板文件位于 `/home/user/app`，任务文件写入自己创建的工作目录。

## 解决的问题

无需在本机安装编码 CLI，即可让 Agent 修改项目、生成可运行文件，并在释放沙箱前导出产物。下面的例子在 `/home/user/workspace` 创建 `hello.py`，运行后打印 `Hello from OpenCode`。

## 快速开始（CLI）

先按[安装与平台配置](../docs/using-templates.zh-CN.md#安装)安装工具、配置沙箱平台。极速版源码构建还需要 Docker、ACR 和对应平台凭据。平台 API Key 与模型服务 API Key 是两种不同的凭据。

在**启动模板之前**设置应用配置。下面使用百炼国内主站的 OpenAI 兼容端点；请使用该端点接受的模型 API Key，不要填沙箱平台 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="<独立的应用访问令牌>"
export ABX_LLM_API_KEY="<模型服务APIKey>"
export ABX_LLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export ABX_HTTP_TIMEOUT=660
abx template launch Alibaba-Agent-Sandbox/awesome-templates//opencode --sandbox-timeout 1800 --yes
```

把返回的沙箱 ID 填入下一条变量。如果使用 OpenSandbox，先完成该平台配置，并在后续所有示例中统一使用 `ABX_PROVIDER=opensandbox`。

```bash
export ABX_SANDBOX_ID="<返回的沙箱ID>"
abx exec "$ABX_SANDBOX_ID" -- mkdir -p /home/user/workspace
abx run "$ABX_SANDBOX_ID" opencode_version
abx run "$ABX_SANDBOX_ID" opencode_setup_check
abx run "$ABX_SANDBOX_ID" opencode_run --json-args '{"prompt":"在当前目录创建 hello.py，运行后打印 Hello from OpenCode，然后运行它。","model":"dashscope/qwen3.8-flash","cwd":"/home/user/workspace"}'
abx download "$ABX_SANDBOX_ID" /home/user/workspace/hello.py ./hello.py
```

任务返回 `text`、`stdout`、`session_id`、`model`、`agent`、`cwd`。模型说明文字每次可能不同；下载后的 Python 文件运行时应打印 `Hello from OpenCode`。CLI、SDK、HTTP 是同一任务的三种调用方式，任选一种即可，无需为它们分别创建沙箱。

## 快速开始（Python SDK）

在自己的虚拟环境安装 `agent-sandbox-client==0.4.0a6`。保留上面的环境变量，连接**已经由 CLI 启动的应用**。将以下完整代码保存为 `quickstart.py`：

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        await sb.commands.run("mkdir -p /home/user/workspace")
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            result = await client.commands.run(
                "opencode_run",
                prompt="在当前目录创建 hello.py，运行后打印 Hello from OpenCode，然后运行它。",
                model="dashscope/qwen3.8-flash",
                cwd="/home/user/workspace",
            )
            print(result["text"])
            Path("hello.py").write_bytes(
                await sb.files.read_bytes("/home/user/workspace/hello.py")
            )
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

执行 `python quickstart.py`。关闭客户端不会删除沙箱；导出所需文件后按下方步骤清理。`sb.commands.run` 执行进程命令，`client.commands.run` 调用模板注册的命名命令。

## 快速开始（HTTP POST）

请求头设置 `Content-Type: application/json`。

请求 `POST /commands/opencode_run`，JSON 参数直接放在请求体中，不额外套 `arguments`：

```json
{"prompt":"在当前目录创建 hello.py，运行后打印 Hello from OpenCode，然后运行它。","model":"dashscope/qwen3.8-flash","cwd":"/home/user/workspace"}
```

[完整 HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)说明如何解析提供方端点、保留网关头及 URL 路径／查询参数，再添加应用令牌。将示例的命令路径换成 `/commands/opencode_run`，请求体换成上面的对象，并设置 `httpx.AsyncClient(timeout=660)`。先执行上面的 CLI 命令创建工作目录。

响应形状为 `{"result": {"text": "...", "stdout": "...", "session_id": "...", "model": "dashscope/qwen3.8-flash", "agent": "", "cwd": "/home/user/workspace"}}`。它是等待完成后返回的 JSON，不是逐 token 流。参数错误、认证失败和命令执行失败会返回错误；HTTP 客户端断开不代表模型子进程一定取消。

## 命令参考

| 命令 | 参数 | 返回 | 上游 |
|---|---|---|---|
| `opencode_run` | 见下表 | 对象 | `opencode run --pure --format json --auto ...` |
| `opencode_version` | 无 | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | 无 | `"ok"` | `opencode --version`，并读取 `opencode.json` |
| `opencode_serve_start` | `port` 整数，默认 `4096`；`hostname` 字符串，默认 `0.0.0.0` | 对象 | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | 无 | 对象 | 本机 `GET /global/health` |
| `opencode_serve_stop` | 无 | `"stopped"` | 向本模板启动的进程发 `SIGTERM` |

`opencode_run` 的参数：

| 参数 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `prompt` | 字符串 | 是 | | `--` 后的位置参数。不拼进 shell 字符串。 |
| `model` | 字符串 | 否 | `OPENCODE_MODEL`，否则 `dashscope/qwen3.8-flash` | `--model`，格式 `provider/model`。 |
| `agent` | 字符串 | 否 | 空（CLI 主代理 `build`） | 非空时传 `--agent`。 |
| `session` | 字符串 | 否 | 空 | `--session`，继续该会话 id。 |
| `continue_session` | 布尔 | 否 | `false` | `--continue`（上一个会话）。传 JSON 布尔值。 |
| `cwd` | 字符串 | 否 | 镜像中 `/home/user/app`，本地为模块目录 | `--dir` 以及子进程工作目录。必须是已存在的目录。 |

`opencode_run` 的返回：

| 字段 | 含义 |
|---|---|
| `text` | JSON 事件里 `type: text` 片段拼起来的文本。 |
| `stdout` | 已脱敏的 stdout，一行一个 JSON 事件。 |
| `session_id` | 这些事件里的 `sessionID`，没有则为空。 |
| `model` | 传给 `--model` 的选择器。 |
| `agent` | 传给 `--agent` 的名字，没有则为空。 |
| `cwd` | 传给 `--dir` 的目录。 |

缺少 `prompt` 时 HTTP 400。CLI 非零退出时 HTTP 500，正文是 `{"error","type":"RuntimeError"}`。消息里不含密钥。超时 600 秒。标准输入是 `/dev/null`。

`opencode_serve_start` 返回 `running`、`port`、`hostname`、`pid` 和 `healthy`。它会等到 `GET http://127.0.0.1:<port>/global/health` 返回 `{"healthy": true, "version": "1.19.0"}`。通过 `await sb.network.resolve(port)` 获取对外端点及网关头；localhost 地址仅供内部使用。同一端口与 hostname 再次启动会返回当前状态。start/status/stop 全程由进程内锁串行处理；stop 仅允许终止本解释器持有的 Popen 子进程，并校验进程组身份，不读取旧 PID 文件。命令服务器重启后不会接管旧 serve 进程；需要回收 sandbox 清理这类进程。

## 配置

| 设置 | 必填／默认值 | 配置方法 |
|---|---|---|
| `ABX_LLM_API_KEY` | 调用 `dashscope/*` 必填 | 在本机启动模板前导出，应用进程启动时读取。 |
| `ABX_LLM_BASE_URL` | 调用 `dashscope/*` 必填 | 完整 OpenAI 兼容端点，包含 `/v1`；见上面的可复制示例。Key、地域及账号权限应与端点匹配。 |
| 命令参数 `model` | 可选，默认 `dashscope/qwen3.8-flash` | 填 `dashscope/<模型ID>`；模板会为该次调用补入配置里尚未列出的 DashScope 模型 ID。 |
| `ABX_SERVER_TOKEN` | 源码启动前必填 | 独立应用访问令牌，CLI／SDK／HTTP 调用方使用同一个值。 |
| `OPENCODE_API_KEY` | 仅 `opencode/*` Zen 模型需要 | 对应服务的模型凭据，不能代替百炼 Key。 |
| `OPENCODE_SERVER_PASSWORD` | 可选 | 可选 `opencode serve` 服务的 Basic Auth 密码；暴露该服务时在启动前设置。 |
| `ABX_HTTP_TIMEOUT` | 示例设为 660 秒 | CLI 等待 HTTP 的时长；编码子进程本身上限为 600 秒。SDK 和直接 HTTP 客户端分别设置等待时间。 |

**如何登录：** 上面的百炼路径使用 API Key，无需网页登录。你的本机 OpenCode 登录态和配置不会自动复制进沙箱。模板自带 `/home/user/app/opencode.json`，已把自定义供应商 `dashscope` 的端点与 Key 映射到 `ABX_LLM_BASE_URL`、`ABX_LLM_API_KEY`，此路径无需修改镜像或执行 `opencode auth login`。OpenCode 原生全局配置目录是 `~/.config/opencode`，认证／会话数据位于 `~/.local/share/opencode`，与沙箱平台账号不同。

**更换端点或模型：** 继续使用这个自定义兼容供应商的 `dashscope/` 前缀，在启动前修改 `ABX_LLM_BASE_URL`，调用时通过 `model` 指定端点上可用的模型 ID。示例中的模型名称不代表你的账号一定有权限。模板清单已固定 `OPENCODE_MODEL` 的默认值，在 CLI 0.5.6 中只导出同名主机变量不能覆盖它，应使用命令参数选择模型。

**其他上游供应商：** OpenCode 支持其他供应商配置，但模板不会把所有凭据自动转换成 `ABX_LLM_*`。保留现有 DashScope 配置，按 [OpenCode 配置文档](https://opencode.ai/docs/config/)与[供应商文档](https://opencode.ai/docs/providers/)添加相应配置，再指定 `provider/model`。配置文件或登录态必须在该沙箱内准备，不能假设继承主机凭据；非 OpenAI 兼容接口应采用对应供应商支持的配置。

启动后修改本机 export 不会重配既有应用。需要新模型配置时重新启动实例，不要另起第二个模板命令服务。

## 资源

清单请求 2 vCPU、2048 MB 内存；磁盘容量与最长实例寿命由所选平台决定。模型服务需要出网，可能另行计费。4096 端口仅在调用 `opencode_serve_start` 后使用，应通过提供方解析端点，并保留网关和 OpenCode 两层认证。

模板调用固定启用 `--auto`，自动批准 OpenCode 工具执行。`cwd` 选择项目目录，不是文件系统权限边界；模型可执行命令并修改 `user` 可写的文件。只放入任务需要的凭据与文件。

OpenCode 以命令的 `cwd` 为项目目录。示例显式创建工作目录，避免修改模板应用文件。释放前导出代码、会话数据及其他所需产物；沙箱内修改不会更新原始模板。

```bash
abx kill "$ABX_SANDBOX_ID"
```

不再复用准备的模板／镜像时，还应根据启动返回的记录清理本次确切拥有的资源，见[资源清理](../docs/using-templates.zh-CN.md#clisdk-与-http)。不要把 Key 或登录态写进可复用镜像。

## 贡献

模板编写参见 [CONTRIBUTING](../CONTRIBUTING.zh-CN.md)及 [OpenCode 设计说明](../docs/design/opencode.md)。

## 问题反馈

模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端／服务端问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。请移除 Key 与私有项目数据。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。OpenCode 通过固定版本的上游包安装，保留其上游许可证。
