# Factory Droid

## 做什么

运行固定版本 Factory Droid CLI。`droid_byok` 使用显式兼容模型，`droid` 使用 Factory 账号；两条路径均为无交互命令。

在现有项目上无头运行 Factory Droid 0.241.1。具名命令提供有执行时限的编码调用、版本查询与不调用模型的安装检查。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

原版 `@factory/cli@0.241.1` 及配套 Linux x86_64 原生包。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

示例使用 `droid_byok`，显式配置兼容 Chat Completions 自定义模型，不需要 Factory 账号或浏览器登录。该路径允许读写文件，生成的 Python 程序需另外执行。另一条 `droid` 命令需要在 [Factory 设置](https://app.factory.ai/settings/api-keys)获得真正的 `FACTORY_API_KEY`，模型 Key 不能代替。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DROID_MODEL_API_KEY='<your-model-or-vendor-key>'
export DROID_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export DROID_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//droid --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" droid_byok --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('droid_byok', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/droid_byok`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
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

| 命令 | 参数 | 返回值 / 上游调用 |
| --- | --- | --- |
| `droid_byok` | 必填 `prompt: str`，1–32768个 UTF-8 字节、非空、无 NUL；`cwd: str=""`，最多4096字节，工作区内已存在且解析后不越界；`command_timeout: int=300`，1–600秒，拒绝 bool | 对象：原生 `stdout`、`stderr`、`exit_code`、`native_version`。固定 `droid exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`，任务经匿名 stdin。修改所选项目，所有路径清理私有状态。 |
| `droid_byok_setup_check` | 无 | 模型/base/key 存在布尔值、`mode: openai-compatible-byok`、`factory_account_required: false`；无模型请求及秘密值。 |
| `droid_version` | 无 | `droid --version` 的版本字符串；不需要模型密钥。 |
| `droid_setup_check` | 无 | 对象：`installed`（布尔），`package`、`version`、`expected_version`（字符串），`api_key_set`、`workspace_exists`、`auto_update_enabled`（布尔）。不调用模型、不返回密钥值。 |
| `droid` | `prompt`：必填非空字符串；`auto`：字符串，默认 `low`，可为 `""`、`low`、`medium`、`high`；`cwd`：字符串，默认 `""`，必须为 `WORKSPACE` 内现有目录；`command_timeout`：整数，默认 300，范围 1–600 秒 | `droid exec [--auto LEVEL] -- PROMPT` 的缓冲 stdout 字符串。非零退出或超时抛出脱敏执行错误。 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 默认值 | 作用 |
| --- | --- | --- |
| `DROID_MODEL_API_KEY` | 空；BYOK 必填 | 最多8192字符，禁 CR/LF/NUL，仅进入私有原生环境。 |
| `DROID_MODEL_BASE_URL` | 空；BYOK 必填 | 显式 HTTPS 兼容接口，最多2048字符，无 userinfo/query/fragment；仅本地字面 HTTP 用于合成测试。 |
| `DROID_MODEL` | 空；BYOK 必填 | 显式1–200字符模型标识。 |
| `FACTORY_API_KEY` | 空 | 创建时注入的 Factory 账户 API 密钥；仅 `droid` 需要。 |
| `ABX_SERVER_TOKEN` | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `WORKSPACE` | `/home/user/app` | 现有项目根目录；显式配置无效目录会报错。 |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | 子进程强制禁用自动更新，保持固定版本。 |

Factory 凭据在 [Factory API 密钥设置](https://app.factory.ai/settings/api-keys)获取。DashScope 或 OpenAI 密钥不能替代 `FACTORY_API_KEY`。`droid_byok` 使用私有原生 `customModels` 配置，provider 为 `generic-chat-completion-api`，显式模型/base 及 `apiKey: "${ABX_DROID_MODEL_KEY}"`。真实密钥不写入设置或 argv，不注入 Factory 密钥、交互登录或替代二进制。输出脱敏密钥/base 并删除私有状态。[官方 BYOK 文档](https://docs.factory.com/model-independence/byok)。上游行为见 [Droid Exec](https://docs.factory.com/droid-exec/overview)，具体选项以固定版本的真实帮助为准。脱敏涵盖 stdout、错误中的原始与 JSON 转义的已配置秘密值；Agent 写出的项目文件仍需遵守正常的秘密管理要求。cwd 约束用于选择项目，不是操作系统安全隔离边界。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/droid.md)。

## 问题反馈

继续使用 [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19)。模板问题提交至 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/server 问题至 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题至 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附版本、提供方、generation 和脱敏复现；不要附密钥或原始私有日志。

## 许可证

模板代码使用 [Apache-2.0](../LICENSE)。Factory Droid 独立按上游条款分发；安装 CLI 不改变其许可证。
