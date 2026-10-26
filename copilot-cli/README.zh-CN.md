# Copilot CLI

[English](README.md)。

## 做什么

运行固定版本的真实 GitHub Copilot CLI，通过显式 OpenAI 兼容 BYOK 端点调用模型。每次请求使用独立临时状态；修改文件必须传 allow_write=true。固定模型工具列表不包含 shell、委派或网页工具。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

原版 `@github/copilot@1.0.100` 及配套 Linux x86_64 原生包。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream license](UPSTREAM-LICENSE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

此模板使用 Copilot CLI 的 BYOK Chat Completions 模式，不使用 GitHub 托管 Copilot 模型。填写三个 `COPILOT_*` 配置，该路径不需要 GitHub 登录或 Token。示例通过 `allow_write=true` 显式允许项目写入。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export COPILOT_PROVIDER_API_KEY='<your-model-or-vendor-key>'
export COPILOT_PROVIDER_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export COPILOT_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//copilot-cli --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" copilot --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_write":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('copilot', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_write=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/copilot`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_write": true,
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

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| copilot_version | 无 | 实际二进制检查，{native_version:"1.0.100"}；不需要模型 key |
| copilot_setup_check | 无 | mode、base_url_set/api_key_set/model_set 布尔值、github_auth_required=false；无网络 |
| copilot | prompt:str 必填，1..32768UTF-8字节/无 NUL；cwd:str=""，解析符号链接后必须位于 WORKSPACE 内且存在；allow_write:bool=false；command_timeout:int=300，1..600秒 | stdout:str、stderr:str、exit_code:int、native_version:str |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 必需/默认 | 含义 |
| --- | --- | --- |
| COPILOT_PROVIDER_BASE_URL | 模型请求/空 | HTTPS 或回环 HTTP 开发端点；无 userinfo/query/fragment；最长2048字符 |
| COPILOT_PROVIDER_API_KEY | 模型请求/空 | 显式端点凭据，最长8192字符，禁止 CR/LF/NUL |
| COPILOT_MODEL | 模型请求/空 | 显式模型标识，最长200ASCII字符 |
| WORKSPACE | /home/user/app | cwd 根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

模型变量在服务启动时读取。固定 type=openai、wire API=completions、transport=http，prompt/output token 上限65536/4096。不转发 key-command、自定义 headers、bearer、GitHub token 或其他主机凭据。上游 secret-env 过滤和包装层替换保护配置的 key。子进程只继承 PATH/可选 CA 路径及独立 HOME/XDG/temp/state。停止自有进程组和带随机标记的脱离子进程后删除临时配置/缓存/日志，项目修改保留。自有云 sandbox 是恶意代码的最终边界。参见[运行环境](../docs/runtime-environment.md)和[官方 BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models)。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/copilot-cli.md)。

## 问题反馈

[Issue64](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/64)。缺少账号或模型能力时如实保留限制，不替换为无关凭据。

SDK/server 问题：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)；CLI 问题：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

包装代码为 Apache-2.0，见[仓库许可证](../LICENSE)。未修改的 GitHub Copilot CLI 遵守其独立[许可证](UPSTREAM-LICENSE.md)，镜像和安装包保留完整文本。再分发要求作为具有额外实质功能的应用/服务的一部分，禁止独立或作为主要产品分发。鉴权远程 API、文件传输和 sandbox 服务独立许可，不重新许可 CLI，也不授予 GitHub 服务访问权。
