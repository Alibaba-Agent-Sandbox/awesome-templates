# Qwen Code

[English](README.md)

## 做什么

通过类型化命名命令运行固定版本 Qwen Code 无头编码 CLI，并提供安装诊断和 Python 脚本执行命令。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 `@qwen-code/qwen-code@0.23.0` 和 Node.js `24.16.0`；CLI 不需要额外的 OpenAI/DashScope Python 包。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

此路径使用兼容 OpenAI 的 API Key，禁用交互 OAuth。在 launch 前设置 OPENAI_API_KEY（或 DASHSCOPE_API_KEY 后备值）、OPENAI_BASE_URL、OPENAI_MODEL。manifest 的空配置项会注入这些 host 值；未提供 endpoint/模型时，运行时保留 https://dashscope.aliyuncs.com/compatible-mode/v1 和 qwen3-coder-plus。Key、地域、endpoint 和模型权限须匹配。qwen 的 model 参数可覆盖单次模型。需要换启动配置时创建新实例，无需修改本地模板。

使用可选的默认百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_API_KEY='<your-model-or-vendor-key>'
export OPENAI_BASE_URL='<your-chat-completions-base-url>'
export OPENAI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//qwen-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" qwen --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","yolo":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('qwen', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', yolo=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/qwen`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "yolo": true,
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

| 命令 | 参数 | 结果及上游调用 |
| --- | --- | --- |
| `qwen` | `prompt: str` 必填非空；`max_turns: int=100`（1–1000）；`model: str=""` 使用 `OPENAI_MODEL`；`cwd: str=""` 使用工作区；`command_timeout: int=600`（1–1800 秒）；`yolo: bool=false` | 字符串；`qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`，按需加 `--model MODEL`、`--yolo` |
| `qwen_version` | 无 | 真实 `qwen --version` 输出，不需密钥 |
| `qwen_setup_check` | 无 | 安装/版本/pin、密钥/模型/base URL 是否配置、设置文件存在与 JSON 有效性；不返回设置内容，不写文件 |
| `run` | `script: str="main.py"` | 返回 Python stdout，执行期限 120 秒 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 变量 | 含义 |
| --- | --- |
| `OPENAI_API_KEY` | 编码任务所需的主要模型密钥；版本和配置检查不需要 |
| `DASHSCOPE_API_KEY` | 主要密钥为空时的备选值，仅在子进程映射 |
| `OPENAI_BASE_URL` | 默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`，其他兼容端点可在启动前 export OPENAI_BASE_URL |
| `OPENAI_MODEL` | 默认 `qwen3-coder-plus`，命令参数 `model` 优先 |
| `WORKSPACE` | 默认 `/home/user/app` |
| `ABX_SERVER_TOKEN` | 启动 模板启动前必填；独立于模型和网关凭据 |

诊断只读 `~/.qwen/settings.json` 和 `<workspace>/.qwen/settings.json`，保留内容与权限；正常编码可能产生上游运行缓存。兼容约定见[上游模型提供方配置](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md)和[无头模式](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md)。请确认账号和模型支持所需工具调用，不把 API 日志中的秘密写入公开产物。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/qwen-code.md)。

## 问题反馈

模板任务跟踪于 [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26)。SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，附脱敏命令、版本及实际未通过门禁。

## 许可证

模板使用 Apache-2.0。Qwen Code 保留[上游许可](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE)。
