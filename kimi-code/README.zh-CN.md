# kimi-code

## 做什么

在已有沙箱目录运行官方 Kimi Code 2.2.0 的一次无头任务。每次使用私有临时配置，结束、失败和超时清理自有进程组。上游 prompt 模式自动许可工具，wrapper 须显式 allow_tools=True 才启动；返回缓冲的 stream-JSON 字符串，不提供会话续接。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 Node CLI `@moonshot-ai/kimi-code@2.2.0` 和 Node.js `24.16.0`。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

默认 provider type 是 `openai`，填写授权的兼容 OpenAI base/key/model，无需交互 Kimi 登录。原版 CLI 也支持其文档中的 `kimi`、`anthropic` 类型，但修改非空 `KIMI_MODEL_PROVIDER_TYPE` 需要使用自己的源码配方；base、model、key 必须同时匹配该协议。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export KIMI_MODEL_API_KEY='<your-model-or-vendor-key>'
export KIMI_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export KIMI_MODEL_NAME='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//kimi-code --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" kimi --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","allow_tools":true,"cwd":"/home/user/app","command_timeout":300}'
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
            print(await client.commands.run('kimi', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', allow_tools=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/kimi`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

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

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| kimi_version | 无 | 固定 CLI 版本 |
| kimi_setup_check | 无 | installed/version/pinned_version、模型/key/base 是否配置及 workspace，无凭据值 |
| kimi | prompt 必填字符串，1..65536 UTF-8 字节；cwd 可选，默认 workspace，必须存在；command_timeout 默认 600，整数 1..1800 秒；allow_tools 默认 false，布尔 | 缓冲 stream-JSON；非零、超时、每流超过 8 MiB 为错误 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 必需 | 默认/用途 |
| --- | --- | --- |
| KIMI_MODEL_NAME | 模型任务需要 | 实际模型 ID |
| KIMI_MODEL_API_KEY | 模型任务需要 | 空 secret 声明，启动时注入 |
| KIMI_MODEL_BASE_URL | 模型任务需要 | 明确授权的兼容端点，不隐式转发凭据 |
| KIMI_MODEL_PROVIDER_TYPE | 否 | openai，也可 kimi/anthropic |
| WORKSPACE | 否 | /home/user/app |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置名称已从实际 npm 2.2.0 runtime 核对，另见[官方配置](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md)。每次调用用独有 KIMI_CODE_HOME，保留用户配置，去除无关云端/registry 凭据，响应中脱敏 secret 及 JSON 转义形式。allow_tools=false 拒绝启动，不声称提供只读 prompt 模式。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/kimi-code.md)。

## 问题反馈

模板问题见 [Issue 48](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/48)，SDK/server 去 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 去 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。提供版本与脱敏复现。

## 许可证

模板 wrapper 为 Apache-2.0，见 [LICENSE](../LICENSE)；上游 Kimi Code 为 MIT，固定官方 npm 包保留原许可证。
