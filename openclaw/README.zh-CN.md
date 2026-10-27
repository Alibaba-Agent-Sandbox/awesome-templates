# openclaw

[English](README.md)

## 做什么

运行带认证、由当前服务管理的原生 OpenClaw 网关。配置自己的兼容模型 endpoint、API Key 和模型 ID 后，可以汇总费用，并使用返回的会话 ID 继续追问。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

OpenClaw `2026.10.4`、Node.js `24.16.0`、应用端口 9000 和可选网关端口 18789。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

通过原生网关汇总费用、保留上下文继续追问，并管理网关生命周期，无需安装系统服务。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

使用独立的 `OPENCLAW_GATEWAY_TOKEN` 进行网关认证。模型对话需要同时配置下方三个 `OPENCLAW_MODEL_*` 变量；旧的 `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` 不会自动配置这条链路。上游须支持 OpenAI Chat Completions，此 API Key 流程无需厂商 OAuth 登录。不填模型配置时仍可使用网关生命周期。保持 `bind="loopback"` 即可，命名对话方法通过应用端口 9000 访问内部网关。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENCLAW_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENCLAW_MODEL_API_KEY='<your-model-api-key>'
export OPENCLAW_MODEL_BASE_URL='<your-chat-completions-api-base-including-v1-if-required>'
export OPENCLAW_MODEL='<your-exact-model-id>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//openclaw --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_start --json-args '{"bind":"loopback","command_timeout":60}'
abx run "$SANDBOX_ID" gateway_health
abx run "$SANDBOX_ID" gateway_status
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_chat --json-args '{"prompt":"Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total."}'
# Copy session_id from the result to continue this conversation.
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_chat --json-args '{"prompt":"Remove the train from the previous expenses. Return the same JSON fields.","session_id":"<returned-session-id>"}'
abx run "$SANDBOX_ID" gateway_stop
```

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
            print(await client.commands.run('gateway_start', bind='loopback', command_timeout=60))
            print(await client.commands.run("gateway_health"))
            first = await client.commands.run("gateway_chat", prompt="Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total.")
            print(first)
            print(await client.commands.run("gateway_chat", prompt="Remove the train from the previous expenses. Return the same JSON fields.", session_id=first["session_id"]))
        finally:
            try:
                await client.commands.run("gateway_stop")
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/gateway_start`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "bind": "loopback",
  "command_timeout": 60
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 420 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

### 导出产物与清理

HTTP 启动后用相同认证 `POST /commands/gateway_health`（`{}`）检查，然后 `POST /commands/gateway_stop`（`{}`）停止。最后删除沙箱：

```bash
abx kill "$SANDBOX_ID"
```

`close()`/`aclose()` 仅关闭客户端连接，不释放沙箱。launch 日志中的已构建模板和镜像可能保留用于复用，不再需要时仅删除自己创建的那些资源。

### 切换模型和二次开发

更换模型、endpoint 或 API Key 时，修改三个 `OPENCLAW_MODEL_*` 变量并 launch 新实例。运行中的实例保留启动时的环境。`gateway_stop` 会清理临时状态及会话历史，重启后旧 session ID 也从新对话开始；不填或更换 ID 会建立独立对话。每个业务会话使用自己的 ID。

费用示例预期得到 count 3 / total 51.30，追问去掉火车后得到 count 2 / total 36.30。应用应解析 `text` 中的 JSON，并独立核算，不能假定模型始终输出正确格式。可以改为传入发票 CSV 和输出 schema。当前为文本对话能力，禁用模型工具、channel、浏览器/control UI 和嵌套 Docker；不会自动接通 Slack 等渠道。

