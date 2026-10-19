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

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

先配置 `abx` 和 provider。在本地环境准备不可预测的随机网关 token，避免将秘密写入源码或 shell 历史。

```bash
abx template install ./openclaw --registry-type local
abx create --template <template-id> --env "OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN"
abx run <sandbox-id> gateway_status
abx run <sandbox-id> gateway_start --json-args '{"port":18789,"bind":"loopback","command_timeout":60}'
abx run <sandbox-id> gateway_health --json-args '{"command_timeout":20}'
abx run <sandbox-id> gateway_stop --json-args '{"command_timeout":10}'
abx kill <sandbox-id> -y
```

默认只监听 `loopback`。确需沙箱端口转发时才使用 `bind=lan`。返回的 URL 是沙箱内部地址；外部访问使用 provider 的端口 URL 并携带网关 token。它与保护 9000 端口的 `ABX_SERVER_TOKEN` 是两个独立凭据。

## 快速开始（Python SDK）

客户端分发名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。尚未发布的版本使用[配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=300,
        envs={"OPENCLAW_GATEWAY_TOKEN": os.environ["OPENCLAW_GATEWAY_TOKEN"]},
    )
    try:
        print(await sb.run("gateway_start", port=18789, bind="loopback", command_timeout=60, timeout=90))
        print(await sb.run("gateway_health", command_timeout=20, timeout=35))
    finally:
        try:
            await sb.run("gateway_stop", command_timeout=10, timeout=25)
        finally:
            await sb.kill()

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

## 配置

Linux 下短生命周期健康检查 RPC 会持续读取输出，并在清理自身进程组后才回收 leader，覆盖成功、错误和超时；不会停止独立的长期 gateway 进程组。通过 setsid 主动脱离组的进程不在该组清理范围内。

| 变量 | 默认 | 含义 |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | 空 | 启动网关必需，通过沙箱环境注入，不作为命令参数。子进程环境接收值，配置只引用变量名，不返回或加入 argv。 |
| `ABX_SERVER_TOKEN` | 空 | 9000端口业务路由的可选 bearer 认证；公开 `/health` 探针除外。 |
| `ABX_SERVER_PORT` | 9000 | 本地 `python commands.py` 的 server 端口；云端 start_cmd 明确使用9000。 |
| `OPENAI_API_KEY`、`ANTHROPIC_API_KEY` | 空 | 可选上游模型凭据，网关健康不需要。本命令集不实现或验证模型调用。 |

网关使用私有临时配置与状态目录，关闭 browser/control UI、跳过channels，不修改用户已有 OpenClaw 配置。网关输出丢弃，避免上游原始日志将秘密带入命令接口。需要诊断上游配置时，在受控会话单独执行，不公开原始日志。

## 资源

2 vCPU、4096 MB RAM；Express约10G rootfs。网关本身无需 Docker 或额外能力。依赖 Docker 的嵌套 Agent 沙箱不属于已验证范围。

## 已验证

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
