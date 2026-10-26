# devin

[English](README.md)。

## 做什么

在自有一次性沙箱中，通过类型明确且有界的命名命令调用Cognition原版Devin CLI3000.11.92。推理与工具由原版负责；没有替代规划器或兼容模型兜底。自动工具必须显式allow_unsafe_tools=True。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

原版 Devin CLI `3000.11.92` Linux x86_64 发行包，保留自带二进制和声明。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

真正的编码需要在可信机器上使用原版 Devin CLI 登录后得到的原版 `credentials.toml`，账号设置见 [Devin CLI](https://docs.devin.ai/work-with-devin/devin-cli)。没有自创 `DEVIN_API_KEY` 或通用模型 endpoint。`DEVIN_CREDENTIALS_FILE` 必须指向沙箱内部、`WORKSPACE` 之外的私有文件；host 本地路径不会自动上传。文件在任务调用时读取，可按下方流程在 launch 后上传。没有授权账号文件时，setup/version 可用，编码会返回原版登录拒绝。

先按上游指南在可信机器安装原版 CLI，运行 `devin auth login`，账号的 Devin Enterprise 角色须允许 CLI 访问。[官方认证说明](https://docs.devin.ai/cli/enterprise/devin-auth)规定 macOS/Linux 文件位于 `$XDG_DATA_HOME/devin/credentials.toml`；未设置 XDG_DATA_HOME 时为 `~/.local/share/devin/credentials.toml`；Windows 为 `%APPDATA%\devin\credentials.toml`。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DEVIN_CREDENTIALS_FILE='/home/user/devin-private/credentials.toml'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//devin --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

在可信机器完成原版登录后，把你自己实际生成的 credentials.toml 路径填入下面占位符；不要打印文件内容：

```bash
abx exec "$SANDBOX_ID" -- mkdir -p /home/user/devin-private
abx exec "$SANDBOX_ID" -- chmod 700 /home/user/devin-private
abx upload "$SANDBOX_ID" "<local-credentials.toml>" /home/user/devin-private/credentials.toml
abx exec "$SANDBOX_ID" -- chmod 600 /home/user/devin-private/credentials.toml
```

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" devin --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('devin', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/devin`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_unsafe_tools": true,
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

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| devin_version | 无 | 原文件身份校验及真实--version字符串 |
| devin_native_check | 无 | 原版--help；original_native/headless_print/private_config/explicit_permission/workspace_trust_control布尔字段 |
| devin_setup_check | 无 | mode/installed/pinned_version/credentials_file_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态 |
| devin | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原版最终stdout；明确授权后可执行文件／工具动作 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。 模型调用串行执行；并发请求会返回 busy。清理可能延长响应时间，示例为此保留 HTTP 等待余量。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| DEVIN_CREDENTIALS_FILE | 空；诊断／错误路径可缺，账号任务需要 | 包装层变量，模块导入捕获路径；绝对路径、WORKSPACE外、root或当前UID持有的普通非符号链接、无组／其他权限、1..65536字节合法UTF8TOML |
| WORKSPACE | /home/user/app | 导入捕获的项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

缺文件时让原版print明确返回登录拒绝；不执行交互登录、不虚构DEVIN_API_KEY、不借用其他模型／云密钥。子进程只收到最小私有状态环境，不继承操作端密钥或源凭证路径。返回stdout脱敏已知TOML字符串、服务Bearer／私有HOME／源文件路径；原生错误隐藏原输出。同一服务最多一个操作，重叠返回busy。

stdout和stderr各限256KiB；命令1..600秒，加最多90秒自有后代清理；客户端超时至少command_timeout+120秒。同OS用户／工具权限不是多租户文件隔离边界，只用于自有一次性沙箱及明确授权任务。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。 当前固定安装支持 Linux x86_64。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/devin.md)。

## 问题反馈

[Issue72](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。厂商认证／模型行为属于Cognition；不附凭证或私有原始日志。

## 许可证

本包装层Apache-2.0；Cognition原程序／文档／手册保留独立条款，见[声明](UPSTREAM-NOTICE.md)。Git不提交或重许可原版二进制／源码，不宣称厂商背书或独立再分发授权。
