# openclaw

## 这是什么

`openclaw` 是 OpenClaw 开源 AI 编程 Agent 的沙箱模板，提供网关运行时。镜像基于 `python:3.12-slim`，预装 Node.js 22 和 npm 包 `openclaw`。系统工具有 git、curl。资源配置是 2 CPU / 4096 MB。容器入口是 `python3 commands.py`，监听 `ABX_SERVER_PORT`（默认 9000）。OpenClaw Gateway 使用端口 18789。

命名命令只有一个：`gateway`。它在沙箱里执行：

```text
openclaw <action>
```

`action` 默认 `start`，超时 60 秒。所以默认调用就是 `openclaw start`。

## 本地 e2e 怎么跑

仓库根目录，已安装 `agent-sandbox-server` 和 `httpx`：

```bash
python3 -m pip install agent-sandbox-server httpx
python3 scripts/run_local_e2e.py
```

这条命令会给每个带 `commands.py` 和 `e2e_test.py` 的模板各起一个临时端口，在该目录启动 `python3 commands.py`，设置 `E2E_BASE_URL`，跑完 `e2e_test.py` 再停掉进程。它会丢掉名称以 `_TOKEN`、`_API_KEY`、`_SECRET` 结尾的环境变量，因此 `OPENCLAW_GATEWAY_TOKEN` 不会进子进程。

只跑本目录时，先在 `openclaw/` 启动 server，再另开一个终端跑测试。`E2E_BASE_URL` 必须指向这个已经起来的进程：

```bash
cd openclaw
ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
cd openclaw
E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

`commands.py` 不在跑，或者 `E2E_BASE_URL` 和 `ABX_SERVER_PORT` 对不上，`/health` 和 `/commands` 会失败。

## 极速版怎么安装和创建

`abx template install` 只在阿里云极速版（provider `alicloud-express`）上构建镜像并注册模板。

从索引安装并构建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//openclaw
```

在本仓库里从本地目录安装：

```bash
abx template install ./openclaw --registry-type local
```

只下载到 `~/.abx/templates/`、不构建：

```bash
abx template install ./openclaw --registry-type local --download-only
```

在模板目录里构建、推送并注册：

```bash
abx deploy
```

创建沙箱。`template.yaml` 里 `ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY` 都是空字符串，按要用的后端注入其中一个：

```bash
abx create --template openclaw --env ANTHROPIC_API_KEY=<你的密钥>
```

```bash
abx create --template openclaw --env OPENAI_API_KEY=<你的密钥>
```

要让 e2e 真正执行 `gateway` 的 `start`，创建时还要带上 `OPENCLAW_GATEWAY_TOKEN`。这个名字不在 `template.yaml` 里，`commands.py` 也不读取它；`openclaw` 进程继承沙箱环境，e2e 在测试进程里检查它。

```bash
abx create --template openclaw --env ANTHROPIC_API_KEY=<你的密钥> --env OPENCLAW_GATEWAY_TOKEN=<网关令牌>
```

## 怎么调用命名命令

命名命令的名字是 `gateway`，参数是 `action`。不是把 shell 里的 `openclaw` 当成命令名。

```bash
abx run <sandbox-id> gateway --arg action=start
```

```python
await sandbox.run("gateway", action="start")
```

同步代码用 `sandbox.run_sync("gateway", action="start")`。省略 `action` 时 server 使用默认值 `start`。

`abx exec <sandbox-id> -- openclaw --help` 和 `sandbox.commands.run("openclaw --version")` 是直接跑 shell，不会经过 `@command("gateway")`。

## 需要哪些环境变量

| 变量 | 作用 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic 后端密钥。`template.yaml` 留空。和 `OPENAI_API_KEY` 二选一即可驱动 OpenClaw 的模型后端。 |
| `OPENAI_API_KEY` | OpenAI 后端密钥。`template.yaml` 留空。 |
| `OPENCLAW_GATEWAY_TOKEN` | 网关令牌。e2e 没看到它，`POST /commands/gateway (start)` 记为 `SKIP`。令牌要在 `openclaw` 进程的环境里，网关才能真正起来。 |
| `WORKSPACE` | `template.yaml` 写成 `/app`。`gateway` 这条命令本身不读它。 |
| `ABX_SERVER_PORT` | 命名命令 server 的端口，默认 `9000`。Gateway 业务端口是 18789，两者不是同一个端口。 |
| `E2E_BASE_URL` | 只跑 `e2e_test.py` 时指向已启动的 server，例如 `http://127.0.0.1:9000`。根目录的 `run_local_e2e.py` 会自己设置。 |
| `E2E_WORKSPACE` | 可选。文件往返用例用来探测可写目录；探测不到就跳过文件用例。 |

OpenClaw 要能访问所选模型服务商的 API，沙箱需要出网。

## 没有密钥时 e2e 会 SKIP

没有 `OPENCLAW_GATEWAY_TOKEN` 时，`POST /commands/gateway (start)` 记为 `SKIP`，不会把网关启动记成通过。根目录的 `python3 scripts/run_local_e2e.py` 会剥掉 `*_TOKEN`，所以这条在全量本地 e2e 里一定是 `SKIP`。主机上如果 `PATH` 里没有 `openclaw` 二进制，`POST /shell which openclaw` 也是 `SKIP`。测试进程退出码 0 只说明 `/health`、`/commands` 里能看到 `gateway`，以及无效 `action` 能返回。

这不算 Agent 验收。验收要在沙箱里看得到 `OPENCLAW_GATEWAY_TOKEN`（以及实际要用的 `ANTHROPIC_API_KEY` 或 `OPENAI_API_KEY`），再让 `gateway` 的 `start` 真正跑通。没有这条记录，不能把模板写成已经支持 OpenClaw。

## OpenSandbox / E2B

OpenSandbox 和 E2B 上，这个目录不会自动变成对方的模板。`abx template install` 只在极速版构建。OpenSandbox 创建用的是镜像 URI，并且会替换容器入口，仓库里的 `openclaw/Dockerfile` 不会因此在那边注册，端口 18789 也不会自动映射成 OpenSandbox 的模板定义。E2B 也不会出现一个叫 `openclaw` 的 template id。
