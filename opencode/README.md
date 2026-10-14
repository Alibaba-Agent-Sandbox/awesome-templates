# opencode

## 这是什么

这是 OpenCode 编程 Agent 的 Agent Sandbox 模板。镜像基于 `python:3.12-slim`，用 NodeSource 的 `setup_22.x` 安装 Node.js 22，再全局安装 npm 包 `opencode-ai@1.19.0`（2026-10-14 对 registry 执行 `npm view opencode-ai version`，dist-tag `latest` 是 1.19.0）。包提供的命令名是 `opencode`。

沙箱里的 HTTP 服务是 `agent_sandbox.server`，监听 **9000**。具名命令 `opencode` 在被调用时执行非交互的 `opencode run`。能力是 `shell`、`files`、`code`、`ports`。资源是 2 CPU、4096 MB 内存。

默认模型是 OpenCode Zen 文档里的免费模型 **Big Pickle**，选择器写成 `opencode/big-pickle`（<https://opencode.ai/docs/zen/>）。`opencode-ai@1.19.0` 自带的 Zen 目录里，provider `opencode` 的模型 `big-pickle` 输入和输出标价都是 0，凭证环境变量是 `OPENCODE_API_KEY`。OpenSandbox 示例里写过的 `opencode/deepseek-v4-flash-free` 是已经结束的限时活动，这里不用它。

镜像不写入任何密钥。

## 怎么创建

极速版从模板目录安装、发布，再按名字创建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//opencode
abx deploy
abx create --template opencode --env OPENCODE_API_KEY=<你的密钥>
```

`abx template install` 会构建并注册该目录（只要没有加 `--download-only`）。`abx deploy` 发布当前模板目录。`abx create --template opencode` 用发布后的名字启动沙箱。密钥在创建时注入，不要写进 `template.yaml`。

## 怎么调用

服务起来之后，用 Python SDK 的具名命令：

```python
result = await sandbox.run("opencode", prompt="用一句话说明当前目录里有什么")
print(result)
```

换模型时多传 `model`：

```python
result = await sandbox.run(
    "opencode",
    prompt="只回复 ABX_E2E_OK",
    model="opencode/big-pickle",
)
```

CLI：

```bash
abx run <sandbox-id> opencode --json-args '{"prompt":"用一句话说明当前目录里有什么"}'
```

`@command("opencode")` 实际执行的命令行（参数数组，不经过 shell）是：

```text
opencode run --format json --auto --model <model> "$OPENCODE_PROMPT"
```

`<model>` 取调用参数 `model`；参数为空时用环境变量 `OPENCODE_MODEL`；两者都空时用 `opencode/big-pickle`。提示词先写入子进程环境变量 `OPENCODE_PROMPT`，再作为最后一个参数传给 CLI，不会拼进 shell 字符串。`--format json` 让 CLI 打出原始 JSON 事件，`--auto` 自动批准未被明确拒绝的权限，避免非交互运行停在确认上。标准输入设为 `/dev/null`，因为 `opencode run` 在非 TTY 上会读取 stdin。工作目录在 `/app` 存在时用 `/app`。超时 600 秒。入口进程是 `python3 commands.py`。

## 需要的环境变量

| 变量 | 作用 |
| --- | --- |
| `OPENCODE_API_KEY` | OpenCode Zen（provider id `opencode`）的密钥。模板里是空字符串，创建沙箱时再注入。命令被调用时，即使这个变量为空，也会去跑 CLI。CLI 因缺少密钥失败时，抛出的 `RuntimeError` 会写明 `OPENCODE_API_KEY`。 |
| `OPENCODE_MODEL` | `provider/model`。模板默认 `opencode/big-pickle`，即 OpenCode Zen 文档中的免费模型 Big Pickle。调用参数 `model` 可以覆盖它。 |
| `ABX_SERVER_PORT` | 沙箱内 HTTP 服务端口，默认 `9000`。 |

`OPENCODE_DISABLE_AUTOUPDATE=true` 写在镜像里，避免已固定的 1.19.0 在启动时自行升级。

## 本地 e2e

在 `awesome-templates` 仓库根目录，安装 `agent-sandbox-server` 和 `httpx` 之后：

```bash
python3 scripts/run_local_e2e.py
```

该脚本会为每个含 `commands.py` 和 `e2e_test.py` 的目录启动 `python3 commands.py`，设置 `E2E_BASE_URL`，再运行对应的 `e2e_test.py`。它不转发模型密钥，因此真实模型调用会 SKIP。没有 FAIL 时进程退出码是 0。

只跑本目录时，先起服务，再跑测试：

```bash
E2E_RUN_LLM=0 ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
E2E_BASE_URL=http://127.0.0.1:9000 E2E_RUN_LLM=0 python3 e2e_test.py
```

`e2e_test.py` 只用 `httpx`。它检查 `GET /health`、`GET /commands` 是否列出 `opencode`，以及不带 `prompt` 的 `POST /commands/opencode` 是否返回 4xx。`E2E_RUN_LLM` 为 `0` 时，真实模型调用打印 SKIP。存在 FAIL 时退出码为 1。

带密钥的验收设置 `E2E_REQUIRE_LLM=1`。服务进程和测试进程都要能看到 `OPENCODE_API_KEY`，并且不要把 `E2E_RUN_LLM` 设为 `0`。输出里必须包含 `ABX_E2E_OK`。密钥为空、没有标记，或 `E2E_REQUIRE_LLM=1` 又设置了 `E2E_RUN_LLM=0`，都是 FAIL。

## OpenSandbox 与 E2B 上怎么用这个名字

模板名字是 `opencode`。

**E2B。** E2B 预置模板 id 就是 `opencode`。Python SDK 这样创建：

```python
import os
from agent_sandbox import Sandbox

sandbox = await Sandbox.create(
    template="opencode",
    provider="e2b",
    provider_options={"api_key": os.environ["ABX_E2B_API_KEY"]},
)
```

密钥用 `ABX_E2B_API_KEY`。极速版密钥 `ABX_SANDBOX_API_KEY` 不会发给 E2B，这个提供方也不读旧名字 `E2B_API_KEY`。E2B 预置镜像是 E2B 自己的 OpenCode 环境，不是这份 Dockerfile。E2B 适配器没有沙箱内具名命令（`sessions` 返回 `E8004`），在那张预置沙箱里直接执行 `opencode run`。`sandbox.run("opencode", prompt=...)` 用在发布后的本模板上（极速版 `abx create --template opencode`）。

**OpenSandbox。** 官方示例在 code-interpreter 镜像里执行 `npm install -g opencode-ai`，再用 `opencode run`，不使用这份 Dockerfile，也不把裸名字 `opencode` 当成镜像。OpenSandbox 提供方里，`template="base"` 是 `python:3.12-slim`；带 `:` 或 `/` 的 template 按镜像地址使用。要在 OpenSandbox 上跑这份镜像，把发布后的镜像地址传给 `Sandbox.create(template="<镜像地址>", provider="opensandbox")`。本机引擎默认地址是 `ABX_OPENSANDBOX_BASE_URL`（`http://127.0.0.1:8080`）。CLI 目前不加载 `opensandbox` 提供方。
