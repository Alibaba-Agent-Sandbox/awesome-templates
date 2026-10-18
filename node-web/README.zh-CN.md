# node-web

## 做什么

每个沙箱管理一个真实 Node HTTP 应用。`serve` 启动 JavaScript 入口，`start` 和 `dev` 在后台运行 npm 脚本。只有子进程存活并返回 HTTP 2xx/3xx，启动才成功。`status`、`request`、`logs`、`stop` 提供状态、真实请求、日志和停止。内置无第三方依赖的 `index.js`，可直接验证 HTTP 服务。

## 技术栈

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 提供 Node 20 和 Python 3.13；部署默认替换为 `cn-hangzhou`、`v0.0.49`。server 的归档安装锁定 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505`，CLI 注入的 wheel 优先。无额外 npm 依赖。工作目录 `/home/user/app`，以非 root 的 `user` 运行，generation 2。`start_cmd` 在 9000 启动命令服务，`ready_cmd` 做 healthcheck；Dockerfile 无 CMD/ENTRYPOINT。

## 解决的问题

仅创建进程或端口可连接不能证明应用就绪。模板执行 HTTP 检查，持续消费 stdout/stderr，限制服务日志大小，并将 npm 启动器与 Node 子进程一起停止。`build` 执行应用真实构建脚本，非零退出会报错。

## 快速开始（CLI）

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

已有提供方配置时，在仓库根目录执行：

```bash
abx template deploy ./node-web -y
abx create --template <template-id> -y
abx run <sandbox-id> serve --json-args '{"entry":"index.js","port":3000}'
abx run <sandbox-id> request --json-args '{"path":"/"}'
abx run <sandbox-id> logs --json-args '{"max_bytes":16384}'
abx run <sandbox-id> stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

request 返回 `status_code: 200` 和 `body: "node-web ready\n"`。自定义 `entry`/`cwd` 前，上传应用及锁定依赖。`start`/`dev`/`build` 需要项目自己的 `package.json` 脚本，内置样例无需 npm 安装。应用须使用 `PORT` 并绑定 `0.0.0.0`，才能通过提供方网关预览。应用端口默认 3000，命令 API 端口为 9000。

## 快速开始（Python SDK）

客户端发行名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。配套版本发布前，请按[固定提交的双包安装说明](../docs/python-client-installation.md)安装。

```python
import asyncio
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("serve", entry="index.js", port=3000, timeout_s=20))
        result = await sb.run("request", path="/")
        assert result["status_code"] == 200
        assert result["body"] == "node-web ready\n"
        print(sb.network.get_url(3000))
        print(await sb.run("logs", max_bytes=16384))
        await sb.run("stop")
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 返回 HTTP `result` 内的值。`sb.commands.run` 为独立 shell/进程 API。长构建需让 HTTP `timeout` 大于执行参数 `timeout_s`，如 `await sb.run("build", cwd="/home/user/app/my-app", timeout_s=120, timeout=150)`。`timeout_s` 是执行/就绪期限；客户端 `timeout` 只限制请求，超时不保证取消。需断线重连的长任务请使用进程 API。

## 快速开始（HTTP POST）

将 `SERVER_URL` 设为沙箱端口 9000 的提供方 URL（`sb.network.get_url(9000)`），本地 L0 使用 `http://127.0.0.1:9000`。JSON 直接传参数对象，无 `args` 包装：

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/serve" \
  -H 'Content-Type: application/json' -d '{"entry":"index.js","port":3000,"timeout_s":20}'
curl --fail-with-body -X POST "$SERVER_URL/commands/request" \
  -H 'Content-Type: application/json' -d '{"path":"/"}'
curl --fail-with-body -X POST "$SERVER_URL/commands/stop" \
  -H 'Content-Type: application/json' -d '{}'
