# amp

## 这是什么

这是 Sourcegraph Amp 编码 CLI 的 Agent Sandbox 模板。镜像基于 `python:3.12-slim`，用 Server SDK（`agent_sandbox.server`）在 9000 端口提供 HTTP 服务。

镜像里预装：

| 类别 | 内容 |
|------|------|
| Node.js | 22.x（NodeSource `setup_22.x`） |
| Amp CLI | `@ampcode/cli@0.0.1791964847-g13f24a`，命令名 `amp` |
| 系统工具 | git、curl、ca-certificates、ripgrep |
| 资源 | 2 CPU / 4096 MB 内存 |

`amp` 命令在沙箱里执行的 argv 是 `amp --dangerously-allow-all -x <prompt>`。`prompt` 是单独的参数，不经过 shell。

## 极速版创建

在阿里云极速版上，先安装模板再创建沙箱：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//amp
abx create --template amp --env AMP_API_KEY=REPLACE_ME
```

## 怎么调用

命名命令用 `sandbox.run("amp", prompt=...)`。这是 `POST /commands/amp`，返回值是 CLI 的标准输出。

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sandbox = await Sandbox.create(
        template="amp",
        env={"AMP_API_KEY": "REPLACE_ME"},
    )
    try:
        result = await sandbox.run("amp", prompt="用 Python 写一个返回 200 的 HTTP 服务")
        print(result)
    finally:
        await sandbox.kill()

asyncio.run(main())
```

命令行对应：

```bash
abx run <sandbox-id> amp --arg prompt="用 Python 写一个返回 200 的 HTTP 服务"
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `AMP_API_KEY` | Amp 的 API 密钥。在创建沙箱时注入。模板里的值是空字符串，密钥不会写进镜像。未设置或只有空白时，`amp` 命令抛出 `RuntimeError`，错误信息包含 `AMP_API_KEY`，并且不会启动 CLI。 |

## 本地 e2e

在模板目录安装依赖并启动服务：

```bash
pip install agent-sandbox-server httpx
python3 commands.py
```

另一个终端运行：

```bash
python3 e2e_test.py
```

`E2E_BASE_URL` 默认是 `http://127.0.0.1:9000`。脚本只用 `httpx`，会检查 `GET /health`、`GET /commands` 是否包含 `amp`，以及不带 `prompt` 的 `POST /commands/amp` 是否为客户端错误。

`E2E_RUN_LLM=0` 或环境里没有 `AMP_API_KEY` 时，LLM 调用记为 `SKIP`。只有某项检查是 `FAIL` 时进程才以非 0 退出；全部通过或跳过时退出码为 0。

要真正调用 Amp：

```bash
AMP_API_KEY=REPLACE_ME python3 e2e_test.py
```

密钥必须同时出现在跑测试的环境里，以及正在跑 `commands.py` 的进程里。

## E2B

E2B 上模板 id 是 amp，创建沙箱时只用 `ABX_E2B_API_KEY`。Amp CLI 的密钥仍是 `AMP_API_KEY`，在创建时注入沙箱。

```python
sandbox = await Sandbox.create(
    provider="e2b",
    template="amp",
    env={"AMP_API_KEY": "REPLACE_ME"},
)
result = await sandbox.run("amp", prompt="用 Python 写一个返回 200 的 HTTP 服务")
```
