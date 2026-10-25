# node-web

## 做什么

每个沙箱管理一个真实 Node HTTP 应用。`serve` 启动 JavaScript 入口，`start` 和 `dev` 在后台运行 npm 脚本。只有子进程存活并返回 HTTP 2xx/3xx，启动才成功。`status`、`request`、`logs`、`stop` 提供状态、真实请求、日志和停止。内置无第三方依赖的 `index.js`，可直接验证 HTTP 服务。

## 技术栈

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 提供 Node 20 和 Python 3.13；部署默认替换为 `cn-hangzhou`、`v0.0.49`。server 的归档安装锁定 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505`，CLI 注入的 wheel 优先。无额外 npm 依赖。工作目录 `/home/user/app`，以非 root 的 `user` 运行，generation 2。`start_cmd` 在 9000 启动命令服务，`ready_cmd` 做 healthcheck；Dockerfile 无 CMD/ENTRYPOINT。

## 解决的问题

仅创建进程或端口可连接不能证明应用就绪。模板执行 HTTP 检查，持续消费 stdout/stderr，限制服务日志大小，并将 npm 启动器与 Node 子进程一起停止。`build` 执行应用真实构建脚本，非零退出会报错。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./node-web --yes
abx run <sandbox-id> smoke --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('smoke'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/smoke`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "node-web ready"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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
| `ABX_SERVER_TOKEN` | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

命令无需模型或云密钥。秘密值不得写进源码、镜像、日志。只通过授权运行配置注入，不打印环境变量。应用 stdout 由用户代码决定，可能含敏感信息，应用须自行脱敏，公开 issue 前须审阅日志。

## 资源

2 vCPU、2048 MB 内存。9000 为命令 API，3000 为样例服务；其他端口需网关支持。无需特权、沙箱内 Docker、GPU、KVM、浏览器。应用依赖与产物共享提供方根文件系统预算（Express 约 10 GB）。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

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

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py node-web`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计分析](../docs/design/node-web.md)。在仓库根运行 `python3 scripts/check_template.py node-web`，再运行 `python3 scripts/run_local_e2e.py`；需 server SDK、httpx、PyYAML、Node 与 npm。测试运行真实进程并断言结果。具备 Docker 与已授权 Express 配置时运行 `python3 scripts/express_e2e.py node-web`，仅通过后添加提供方证据。在此之前保持 tested_on 与提供方验证列表为空。合并前交叉审查进程生命周期与失败路径。

## 问题反馈

本模板已有 [awesome-templates#29](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/29)，先检索再提交。提供脱敏参数、预期/实际行为、验证级别、提供方、generation 2、SDK 提交。模板问题放 awesome-templates；server/客户端问题放 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题加 `[templates]`；CLI 问题放 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，同样加前缀。禁止附 `.env`、token 或未经审阅的应用日志。

## 许可证

Apache-2.0，见仓库 [LICENSE](../LICENSE)。
