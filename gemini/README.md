# gemini

## 这是什么

这是 Gemini CLI 的 Agent Sandbox 模板。镜像基于 `python:3.12-slim`，安装 Node.js 22，再全局安装 npm 包 `@google/gemini-cli@0.64.0`（2026-10-14 对 registry 执行 `npm view @google/gemini-cli version`，dist-tag `latest` 是 0.64.0）。包提供的命令名是 `gemini`。

沙箱里的 HTTP 服务是 `agent_sandbox.server`，监听 **9000**。具名命令 `gemini` 在被调用时执行非交互的 `gemini -p`。能力是 `shell`、`files`、`code`、`ports`。资源是 2 CPU、4096 MB 内存。

默认模型是该版本里的 `DEFAULT_GEMINI_FLASH_LITE_MODEL`：`gemini-3.1-flash-lite`。状态是 `experimental`。2026-10-14 的 `docker build` 已经在日志里看到 `@google/gemini-cli@0.64.0` 和 `gemini --version` 的 `0.64.0`，记录在 [docs/gemini-image-build.md](../docs/gemini-image-build.md)。带密钥且输出含 `ABX_E2E_OK` 的调用还没有记录。

镜像不写入任何密钥。

## 怎么创建

极速版从模板目录安装、发布，再按名字创建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//gemini
abx deploy
abx create --template gemini --env GEMINI_API_KEY=<你的密钥>
```

`abx template install` 会构建并注册该目录（只要没有加 `--download-only`）。密钥在创建时注入，不要写进 `template.yaml`。

## 怎么调用

发布到极速版之后，用 Python SDK 的具名命令：

```python
result = await sandbox.run("gemini", prompt="用一句话说明当前目录里有什么")
print(result)
```

换模型时多传 `model`：

```python
result = await sandbox.run(
    "gemini",
    prompt="只回复 ABX_E2E_OK",
    model="gemini-3.1-flash-lite",
)
```

CLI：

```bash
abx run <sandbox-id> gemini --json-args '{"prompt":"用一句话说明当前目录里有什么"}'
```

`@command("gemini")` 实际执行的命令行（参数数组，不经过 shell）是：

```text
gemini -p <prompt> --yolo --model <model>
```

`<model>` 取调用参数 `model`；参数为空时用环境变量 `GEMINI_MODEL`；两者都空时用 `gemini-3.1-flash-lite`。`-p` 进入 headless。`--yolo` 自动批准工具调用，它本身不决定是否 headless。标准输入设为 `/dev/null`。超时 600 秒。没有 `GEMINI_API_KEY` 时，命令抛出 `RuntimeError`，不会去启动 CLI。

## 需要的环境变量

| 变量 | 作用 |
| --- | --- |
| `GEMINI_API_KEY` | Gemini API 密钥。模板里是空字符串。命令被调用时如果为空，直接失败。 |
| `GEMINI_MODEL` | 传给 `--model`。模板默认 `gemini-3.1-flash-lite`。 |
| `ABX_SERVER_PORT` | 沙箱内 HTTP 服务端口，默认 `9000`。 |

## 本地 e2e

在仓库根目录，安装 `agent-sandbox-server` 和 `httpx` 之后：

```bash
python3 scripts/run_local_e2e.py
```

该脚本强制 `E2E_RUN_LLM=0`，并且不转发 `GEMINI_API_KEY`。模型调用记为 SKIP。没有 FAIL 时进程退出码是 0。这只说明 `/health`、`/commands` 和缺 `prompt` 时的 4xx 过了。

带密钥的验收在本目录另开两个进程。服务进程和测试进程都要能看到密钥，并且不要设置 `E2E_RUN_LLM=0`：

```bash
GEMINI_API_KEY=<你的密钥> ABX_SERVER_PORT=9000 python3 commands.py
```

```bash
GEMINI_API_KEY=<你的密钥> E2E_REQUIRE_LLM=1 E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```

提示词要求模型只回复 `ABX_E2E_OK`。输出里没有这个标记、密钥为空，或同时又设置了 `E2E_RUN_LLM=0`，都记为 FAIL，退出码为 1。

## 其他 provider

`sandbox.run("gemini", prompt=...)` 只用于已经发布了这份模板、并且提供方有具名命令数据面的沙箱。E2B 上具名命令返回 `E8004`，不要对 E2B 调用 `sandbox.run("gemini", ...)`。本仓库也不把 `gemini` 登记成 E2B 的预置模板 id。

OpenSandbox 上要跑这份镜像时，先推送构建产物，再把镜像地址传给 `Sandbox.create(template="<镜像地址>", provider="opensandbox")`。短名字 `gemini` 不是 OpenSandbox 已发布的沙箱镜像。
