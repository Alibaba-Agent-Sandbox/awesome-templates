# node-web

[English](README.md)

## 做什么

每个沙箱管理一个真实 Node HTTP 应用。`serve` 启动 JavaScript 入口，`start` 和 `dev` 在后台运行 npm 脚本。只有子进程存活并返回 HTTP 2xx/3xx，启动才成功。`status`、`request`、`logs`、`stop` 提供状态、真实请求、日志和停止。内置无第三方依赖的 `index.js`，可直接验证 HTTP 服务。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 提供 Node 20 和 Python 3.13；部署默认替换为 `cn-hangzhou`、`v0.0.49`。无额外 npm 依赖。工作目录 `/home/user/app`，以非 root 的 `user` 运行，generation 2。`start_cmd` 在 9000 启动命令服务，`ready_cmd` 做 healthcheck；Dockerfile 无 CMD/ENTRYPOINT。

## 解决的问题

仅创建进程或端口可连接不能证明应用就绪。模板执行 HTTP 检查，持续消费 stdout/stderr，限制服务日志大小，并将 npm 启动器与 Node 子进程一起停止。`build` 执行应用真实构建脚本，非零退出会报错。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//node-web --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" serve --json-args '{"entry":"index.js","port":3000}'
abx run "$SANDBOX_ID" request --json-args '{"path":"/"}'
```

返回示例应用的 HTTP 状态和包含 `node-web ready` 的响应正文。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

在完成上述 CLI 启动、设置 `SANDBOX_ID` 后，将以下保存为 `use_template.py`，执行 `python3 use_template.py`。它连接同一实例，不另建沙箱。对于需要输入的示例，先在本机准备上面的文件。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            await client.commands.run('serve', entry='index.js', port=3000)
            result = await client.commands.run('request', path='/')
            print(result)
        finally:
            try:
                await client.commands.run('stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

先按顺序调用：

- `POST /commands/serve` with `{"entry": "index.js", "port": 3000}`.

`POST /commands/request`

```json
{
  "path": "/"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/stop` with `{}`.

## 命令参考

全部参数可选。`cwd` 为字符串，默认空：先选 `WORKSPACE`，再选 `/home/user/app`；默认目录不存在时采用命令服务当前目录。显式目录必须存在。三个启动命令共用 `port: int = 3000`（1024–65535，排除命令服务端口）、`ready_path: str = "/"`（本地绝对路径，禁止 `//` 与 CR/LF）、`timeout_s: int = 20`（1–120 秒）。

| 命令 | 参数 | 返回 / 实际 argv |
|---|---|---|
| `serve` | 共用参数；`entry: str = "index.js"`；`cwd: str = ""` | HTTP 就绪后的运行信息；在 cwd 执行 `node <resolved-entry>` |
| `start` | 共用参数；`cwd: str = ""` | 运行信息；`npm start` |
| `dev` | 共用参数；`cwd: str = ""` | 运行信息；`npm run dev` |
| `status` | 无 | `status`、`pid`、`http_ready`；启动过还含 `port`、`exit_code`、`http_status` |
| `stop` | 无 | `status: stopped`、`pid`；向所属进程组先 SIGTERM 后 SIGKILL，可重复调用 |
| `logs` | `max_bytes: int = 16384`，1–131072 | `output`、`max_bytes`；合并 stdout/stderr 最新字节，停止后仍可读 |
| `request` | `path: str = "/"`，仅本地路径；`timeout_s: int = 5`，1–30 | 真实回环 GET：`status_code`、UTF-8 `body`（最多 65536 字节）、`truncated`，不跟随重定向 |
| `build` | `cwd: str = ""`；`timeout_s: int = 120`，1–600 | `npm run build`；成功返回 `exit_code: 0`、最新 131072 字节 `output`、`truncated`；失败/超时报错 |
| `smoke` | 无 | 在 3000 启动内置样例，断言真实 HTTP 响应，在 finally 停止，返回 `node-web ready` |

同一时间仅运行一个服务，第二次启动须先 stop。就绪路径只接受 HTTP 200–399，子进程退出即失败。request 仅访问管理中的回环端口。服务日志在独立临时目录中按 1 MiB 轮转，最多两个文件。build 临时文件在结束后删除，返回量有限制，但非常冗长的构建仍会在结束前消耗临时磁盘。进程注册表仅在内存中，重启命令服务会丢失；销毁沙箱是最终清理边界。

## 配置

| 环境变量 | 默认值 | 用途 |
|---|---|---|
| `NODE_ENV` | `production` | 传给应用；开发场景可在创建沙箱时更改 |
| `PORT` | `3000` | 样例默认端口，每次启动由 `port` 参数覆盖 |
| `HOST` | 启动时设为 `0.0.0.0` | 兼容应用的监听提示，应用须自行遵循 |
| `WORKSPACE` | 未设置 | 默认应用目录 |
| `ABX_SERVER_PORT` | `9000` | 本地命令服务端口 |
| `ABX_SERVER_TOKEN` | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

命令无需模型或云密钥。秘密值不得写进源码、镜像、日志。只通过授权运行配置注入，不打印环境变量。应用 stdout 由用户代码决定，可能含敏感信息，应用须自行脱敏，公开 issue 前须审阅日志。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx run "$SANDBOX_ID" stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB 内存。9000 为命令 API，3000 为样例服务；其他端口需网关支持。无需特权、沙箱内 Docker、GPU、KVM、浏览器。应用依赖与产物共享提供方根文件系统预算（Express 约 10 GB）。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/node-web.md)。

## 问题反馈

本模板已有 [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29)，先检索再提交。提供脱敏参数、预期/实际行为、验证级别、提供方、generation 2、SDK 提交。模板问题放 awesome-templates；server/客户端问题放 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题加 `[templates]`；CLI 问题放 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，同样加前缀。禁止附 `.env`、token 或未经审阅的应用日志。

## 许可证

Apache-2.0，见仓库 [LICENSE](../LICENSE)。
