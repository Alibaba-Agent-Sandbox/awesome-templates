# DeepAgents

[English](README.md).

## 做什么

运行真实DeepAgents0.7.25本地文件/shell后端及显式兼容OpenAI聊天模型。默认不开放工具；allow_tools=true仅启用ls/read_file/write_file/edit_file/glob/grep/execute/delete八项。关闭通用及显式子Agent，工具中没有task/委派。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 DeepAgents `0.7.25` 和 langchain-openai `1.7.2`，安装于固定依赖及哈希的 Python 环境。

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
export DEEPAGENTS_API_KEY='<your-model-or-vendor-key>'
export DEEPAGENTS_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export DEEPAGENTS_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//deepagents --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" deepagents --json-args '{"task":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('deepagents', task='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/deepagents`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "task": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
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

| Command | Parameters | Result |
| --- | --- | --- |
| deepagents_version | none | actual installed0.7.25 |
| deepagents_setup_check | none | installed/version/api_key_set/base_url_set/model_set flags; read-only |
| deepagents | task:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| DEEPAGENTS_API_KEY | model calls | empty | explicit compatible-provider credential |
| DEEPAGENTS_BASE_URL | model calls | empty | HTTP(S), no userinfo/query/fragment |
| DEEPAGENTS_MODEL | model calls | empty | explicit model identifier |
| DEEPAGENTS_PYTHON | no | /opt/deepagents/bin/python | exact native dependency environment, version checked |
| WORKSPACE | no | /home/user/app | existing owned project directory |
| ABX_SERVER_TOKEN | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

显式模型配置保留在私有stdin，不作为环境传入生成的shell。运行时仅PATH/可选CA、私有HOME/XDG、关闭LangSmith追踪；LocalShellBackend只接收PATH/HOME/locale及随机非秘密进程归属标记，不继承模型/云/GitHub/服务密钥。不加载skills/memory/profile文件。虚拟文件路径映射至cwd，但shell仍有沙箱用户全部权限，该映射不是shell隔离边界。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/deepagents.md)。

## 问题反馈

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码为[Apache-2.0](../LICENSE)。DeepAgents及langchain-openai为MIT，保留[DeepAgents原许可](upstream-LICENSE)与[集成库原许可](langchain-openai-LICENSE)。其余哈希固定依赖按各自许可证保留pip安装声明，不能统一重标Apache-2.0。
