# openclaw

[English](README.md)

## 做什么

将需要认证的 OpenClaw WebSocket 网关作为本 server 拥有的后台进程运行。命名命令提供启动、状态、认证健康检查和停止；无需安装系统服务。网关健康仅证明运行时可用，不能证明编程 Agent 或模型调用通过。

## 技术栈

- 阿里云 FC 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，部署工具解析占位符。
- Node.js `24.16.0`，npm 包 `openclaw@2026.10.4`。该上游包要求 Node >=24.16.0，基础镜像的 Node 20 不满足要求。
- server 固定为 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505`；部署时注入的 wheel 优先。
- 非 root `user`，目录 `/home/user/app`，generation 2；HTTP server 9000，网关默认 18789。

## 解决的问题

网关是常驻服务。同步执行 `openclaw start` 既不是正确的网关命令，也无法提供可用的命名命令生命周期。本模板运行 `openclaw gateway run`，等待认证 WebSocket health RPC 后返回并持有子进程对象。不读取 PID 文件，也不使用可能终止其他进程的 `--force`。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：SDK 示例显式启动并配置新的命名服务。预热进程不会自动获得后续创建时设置，参见[显式进程配置](../docs/runtime-environment.zh-CN.md)。

先配置 `abx` 和 provider。SDK 验收控制器在内存中生成私有网关和服务器令牌，显式启动自有进程，令牌不进入 shell 参数。

```bash
abx template install ./openclaw --registry-type local
abx create --template <template-id>
abx run <sandbox-id> gateway_status
python3 openclaw/sdk_e2e_test.py --sandbox-id <sandbox-id>
abx run <sandbox-id> gateway_status
abx kill <sandbox-id> -y
```

默认只监听 `loopback`。确需沙箱端口转发时才使用 `bind=lan`。返回的 URL 是沙箱内部地址；外部访问使用 provider 的端口 URL 并携带网关 token。它与保护 9000 端口的 `ABX_SERVER_TOKEN` 是两个独立凭据。

## 快速开始（Python SDK）

客户端分发名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。尚未发布的版本使用[配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
import os
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    server = None
    try:
        server = await sb.start_server(
            port=9010, commands="/home/user/app/commands.py", timeout=60,
            token=secrets.token_urlsafe(32),
            env={"OPENCLAW_GATEWAY_TOKEN": secrets.token_urlsafe(32),
                 "OPENCLAW_TRUSTED_PROXIES": os.environ.get("OPENCLAW_TRUSTED_PROXIES", "")})
        print(await server.commands.run("gateway_start", port=18789, bind="loopback", command_timeout=60, timeout=90))
        print(await server.commands.run("gateway_health", command_timeout=20, timeout=35))
        print(await server.commands.run("gateway_stop", command_timeout=10, timeout=25))
    finally:
        if server:
            await server.aclose()
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

`command_timeout` 控制服务端生命周期；SDK保留的 `timeout` 仅控制HTTP等待，应大于服务端时限及清理余量。命名命令使用 `sb.run`；shell 使用 `sb.commands.run`。启用 `ABX_SERVER_TOKEN` 时，按[模板规范](../docs/template-spec.md)使用 `sb.server_at(9000, token=...)` 调用认证 server。

## 快速开始（HTTP POST）

`ABX_SERVER_URL` 指向 9000 端口。网关 token 应预先注入 server 环境。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gateway_start" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  -H 'Content-Type: application/json' \
  --data '{"port":18789,"bind":"loopback","command_timeout":60}'
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gateway_health" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  -H 'Content-Type: application/json' --data '{"command_timeout":20}'
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gateway_stop" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  -H 'Content-Type: application/json' --data '{}'
```

未启用 server 认证时去掉 Authorization。参数直接放在 JSON body 内。成功返回 HTTP 200 `{"result":...}`；缺少或错误类型参数为 400；认证失败为 401；范围或 action 不合法、缺少 CLI/token、端口冲突、启动超时、认证健康失败为 500 `{"error","type"}`。执行异常不能作为网关成功。客户端断开不会自动取消服务端操作；生命周期命令各自有超时。当前 server `/health` 是公开探针，`/commands` 等业务路由受认证保护。

## 命令参考

