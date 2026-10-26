# Cursor Agent

[English](README.md)。

## 做什么

通过类型化命名命令，在自有一次性沙箱中运行原版 Cursor Agent CLI。推理和工具执行由原生 Cursor 完成。agent任务需要独立的CURSOR_API_KEY；不会复用兼容模型或操作端其他密钥。自动工具执行必须显式传入allow_unsafe_tools=True。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

原版 Cursor Agent CLI `2026.10.19-6bbf2c4` Linux x86_64 发行包及其自带 Node 运行时。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

在 Cursor Dashboard 的 API Keys/Integrations 中创建个人 User API Key，按 [Cursor CLI 认证说明](https://cursor.com/help/integrations/cli)取得真正的 Cursor 账号 API Key。本无交互包装使用 `CURSOR_API_KEY`，不使用浏览器登录，也不接受 OpenAI Key 代替。命令可选 `model` 选择该 Cursor 账号可用模型；未提供任意模型 endpoint 配置。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CURSOR_API_KEY='<your-model-or-vendor-key>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//cursor-agent --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" agent --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('agent', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/agent`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

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
| agent_version | 无 | 验证原文件后执行原生--version，返回固定版本字符串 |
| agent_native_check | 无 | original_native/headless_print/json_output/explicit_force/contained_workspace布尔字段，执行原生--help，无模型调用 |
| agent_setup_check | 无 | mode/installed/pinned_version/api_key_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态，无值或网络 |
| agent | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原生最终响应；明确授权后可读写文件和执行工具 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。 模型调用串行执行；并发请求会返回 busy。清理可能延长响应时间，示例为此保留 HTTP 等待余量。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| CURSOR_API_KEY | 空；agent必需 | 厂商凭证，命令模块导入时捕获 |
| WORKSPACE | /home/user/app | 项目根目录，导入时捕获 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

原生子进程只获得自身显式厂商密钥及私有HOME/config/data/cache/TMP等最小环境。固定原生参数关闭更新和项目配置加载；不使用操作系统钥匙串或原生持久会话。成功／失败／超时后删除每次私有状态。服务和工具共享OS用户，路径不是其他租户的隔离边界；自动工具仅用于自有一次性沙箱。

每个服务进程最多一个agent操作，重叠返回busy。stdout/stderr各限256KiB；命令1..600秒加最多90秒清理，客户端超时应至少command_timeout+120秒。已知厂商密钥、命令token、私有HOME值脱敏。私有会话或云资源ID不进入公开证据。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。 当前固定安装支持 Linux x86_64。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/cursor-agent.md)。

## 问题反馈

[Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。上游行为反馈给Cursor，不附凭证或私有会话。

## 许可证

自编写模板代码Apache-2.0；Anysphere原版软件和第三方许可保持原条款与声明，见[说明](UPSTREAM-NOTICE.md)。本Git仓库不分发上游二进制／源码，也不声称厂商背书。