```

请求结果：`{"result":{"status_code":200,"body":"node-web ready\n","truncated":false}}`。serve 返回 `pid`、`port`、`status`、`cwd`、`http_status`；stop 返回 `status` 与 `pid`。

沙箱中配置 `ABX_SERVER_TOKEN` 后，每次命令请求须添加 `Authorization: Bearer $ABX_SERVER_TOKEN` 或 `X-Access-Token: $ABX_SERVER_TOKEN`。Python 使用 `sb.server_at(9000, token=server_token).commands.run(...)`，token 与该服务启动前获得的值一致。提供方网关鉴权独立：按该提供方要求添加访问头（Express 为 `X-Access-Token: $SANDBOX_ACCESS_TOKEN`）。同时启用时，server token 放 `Authorization`，网关 token 放 `X-Access-Token`。仅从已授权运行配置取得值，示例不含真实凭据。

错误体为 `{"error":"...","type":"..."}`：参数缺失、类型错误、未知参数为 400；server 鉴权失败 401；未知命令 404；命令执行失败 500（包括数值越界、端口占用、构建失败、就绪超时）。命令结果一次缓冲返回。应用本身返回 HTTP 404 时，命令 API 仍是 HTTP 200，应用码位于 `request.result.status_code`。

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
| `ABX_SERVER_TOKEN` | 空 | 可选 server 鉴权，仅以空值声明密钥名 |

命令无需模型或云密钥。秘密值不得写进源码、镜像、日志。只通过授权运行配置注入，不打印环境变量。应用 stdout 由用户代码决定，可能含敏感信息，应用须自行脱敏，公开 issue 前须审阅日志。

## 资源

2 vCPU、2048 MB 内存。9000 为命令 API，3000 为样例服务；其他端口需网关支持。无需特权、沙箱内 Docker、GPU、KVM、浏览器。应用依赖与产物共享提供方根文件系统预算（Express 约 10 GB）。

## 已验证

尚未记录任何通过的提供方测试。

2026-10-16 本地 L0 使用真实 Node 22.22.2、隔离 npm 10.9.4、agent-sandbox-server 0.3.0、httpx 0.28.1，60 项断言全部通过：HTTP API 发现、就绪前 4 MiB 高输出、真实 HTTP 请求、stderr 日志、npm 构建产物、start/dev 及进程组停止后端口重用、构建非零/超时、就绪失败。该结果仅为本地主机验证，未证明 Node 20 镜像或云端行为。Docker 缺失，L1 待运行；L2/L4 待运行，`tested_on` 保持空。服务模板不需要模型调用。

## Express 源码运行验证

2026-10-16，改动后的源码在自有 Express base 的真实 Node.js 20 中通过全部 60 项外部 HTTP 断言，覆盖样例 smoke、上传应用的构建/start/dev、HTTP 就绪、日志边界、退出、端口复用及清理。自有实例已销毁。[JSON 证据](evidence/runtime-express-2026-10-16.json)记录源码、配置、fixture 和 wheel 哈希，[HTTP 结果](evidence/runtime-express-2026-10-16.log)记录断言。此结果不等于 Dockerfile 构建或新模板镜像部署，`tested_on` 保持为空；见[共享工具](../docs/express-source-runtime.md)。

## 二次开发

HTTP 验收脚本为每项断言输出 `[PASS]` 或 `[FAIL]` 行。外层验收要求退出0、无失败
且通过计数大于0；即使退出0，识别到零项断言也会被拒。运行
`python -m pytest --import-mode=importlib -q node-web/test_http_output.py`，可执行真实
本地 server/Node/npm 的完整60项套件，再使用相同严格计数器检查；另用真实 HTTP503
fixture 检查非零退出和可识别失败。测试仅使用自有临时 npm cache，保留原 HOME，
无需安装依赖或调用模型。此前无方括号输出的云验收仍保留为计数协议不兼容而被拒收，
不会追改为通过。

把项目上传至 `/home/user/app` 下并提交依赖锁文件。衍生镜像用 `npm ci` 从锁文件安装精确版本；依赖安装放在最终 `COPY commands.py` 之前，npm 缓存在同层清理。保留锁定 server、Alibaba 基础镜像、非 root 用户、generation 2 的启动/就绪命令，无 Docker CMD/ENTRYPOINT。Express/Fastify 可用 serve，或提供 start/dev/build 脚本。模板不预装框架，不创建 Next/Vite 项目。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计分析](../docs/design/node-web.md)。在仓库根运行 `python3 scripts/check_template.py node-web`，再运行 `python3 scripts/run_local_e2e.py`；需 server SDK、httpx、PyYAML、Node 与 npm。测试运行真实进程并断言结果。具备 Docker 与已授权 Express 配置时运行 `python3 scripts/express_e2e.py node-web`，仅通过后添加提供方证据。在此之前保持 tested_on 与提供方验证列表为空。合并前交叉审查进程生命周期与失败路径。

## 问题反馈

本模板已有 [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29)，先检索再提交。提供脱敏参数、预期/实际行为、验证级别、提供方、generation 2、SDK 提交。模板问题放 awesome-templates；server/客户端问题放 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题加 `[templates]`；CLI 问题放 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，同样加前缀。禁止附 `.env`、token 或未经审阅的应用日志。

## 许可证

Apache-2.0，见仓库 [LICENSE](../LICENSE)。