| 命令 | 参数（均可选） | 返回值与上游行为 |
|---|---|---|
| `gateway_start` | `port: int=18789`（1024..65535，排除9000）；`bind: str="loopback"`（loopback或lan）；`command_timeout: int=60`（1..120秒） | 执行 `openclaw gateway run --allow-unconfigured --bind <bind> --auth token --port <port>`，认证健康后返回 `{running:true,healthy:true,url,bind}`。重复相同参数会重查健康；修改运行中的端口或监听方式前须先停止。 |
| `gateway_status` | 无 | `{running,owned,url}`，仅检查本 server 持有的进程，不代表健康。 |
| `gateway_health` | `command_timeout: int=20`（1..120秒） | 以隔离配置及 token 环境执行 `openclaw gateway health --json --timeout <毫秒>`，认证成功返回 `{healthy:true,url}`，否则异常。 |
| `gateway_stop` | `command_timeout: int=10`（1..120秒） | 对拥有的进程组先 TERM，超时 KILL，最多再等5秒回收。返回 `{running:false,owned:false}`，重复调用安全。 |
| `gateway` | `action: str="start"`（start、status、health、stop）；`port: int=18789`；`bind: str="loopback"`；`command_timeout: int=60` | 兼容别名，返回对应命令结果。port/bind仅用于start；command_timeout用于start/health/stop。不再向上游透传任意主命令。 |

健康探针在执行截止后还需要有界的组终止、进程回收及管道读取清理时间；启动失败也会清理自己创建的网关。一个 server 只拥有一个网关。不安装 systemd 服务。server 意外死亡后内存 handle 丢失；重启不会接管或误杀未知进程。销毁沙箱负责清理其进程。stop 删除临时状态；需要持久化会话时应独立设计上游 Agent 配置，不能假定此运行时保存会话。

### 2.1版显式代理与 SDK 验收

普通回环网关仍无需代理配置。若要通过提供方转发的端口访问网关，显式选择 `bind="lan"`，
并在命名命令服务器启动前设置 `OPENCLAW_TRUSTED_PROXIES`：最多16个逗号分隔的明确IP/CIDR，
最多2048UTF-8字节。拒绝空条目、无效地址、全网及组播配置；重复地址归一化并去重。
这些地址应来自已核实的提供方代理配置，不能使用请求的 X-Forwarded-For 内容作为信任依据。
空值保留上游默认策略；不会自动信任所有代理。令牌认证仍强制启用。

实际2.0.1原生认证健康RPC和转发 `/healthz` 已通过，但 `/readyz` 经提供方代理返回403。
固定上游版本会拒绝来源不受信任的转发头。因此2.1仅把显式配置写入自有临时网关配置，
不修改用户全局配置，不绕过上游来源检查。`/healthz` 应为HTTP200且 `ok=true`，
`/readyz` 应为HTTP200且 `ready=true`；启动阶段可以503，验收保持有界等待。

CLI 示例在仓库根目录运行配套 SDK 控制器。它借用全新自有沙箱，在9012启动短暂的随机路径探针，
从内核连接地址观察该次已知入口，给自有9010服务器显式传入准确 `/32` 或 `/128` 测试配置，
再通过真实 SDK 启停认证网关并独立访问18789的存活/就绪接口。不会信任转发头提供的地址，
不会返回令牌/原始代理地址，不会销毁调用者沙箱；仅清理自己的进程、监听和临时状态目录。
CLI 调用结束后，仍由调用者执行最终沙箱删除。无需模型密钥，也不声称模型或频道已通过。
SDK 示例显式启动9010服务器，避免把 create-time 环境误当成预热9000进程的配置。

## 配置

Linux 下短生命周期健康检查 RPC 会持续读取输出，并在清理自身进程组后才回收 leader，覆盖成功、错误和超时；不会停止独立的长期 gateway 进程组。通过 setsid 主动脱离组的进程不在该组清理范围内。

| 变量 | 默认 | 含义 |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | 空 | 启动网关必需，通过沙箱环境注入，不作为命令参数。子进程环境接收值，配置只引用变量名，不返回或加入 argv。 |
| `OPENCLAW_TRUSTED_PROXIES` | 空 | 端口转发使用的显式已核实代理 IP/CIDR；最多16项/2048字节，拒绝全网和组播。 |
| `ABX_SERVER_TOKEN` | 空 | 9000端口业务路由的可选 bearer 认证；公开 `/health` 探针除外。 |
| `ABX_SERVER_PORT` | 9000 | 本地 `python commands.py` 的 server 端口；云端 start_cmd 明确使用9000。 |
| `OPENAI_API_KEY`、`ANTHROPIC_API_KEY` | 空 | 可选上游模型凭据，网关健康不需要。本命令集不实现或验证模型调用。 |

网关使用私有临时配置与状态目录，关闭 browser/control UI、跳过channels，不修改用户已有 OpenClaw 配置。网关输出丢弃，避免上游原始日志将秘密带入命令接口。需要诊断上游配置时，在受控会话单独执行，不公开原始日志。

## 资源

2 vCPU、4096 MB RAM；Express约10G rootfs。网关本身无需 Docker 或额外能力。依赖 Docker 的嵌套 Agent 沙箱不属于已验证范围。

## 已验证

