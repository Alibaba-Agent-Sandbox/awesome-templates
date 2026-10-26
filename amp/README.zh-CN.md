# amp

Agent Sandbox 里的 Sourcegraph Amp CLI。镜像钉住 `@ampcode/cli`，在端口 9000 上提供命名命令。

## 做什么

安装 Amp CLI（命令名 `amp`），并注册四个命令：

| 命令 | 实际执行 |
|---|---|
| `amp_version` | `amp version` |
| `amp_setup_check` | `amp version`，然后只读检查现有设置文件 |
| `amp_execute` | `amp --no-color --no-notifications --no-ide -x <prompt>` |

`stream_json` 为 true 时，`amp_execute` 加上 `--stream-json`。HTTP 响应是进程退出后的完整标准输出，不是实时流。

`amp_execute` 在启动 CLI 之前检查 `AMP_API_KEY`。变量缺失或只有空白时，命令返回的错误里写明 `AMP_API_KEY`，并说明 CLI 自己会进入设备登录并等待。

Amp 不接受 DashScope 密钥、`ABX_LLM_API_KEY` 或 OpenAI 兼容的 base URL。令牌是 Amp 自己的访问令牌，在 [ampcode.com 设置](https://ampcode.com/settings/security#access-token) 创建。

`--dangerously-allow-all` 是 `0.0.1792022479-ge66e24` 这个二进制接受的标志。该版本的 `amp --help` 选项列表里没有它。帮助文本里写的是设置项 `amp.dangerouslyAllowAll`。仅显式传入 `dangerously_allow_all=true` 时，`amp_execute` 才会添加该标志。已有设置保持原样，可用 `amp_setup_check` 检查其权限值。镜像默认值为 false。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 `@ampcode/cli@0.0.1792022479-ge66e24` Linux x86_64 CLI、平台 Node.js 20、Git 和 ripgrep。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

先按 [Amp 登录说明](https://ampcode.com/docs/cli)取得 Amp 账号密钥。命名命令使用 `AMP_API_KEY`，不会启动浏览器登录。模型和后端由 Amp 选择，本包装没有通用 OpenAI endpoint/model 参数；`AMP_URL` 是 Amp 服务地址，不是模型接口。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AMP_API_KEY='<your-model-or-vendor-key>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//amp --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=720 abx run "$SANDBOX_ID" amp_execute --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","dangerously_allow_all":true}'
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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=720
        )
        try:
            print(await client.commands.run('amp_execute', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', dangerously_allow_all=True))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/amp_execute`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "dangerously_allow_all": true
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 720 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

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

| 命令 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `amp_version` | 无 | 字符串 | `amp version` 的第一个字段，例如 `0.0.1792022479-ge66e24`。 |
| `amp_setup_check` | 无 | 对象 | `installed`、`package`、`version`、`api_key_set`、`settings_path`、`settings_exists`、`dangerously_allow_all`、`updates_mode`。不写文件；文件缺失时报告 false 和 `default`。 |
| `amp_execute` | `prompt` 字符串，必填。`stream_json` 布尔，可选，默认 `false`；`dangerously_allow_all` 布尔，可选，默认 `false`。 | 字符串 | `amp -x` 的标准输出。`stream_json` 为 true 时加上 `--stream-json`。 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `AMP_API_KEY` | `amp_execute` 需要 | 空 | Amp 访问令牌。不是 DashScope 或 OpenAI 密钥。`template.yaml` 里的值是空字符串。 |
| `AMP_URL` | 否 | `https://ampcode.com/` | Amp 服务地址。这是 CLI 自己的默认值，镜像不覆盖它。 |
| `AMP_SETTINGS_FILE` | 否 | 镜像内为 `/home/user/.config/amp/settings.json` | 调用者管理的设置文件，仅作只读检查。 |
| `AMP_LOG_FILE` | 否 | 镜像内为 `/home/user/.cache/amp/logs/cli.log` | CLI 日志路径。 |
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

在 `template launch` 前安全导出清单中声明为空的秘密变量，让应用启动时读取；不要写入镜像、YAML 或日志。


## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/amp.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。
