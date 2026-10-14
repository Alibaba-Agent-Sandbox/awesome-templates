# claude-code

## 这是什么

`claude-code` 是 Anthropic Claude Code 的沙箱模板。镜像基于 `python:3.12-slim`，预装 Node.js 22、Python 3.12（虚拟环境在 `/opt/venv`）、npm 包 `@anthropic-ai/claude-code`，以及 Python 包 `anthropic`、`httpx`、`rich`。系统工具有 git、curl、ripgrep、build-essential。资源配置是 2 CPU / 4096 MB。容器入口是 `python3 commands.py`，进程内用 `agent_sandbox.server` 注册命名命令，监听 `ABX_SERVER_PORT`（默认 9000）。

命名命令只有一个：`claude`。它在沙箱里执行：

```text
claude -p <prompt> --model <model> --output-format json
```

超时 300 秒。`prompt` 必填，`model` 默认 `sonnet`。

## 本地 e2e 怎么跑

仓库根目录，已安装 `agent-sandbox-server` 和 `httpx`：

```bash
python3 -m pip install agent-sandbox-server httpx
python3 scripts/run_local_e2e.py
```

这条命令会给每个带 `commands.py` 和 `e2e_test.py` 的模板各起一个临时端口，在该目录启动 `python3 commands.py`，设置 `E2E_BASE_URL`，跑完 `e2e_test.py` 再停掉进程。它强制 `E2E_RUN_LLM=0`，并且不把 `ANTHROPIC_API_KEY` 等密钥传给子进程。

只跑本目录时，先在 `claude-code/` 启动 server，再另开一个终端跑测试。`E2E_BASE_URL` 必须指向这个已经起来的进程：

```bash
cd claude-code
ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
cd claude-code
E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

`commands.py` 不在跑，或者 `E2E_BASE_URL` 和 `ABX_SERVER_PORT` 对不上，`/health` 和 `/commands` 会失败。

## 极速版怎么安装和创建

`abx template install` 只在阿里云极速版（provider `alicloud-express`）上构建镜像并注册模板。

从索引安装并构建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//claude-code
```

在本仓库里从本地目录安装：

```bash
abx template install ./claude-code --registry-type local
```

只下载到 `~/.abx/templates/`、不构建：

```bash
abx template install ./claude-code --registry-type local --download-only
```

在模板目录里构建、推送并注册：

```bash
abx deploy
```

创建沙箱并注入密钥（密钥不要写进镜像或 `template.yaml`，`template.yaml` 里 `ANTHROPIC_API_KEY` 的值是空字符串）：

```bash
abx create --template claude-code --env ANTHROPIC_API_KEY=<你的密钥>
```

## 怎么调用命名命令

命名命令走 `abx run` 或 `sandbox.run`。参数名就是 `commands.py` 里的 `prompt` 和 `model`。`abx run` 用 `--arg KEY=VALUE`，整数或混合类型用 `--json-args`。这不是 shell。

```bash
abx run <sandbox-id> claude --arg prompt="编写一个 Python HTTP 服务器" --arg model=sonnet
```

```python
await sandbox.run("claude", prompt="编写一个 Python HTTP 服务器", model="sonnet")
```

同步代码用 `sandbox.run_sync("claude", prompt="...", model="sonnet")`。省略 `model` 时 server 使用默认值 `sonnet`。

`abx exec <sandbox-id> -- claude -p "..."` 和 `sandbox.commands.run("claude -p '...'")` 是直接跑 shell，不会经过 `@command("claude")`。

## 需要哪些环境变量

| 变量 | 作用 |
|---|---|
| `ANTHROPIC_API_KEY` | Claude Code CLI 的密钥。创建沙箱时用 `--env` 注入。`e2e_test.py` 只有在跑测试的进程里看得到这个变量，才会去调 `POST /commands/claude`。密钥还必须出现在 `commands.py` 那个进程的环境里，CLI 才读得到。 |
| `WORKSPACE` | `template.yaml` 写成 `/app`。`claude` 这条命令本身不读它。 |
| `ABX_SERVER_PORT` | server 端口，默认 `9000`。 |
| `E2E_BASE_URL` | 只跑 `e2e_test.py` 时指向已启动的 server，例如 `http://127.0.0.1:9000`。根目录的 `run_local_e2e.py` 会自己设置。 |
| `E2E_RUN_LLM` | `0` 强制跳过模型调用；`1` 强制去调。默认按有没有 `ANTHROPIC_API_KEY` 决定。根目录脚本固定写成 `0`。 |
| `E2E_MODEL` | 可选。设了就作为 `model` 参数发给 `claude`，不设就用命令默认值 `sonnet`。 |

Claude Code 要能访问 Anthropic API，沙箱需要出网。

## 没有密钥时 e2e 会 SKIP

`POST /commands/claude` 这条用例在没有 `ANTHROPIC_API_KEY`，或 `E2E_RUN_LLM=0` 时记为 `SKIP`。根目录的 `python3 scripts/run_local_e2e.py` 两种情况都占了：它不转发密钥，并且强制 `E2E_RUN_LLM=0`。测试进程退出码 0 只说明 server 的 `/health`、`/commands` 和其余本地检查过了。

这不算 Agent 验收。验收要在沙箱进程里看得到 `ANTHROPIC_API_KEY`，再跑同一份 `e2e_test.py`，让 `claude` 真正执行。探测提示词是 `Reply with exactly: ABX_E2E_OK`。没有这条带密钥的记录，不能把模板写成已经支持 Claude Code。

## OpenSandbox / E2B

OpenSandbox 和 E2B 上，这个目录不会自动变成对方的模板。`abx template install` 只在极速版构建。OpenSandbox 创建用的是镜像 URI，并且会替换容器入口，仓库里的 `claude-code/Dockerfile` 不会因此在那边注册。E2B 也不会出现一个叫 `claude-code` 的 template id。`base`、`code-interpreter-v1`、`desktop` 是平台自己的 id，和这个目录无关。