2.1.0 已在阿里云极速版通过真实 SDK 创建的原生 steps **及**精确 CI Docker 镜像验收。两种模式均实际启动并认证原生网关、确认返回后持续运行，独立检查转发 healthz（ok=true）和 readyz（ready=true）均 HTTP200，再停止并确认状态、自有监听端口和临时状态不存在。测试仅显式信任独立观测到的精确代理地址，不公开地址或 token。

| 提供方 | 版本和已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 2.1.0；原生 steps、SDK 生命周期/探针、自有资源独立清理 | [CLI/SDK 冒烟](evidence/express-2026-10-20T153536Z.json)、[完整原生 SDK 网关](evidence/sdk-gateway-steps-2026-10-20T153536Z.json) |
| alicloud-express | 2.1.0；精确 CI 镜像、SDK 生命周期/探针、sandbox/模板/镜像独立清理 | [镜像/源码完整性](evidence/image-http-2026-10-20T163034Z.json)、[完整原生 SDK 网关](evidence/sdk-gateway-image-2026-10-20T163034Z.json) |

网关范围无需模型 key；不推断模型、消息通道或嵌套 sandbox 已验证。通用镜像回执中的空 HTTP 测试集不算完整 HTTP 控制器通过，原生功能由单独 SDK 网关控制器证明。保留四次2.0.1失败诊断和一次2.1云操作前磁盘预算失败。见[最终工程记录](../.agents/evidence/verify/2026-10-20-openclaw-native-sdk-final.md)。旧2.0.1凭证仅保留历史范围。

## 2.0.1历史验证


| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.0.1; steps构建、官方READY、CLI/SDK基础冒烟、独立清理；当前版本真实模型尚未执行 | [2026-10-19](evidence/express-2026-10-19T183726Z.json) |

新版本的目录归属已在真实生成步骤中验证。旧版本回执保持历史范围；基础冒烟不能推断完整模型验收。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

本修订尚无 provider 镜像或云端通过证据。本地真实 CLI 的启动、认证健康、返回后持续运行与清理记录在[工程验证](../.agents/evidence/verify/2026-10-16-openclaw-owned-gateway.md)。L1镜像构建、L2 Express仍待执行；本地运行不能替代。L3模型/编程验收尚未运行。

</details>

## 二次开发

阅读[设计文档](../docs/design/openclaw.md)。固定上游版本，argv使用列表，token放环境，保留拥有的进程对象，不使用PID文件。生命周期变更应增加行为回归并同步双语文档。新增Agent/模型命令需要独立契约和真实模型验收。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py openclaw`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵循[贡献指南](../CONTRIBUTING.md)和[模板规范](../docs/template-spec.md)。执行 `python3 scripts/check_template.py openclaw`、`python3 -m pytest openclaw/test_commands.py`。本地HTTP验收先启动 `python3 openclaw/commands.py`，再用一致的 `E2E_BASE_URL`、server认证、网关token执行 `python3 openclaw/e2e_test.py`。随机合成token足以验收真实本地网关，无需模型key。provider证据通过前保留 `tested_on: []`；缺少镜像或云端门禁时明确记录。

## 问题反馈

复用 [awesome-templates#20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20)。SDK/server问题在 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 提交，CLI问题在 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 提交，标题加 `[templates]`。上游参考：[Gateway CLI](https://docs.openclaw.ai/cli/gateway)；版本和参数同时通过已安装2026.10.4二进制核实。

## 许可证

[Apache-2.0](../LICENSE)。保留 OpenClaw 自身许可证及署名。

### 2026-10-20真实认证网关完整 step 检查点

[真实2.0.1 step](evidence/express-2026-10-20T161954Z.json)及[原完整 HTTP 控制器](evidence/verification-steps-2026-10-20T161954Z.json)已通过官方 READY、Python SDK 创建、全部 CLI/SDK smoke，以及11项 HTTP PASS/0 FAIL/1模型 SKIP，耗时703.799秒。独有测试令牌仅在私有配方安装步骤之后注入，实际验证认证就绪／健康、持续运行状态、自有停止及停止后的健康失败。沙箱、模板和精确私有 Node 缓存对象／bucket均独立确认清理；未使用操作者／模型凭据，公开回执无令牌值。早期6/0/2回执仅保留较窄范围，不算网关生命周期通过。[严格审计和复现](../docs/platform-steps.zh-CN.md)。

### 当前2.1.0完整 HTTP step 复测

集成显式代理配置及4GiB资源后，[当前2.1.0 step 回执](evidence/express-2026-10-20T165241Z.json)和[未改变的完整 HTTP 控制器](evidence/verification-steps-2026-10-20T165241Z.json)在525.594秒内通过11/0/1（模型 SKIP）：官方 READY、真实 CLI/Python SDK、认证网关生命周期及沙箱／模板／私有缓存独立清理。当前完整 manifest 绑定的严格审计接受此源码；旧2.0.1完整回执仍为历史。上方当前原生 SDK／转发健康及镜像证明独立保留。
