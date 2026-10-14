# qwen-code

## 这是什么

`qwen-code` 是通义千问编码 Agent 的沙箱模板，用 qwen-code CLI 做自然语言部署。镜像基于 `python:3.12-slim`，预装 Python 3.12（`/opt/venv`）、Node.js 22、npm 包 `@qwen-code/qwen-code@0.23.0`，以及 Python 包 `dashscope`、`openai>=1.0`、`httpx`、`rich`。系统工具有 git、curl、wget、ripgrep、jq、build-essential。资源配置是 2 CPU / 4096 MB。容器入口是 `python3 commands.py`，监听 `ABX_SERVER_PORT`（默认 9000）。

命名命令有两个。

`qwen(prompt, max_turns=100)` 在沙箱里执行：

```text
qwen -p <prompt> --yolo --output-format json --max-turns <max_turns>
```

超时 600 秒。工作目录优先用 `/app`；`/app` 不存在时用 `WORKSPACE`，再没有就用进程当前目录。这条命令不接收 `model` 参数，模型由环境变量 `OPENAI_MODEL` 决定。

`run(script="main.py")` 执行 `python3 <script>`，超时 120 秒，工作目录规则和上面相同。

## 本地 e2e 怎么跑

仓库根目录，已安装 `agent-sandbox-server` 和 `httpx`：

```bash
python3 -m pip install agent-sandbox-server httpx
python3 scripts/run_local_e2e.py
```

这条命令会给每个带 `commands.py` 和 `e2e_test.py` 的模板各起一个临时端口，在该目录启动 `python3 commands.py`，设置 `E2E_BASE_URL`，跑完 `e2e_test.py` 再停掉进程。它强制 `E2E_RUN_LLM=0`，并且不把 `OPENAI_API_KEY`、`DASHSCOPE_API_KEY` 传给子进程。

只跑本目录时，先在 `qwen-code/` 启动 server，再另开一个终端跑测试。`E2E_BASE_URL` 必须指向这个已经起来的进程：

```bash
cd qwen-code
ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
cd qwen-code
E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

`commands.py` 不在跑，或者 `E2E_BASE_URL` 和 `ABX_SERVER_PORT` 对不上，`/health` 和 `/commands` 会失败。

## 极速版怎么安装和创建

`abx template install` 只在阿里云极速版（provider `alicloud-express`）上构建镜像并注册模板。

从索引安装并构建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qwen-code
```

在本仓库里从本地目录安装：

```bash
abx template install ./qwen-code --registry-type local
```

只下载到 `~/.abx/templates/`、不构建：

```bash
abx template install ./qwen-code --registry-type local --download-only
```

在模板目录里构建、推送并注册：

```bash
abx deploy
```

创建沙箱。镜像里的 qwen-code 走 OpenAI 兼容接口：`OPENAI_BASE_URL` 已是 DashScope 兼容地址，认证变量是 `OPENAI_API_KEY`。`template.yaml` 里两个密钥都是空字符串。

```bash
abx create --template qwen-code --env OPENAI_API_KEY=<DashScope 密钥>
```

`DASHSCOPE_API_KEY` 可以同时注入，供镜像里的 `dashscope` SDK 使用。只设置 `DASHSCOPE_API_KEY` 不会让 e2e 去调用命名命令 `qwen`。

## 怎么调用命名命令

`qwen` 的参数是 `prompt` 和 `max_turns`。`max_turns` 是整数，用 `--json-args` 把类型交给 server。

```bash
abx run <sandbox-id> qwen --json-args '{"prompt":"部署这个 FastAPI 项目","max_turns":100}'
```

```python
await sandbox.run("qwen", prompt="部署这个 FastAPI 项目", max_turns=100)
```

同步代码用 `sandbox.run_sync("qwen", prompt="...", max_turns=100)`。省略 `max_turns` 时默认 100。

跑仓库里的 Python 脚本用命名命令 `run`，参数是 `script`：

```bash
abx run <sandbox-id> run --arg script=main.py
```

```python
await sandbox.run("run", script="main.py")
```

`abx exec <sandbox-id> -- qwen -p "..." --yolo` 和 `sandbox.commands.run("python3 --version && node --version")` 是直接跑 shell，不会经过 `@command("qwen")` 或 `@command("run")`。

## 需要哪些环境变量

| 变量 | 作用 |
|---|---|
| `OPENAI_API_KEY` | qwen-code CLI 的密钥。e2e 只认这个名字来决定要不要调用 `POST /commands/qwen`。创建沙箱时用 `--env` 注入，并且要出现在 `commands.py` 进程里。 |
| `DASHSCOPE_API_KEY` | `template.yaml` 留空，给 `dashscope` SDK 用。e2e 不把它当作模型用例的开关。 |
| `OPENAI_BASE_URL` | `template.yaml` 写成 `https://dashscope.aliyuncs.com/compatible-mode/v1`。 |
| `OPENAI_MODEL` | `template.yaml` 写成 `qwen3-coder-plus`。`qwen` 命令没有 `model` 参数，换模型改这个环境变量。 |
| `WORKSPACE` | `template.yaml` 写成 `/app`。`/app` 不存在时，`qwen` 和 `run` 用它当工作目录。 |
| `ABX_SERVER_PORT` | server 端口，默认 `9000`。 |
| `E2E_BASE_URL` | 只跑 `e2e_test.py` 时指向已启动的 server，例如 `http://127.0.0.1:9000`。根目录的 `run_local_e2e.py` 会自己设置。 |
| `E2E_RUN_LLM` | `0` 强制跳过 `qwen` 模型调用；`1` 强制去调。默认按有没有 `OPENAI_API_KEY` 决定。根目录脚本固定写成 `0`。 |
| `E2E_MAX_TURNS` | 可选。e2e 发给 `qwen` 的 `max_turns`，默认 `1`。这只影响测试，不改变命令本身的默认值 100。 |

qwen-code 要能访问 `dashscope.aliyuncs.com`，沙箱需要出网。

## 没有密钥时 e2e 会 SKIP

`POST /commands/qwen` 在没有 `OPENAI_API_KEY`，或 `E2E_RUN_LLM=0` 时记为 `SKIP`。只有 `DASHSCOPE_API_KEY` 同样是 `SKIP`。根目录的 `python3 scripts/run_local_e2e.py` 不转发这两个密钥，并且强制 `E2E_RUN_LLM=0`。测试进程退出码 0 只说明 server 的 `/health`、`/commands` 和其余本地检查过了。

这不算 Agent 验收。验收要在沙箱进程里看得到 `OPENAI_API_KEY`（以及模板里已经写好的 `OPENAI_BASE_URL`、`OPENAI_MODEL`），再跑同一份 `e2e_test.py`，让 `qwen` 真正执行。探测提示词是 `Reply with exactly: ABX_E2E_OK`。没有这条带密钥的记录，不能把模板写成已经支持 qwen-code。

## OpenSandbox / E2B

OpenSandbox 和 E2B 上，这个目录不会自动变成对方的模板。`abx template install` 只在极速版构建。OpenSandbox 创建用的是镜像 URI，并且会替换容器入口，仓库里的 `qwen-code/Dockerfile` 不会因此在那边注册。E2B 也不会出现一个叫 `qwen-code` 的 template id。`base`、`code-interpreter-v1`、`desktop` 是平台自己的 id，和这个目录无关。