直接 HTTP 业务请求使用 `POST /commands/gateway_chat`，body 为 `{"prompt":"Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total."}`。第二次 body 为 `{"prompt":"Remove the train from the previous expenses. Return the same JSON fields.","session_id":"<第一次返回的-session-id>"}`；使用完停止网关。内部调用的是 [OpenClaw 原生 Chat Completions](https://docs.openclaw.ai/gateway/openai-http-api)，无需把网关端口转发到公网。

## 命令参考

| 命令 | 参数（chat 的 prompt 必填，其余可选） | 返回值与上游行为 |
|---|---|---|
| `gateway_start` | `port: int=18789`（1024..65535，排除9000）；`bind: str="loopback"`（loopback或lan）；`command_timeout: int=60`（1..120秒） | 执行 `openclaw gateway run --allow-unconfigured --bind <bind> --auth token --port <port>`，认证健康后返回 `{running:true,healthy:true,url,bind}`。重复相同参数会重查健康；修改运行中的端口或监听方式前须先停止。 |
| `gateway_chat` | `prompt: str` 必填（非空，1..65536 UTF-8 字节）；`session_id: str=""`（空或1..80位 ASCII 字母/数字/下划线/连字符）；`command_timeout: int=180`（1..300秒） | 原生网关 `/v1/chat/completions` 返回 `{session_id,text}`；以 `openclaw/default` 为目标，以稳定的 `user` 保留会话。必要时自动启动当前服务管理的网关。 |
| `gateway_status` | 无 | `{running,owned,url}`，仅检查本 server 持有的进程，不代表健康。 |
| `gateway_health` | `command_timeout: int=20`（1..120秒） | 以隔离配置及 token 环境执行 `openclaw gateway health --json --timeout <毫秒>`，认证成功返回 `{healthy:true,url}`，否则异常。 |
| `gateway_stop` | `command_timeout: int=10`（1..120秒） | 对拥有的进程组先 TERM，超时 KILL，最多再等5秒回收。返回 `{running:false,owned:false}`，重复调用安全。 |

同一应用只拥有一个网关；使用 `gateway_stop` 停止自己启动的进程。loopback 网关只供沙箱内部使用。转发访问使用 lan，必须事先显式配置可信代理；不能从 X-Forwarded-For 推断信任。

## 配置

Linux 下短生命周期健康检查 RPC 会持续读取输出，并在清理自身进程组后才回收 leader，覆盖成功、错误和超时；不会停止独立的长期 gateway 进程组。通过 setsid 主动脱离组的进程不在该组清理范围内。

| 变量 | 默认 | 含义 |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | 空 | 启动网关必需，通过沙箱环境注入，不作为命令参数。子进程环境接收值，配置只引用变量名，不返回或加入 argv。 |
| `OPENCLAW_TRUSTED_PROXIES` | 空 | 端口转发使用的显式已核实代理 IP/CIDR；最多16项/2048字节，拒绝全网和组播。 |
| `ABX_SERVER_TOKEN` | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 `/health` 不要求应用令牌。 |
| `OPENAI_API_KEY`、`ANTHROPIC_API_KEY` | 空 | 可选上游模型凭据，网关健康不需要。本命令集不实现或验证模型调用。 |

网关使用私有临时配置与状态目录，关闭 browser/control UI、跳过channels，不修改用户已有 OpenClaw 配置。网关输出丢弃，避免上游原始日志将秘密带入命令接口。需要诊断上游配置时，在受控会话单独执行，不公开原始日志。

客户端超时或断开不保证原生网关已接受的任务取消；停止网关或删除沙箱可以结束剩余工作。对话和生命周期操作使用同一把锁，stop 可能等待当前有执行期限的请求结束。模型工具禁用，会话状态仅存于当前临时目录。

## 资源

2 vCPU，4096 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。网关内部健康检查不需要模型服务。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/openclaw.md)。

## 问题反馈

复用 [awesome-templates#20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20)。SDK/server问题在 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 提交，CLI问题在 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 提交，标题加 `[templates]`。上游参考：[Gateway CLI](https://docs.openclaw.ai/cli/gateway)；版本和参数同时通过已安装2026.10.4二进制核实。

## 许可证

[Apache-2.0](../LICENSE)。保留 OpenClaw 自身许可证及署名。
