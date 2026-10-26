# grok

## 做什么

运行真正的 xAI 官方 `@xai-official/grok@1.0.62` 无头编码 CLI。Rust 原生程序经 --prompt-file /dev/stdin 读取匿名 stdin，使用真实工具修改项目，返回缓冲 JSON 与实际退出码。本模板是官方 Grok Build；兼容模型通过不代表 xAI 托管模型或订阅已验证。

[Official xAI source snapshot](https://github.com/xai-org/grok-build/tree/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8), [native custom models](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md), [headless protocol](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md).

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 Grok Build `1.0.62`、其 Linux x86_64 Rust 原生运行时和 Node.js `24.16.0`。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream license](UPSTREAM-LICENSE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

此包装显式配置兼容 OpenAI 的 Chat Completions 模型，不需要 xAI 订阅或登录，不会自动切换到托管 Grok 模型。原生 Agent 可使用沙箱用户权限执行文件和 shell 工具。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export GROK_MODEL_API_KEY='<your-model-or-vendor-key>'
export GROK_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export GROK_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//grok --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" grok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/workspace","command_timeout":300}'
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
            print(await client.commands.run('grok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/workspace', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/grok`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "cwd": "/home/user/workspace",
  "command_timeout": 300
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

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| grok_version | 无 | 实际固定原生版本 `{"native_version":"1.0.62"}`；不调用模型／登录 |
| grok_setup_check | 无 | mode=openai-compatible-byok、base_url_set／api_key_set／model_set 布尔值、xai_account_required:false；不联网／返回秘密 |
| grok | prompt：必填非空字符串，1..32768 UTF-8字节且无 NUL；cwd：可选字符串，默认空，最多4096字节，解析后必须为 WORKSPACE 内现存目录；command_timeout：整数1..600秒，默认300 | `{stdout:string,stderr:string,exit_code:int,native_version:"1.0.62"}`；原生工具执行及工作区文件修改 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 必需／默认 | 含义 |
| --- | --- | --- |
| GROK_MODEL_API_KEY | 模型必需，空 | 授权兼容端点密钥，仅作为原生 ABX_GROK_MODEL_KEY 传递 |
| GROK_MODEL_BASE_URL | 模型必需，空 | 显式 HTTPS API base；仅固定本地地址可用 HTTP；无用户信息／query／fragment；最多2048字符 |
| GROK_MODEL | 模型必需，空 | 实际模型标识，最多200个允许字符 |
| WORKSPACE | `/home/user/workspace` | 已存在工作区根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在 commands.py 加载时捕获。私有0600 config.toml 仅含显式 model/base 与 env_key="ABX_GROK_MODEL_KEY"，不保存密钥值，固定 chat_completions 后端。每次调用使用并删除私有 GROK_HOME/HOME/cache/session；关闭更新、leader、遥测/trace、记忆及后台 workflow。原生 shell_environment_policy 继承 core 并排除秘密变量；不转发调用者云/GitHub/厂商账号凭据。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/workspace`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。 当前固定安装支持 Linux x86_64。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/grok.md)。

## 问题反馈

[模板 Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 和 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不发布凭据／私有日志。

## 许可证

包装器与官方 Grok Build 均为 Apache-2.0。[仓库许可](../LICENSE)、[上游许可](UPSTREAM-LICENSE.md)、[官方二进制第三方声明](THIRD_PARTY_NOTICES.md)。保留原始依赖声明，不提供托管账号或商标权利。
