# claude-code

## 做什么

运行官方未修改的 Claude Code2.0.76无交互规划及 Read/Edit/Write/Bash 工具。原 `claude` 保留面向 Anthropic 的接口；`claude_byok` 显式使用本项目编写的 Messages 到 OpenAI Chat 文本和工具协议适配器。兼容模型模式属于实验功能，[Anthropic 不支持将其用于非 Claude 模型](https://code.claude.com/docs/en/llm-gateway)，不代表获得 Claude 模型、订阅或官方背书。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

原版 Claude Code `2.0.76`、Node.js 20，以及显式 BYOK 命令使用的模板文本/工具协议适配层。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

示例选择 `claude_byok`：原版 Claude CLI 加上模板显式的文本/工具适配层，连接你的 Chat Completions endpoint；不会登录 Claude 订阅，也不实现完整 Anthropic API。填写全部三个 `CLAUDE_MODEL_*` 配置。`ANTHROPIC_API_KEY` 属于另一条 `claude` 命令，不会被此路径自动复用；不会启动浏览器登录。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CLAUDE_MODEL_API_KEY='<your-model-or-vendor-key>'
export CLAUDE_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export CLAUDE_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//claude-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=660 abx run "$SANDBOX_ID" claude_byok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_unsafe_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            print(await client.commands.run('claude_byok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_unsafe_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/claude_byok`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "allow_unsafe_tools": true,
  "cwd": "/home/user/app",
  "command_timeout": 300
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 660 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

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

| 命令 | 参数 | 结果与副作用 |
| --- | --- | --- |
| claude_version | 无 | 原 CLI `2.0.76 (Claude Code)`；无模型调用 |
| claude_native_check | 无 | 原 cli.js 哈希与帮助参数：original_native/isolated_settings/no_session_persistence/strict_mcp 布尔值 |
| claude_setup_check | 无 | mode及model_key_set/model_base_set/model_set存在标志、vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true；不返回值、不发网络请求 |
| claude_byok | prompt必需字符串，非空、1..32768UTF8字节、无NUL；cwd默认空字符串、最多4096字节、解析后位于WORKSPACE内的已有目录；command_timeout整数1..600秒，默认300，拒绝布尔值；allow_unsafe_tools布尔默认False，需显式True才能使用该可丢弃沙箱权限模式 | stdout/exit_code0/native_completed/native_version/cli_sha256/model/permission_profile/protocol/model_calls/native_tool_results/relay_calls；原始工具修改项目，不返回完整轨迹 |
| claude | prompt必需非空字符串；model字符串默认sonnet；cwd默认空字符串、已有且位于工作区内；allowed_tools默认Read,Edit,Write；resume默认空字符串；command_timeout整数默认300、范围1..900秒 | 原生接口将原生JSON编码为字符串并脱敏环境密钥；保留原Anthropic凭据和设置行为，BYOK隔离模式的保证不覆盖原生接口 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。 模型调用串行执行；并发请求会返回 busy。清理可能延长响应时间，示例为此保留 HTTP 等待余量。

## 配置

| 名称 | 默认与要求 | 含义 |
| --- | --- | --- |
| CLAUDE_MODEL_API_KEY | 空，BYOK必需 | 明确授权的兼容上游密钥，仅父适配器持有 |
| CLAUDE_MODEL_BASE_URL | 空，BYOK必需 | HTTPS Chat基址，无userinfo/query/fragment、最多2048字符；固定测试允许字面环回HTTP |
| CLAUDE_MODEL | 空，BYOK必需 | 选定模型，1..200允许的标识字符 |
| ANTHROPIC_API_KEY | 空，仅原生供应商模式 | 原生Anthropic配置；BYOK入口不会隐式复用 |
| WORKSPACE | /home/user/app | 已有项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

BYOK配置在模块导入时捕获。密钥最多8192字符且无控制字符；不默认回退厂商、模型或密钥。原CLI和工具仅获得临时本地适配器token、最小环境以及私有HOME/config/cache；真实密钥仅父进程持有并只发往明确指定的Chat来源。结果与错误不含凭据、私有地址或完整轨迹。同用户OS访问仍存在；环境过滤和cwd约束不构成另一个租户边界。原生接口resume与设置行为保留，不纳入BYOK隔离承诺。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。 当前固定安装支持 Linux x86_64。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/claude-code.md)。

## 问题反馈

[Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15)、[模板缺陷](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原始上游问题遵循其支持渠道。不得附加密钥或私有轨迹。

## 许可证

本项目模板和适配器：[Apache-2.0](../LICENSE)。原Anthropic包保留全部权利并遵循[上游条款和声明](UPSTREAM-NOTICE.md)，不重新授权或暗示官方背书。
