# Pi

## 做什么

在阿里云沙箱基础镜像内运行[官方 Pi 编程 CLI](https://github.com/earendil-works/pi)。本模板提供一次性的 print 模式任务，使用 OpenAI 兼容模型端点；它是独立模板，不依赖 E2B 模板注册。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 `@earendil-works/pi-coding-agent@1.3.0`、Node.js `24.16.0`、fd `10.5.0` 和 ripgrep `15.2.0`。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

此无交互路径使用下方三个显式模型配置，不启动浏览器/OAuth 登录。endpoint 必须支持兼容 OpenAI 的 Chat Completions 及工具调用。从对应服务商取得 Key 和准确模型 ID，云沙箱 API Key 是另一种凭据。下方以百炼公共兼容接入点为例，必须使用同地域有权限的 Key 和模型；换服务时三个值一起替换。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export PI_API_KEY='<your-model-or-vendor-key>'
export PI_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export PI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//pi --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" pi --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
```

任务要求在 `/home/user/app` 写出 `generated_hello.py` 和 `GENERATED_REPORT.md`。示例显式开放所需的编辑/工具权限，只在自己拥有的可丢弃沙箱中使用。下面的 SDK 和 HTTP 是同一任务的替代调用方式，选择一种即可。

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
            print(await client.commands.run('pi', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/pi`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_tools": true,
  "cwd": "/home/user/app",
  "command_timeout": 300
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 420 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

### 导出产物与清理

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/app/generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

程序预期输出 `Hello from the sandbox`。先读取产物并检查再使用；模型回答成功不代表文件一定存在。文件不会自动回写模板或你的本机，释放沙箱前必须导出。

`close()`/`aclose()` 仅关闭客户端连接，不释放沙箱。launch 日志中的已构建模板和镜像可能保留用于复用，不再需要时仅删除自己创建的那些资源。

## 命令参考

| 命令 | 参数 | 返回值 |
|---|---|---|
| pi_version | 无 | 已安装版本字符串。 |
| pi_tools_check | 无 | 在临时文件上真正离线执行官方 read/find/grep/ls，返回 `read/find/grep/ls OK`。 |
| pi_setup_check | 无 | 安装状态、版本、固定版本、key/端点/模型是否配置的布尔值、工作目录；不返回凭证或端点值。 |
| pi | prompt: string 必填；cwd: string = ""；allow_tools: boolean = false；command_timeout: integer = 600 | 脱敏后的缓冲文本；期限范围 1–1800 秒。 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

`PI_BASE_URL` 是兼容 chat-completions 的端点，`PI_MODEL` 是模型 ID，`PI_API_KEY` 是密钥；三项必须齐全。拒绝含内嵌凭证、query 或 fragment 的 URL，不启动交互登录。metadata 内凭证值为空。

每次任务在私有临时目录生成 `models.json`，仅写上游支持的 `$PI_API_KEY` 引用；成功、失败或 Python 取消后均删除。不会复用用户配置或持久会话。`--offline` 关闭启动时的模型目录刷新等自动网络操作，所请求的模型调用仍访问配置端点。扩展、MCP、skills、上下文文件、主题、提示词模板均关闭。

镜像明确安装固定版本的 `fd` 与 `rg`，离线模式不依赖运行时下载工具。`pi_tools_check` 无需模型就运行四个真实默认工具，并纳入镜像/云端 smoke。

默认工具严格为 `read,grep,find,ls`。`allow_tools=true` 明确加入 `edit,write,bash`，允许模型在当前沙箱用户可访问范围内修改文件、执行代码。Pi 的 `--no-approve` 仅忽略需要信任的项目配置，不限制工具；默认工具由白名单控制，真正的隔离边界仍是沙箱。不要让不可信调用方直接使用可写模型执行。

Linux 下每次调用拥有独立进程组，并发排空 stdout/stderr；成功、错误、超时或 Python 取消时先清理进程组，再回收 leader。自行创建新 session 的子进程会逃离此进程组边界。HTTP 断开不代表取消。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/pi.md)。

## 问题反馈

[模板 Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41)。SDK/server 问题在 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题在 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。请提供脱敏版本和复现步骤。

## 许可证

模板代码采用 Apache-2.0，Pi 上游采用 MIT；fd 官方归档的 LICENSE-MIT、LICENSE-APACHE，以及 ripgrep 的 LICENSE-MIT、UNLICENSE、COPYING（MIT/Unlicense）随完整解包目录保留在 `/opt/pi-tools/`，npm 依赖也保留各自许可文件。[LICENSE](../LICENSE)。
