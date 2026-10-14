# droid

## 这是什么

这是 Factory Droid 编码 CLI 的 Agent Sandbox 模板。镜像里预装官方 npm 包 `@factory/cli@0.241.1`（命令名 `droid`），版本与官方安装脚本 `https://app.factory.ai/cli` 当前固定的 `VER=0.241.1` 一致。命名命令 `droid` 以参数数组调用无头命令 `droid exec`，提示词是单独的 argv，不拼进 shell 字符串。

## 安装

极速版从模板库安装：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//droid
```

本地目录：

```bash
abx template install ./droid --registry-type local
```

## 使用

创建沙箱时注入 `FACTORY_API_KEY`。不要把密钥写进模板或镜像。

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(
    template="droid",
    env={"FACTORY_API_KEY": "fk-..."},
)
result = sandbox.run("droid", prompt="用一句话说明这个仓库做什么")
print(result)
```

`sandbox.run("droid", prompt=...)` 对应容器内的 `droid exec <prompt>`。未设置 `FACTORY_API_KEY` 时，命令抛出 `RuntimeError`。

## 本地 e2e

在本目录安装 `agent-sandbox-server` 和 `httpx` 后：

```bash
ABX_SERVER_PORT=9000 python3 commands.py
```

另一个终端：

```bash
E2E_RUN_LLM=0 python3 e2e_test.py
```

`e2e_test.py` 用 httpx 检查 `GET /health`、`GET /commands` 是否列出 `droid`，以及缺少 `prompt` 时是否返回客户端错误（HTTP 4xx）。没有 `FACTORY_API_KEY`，或 `E2E_RUN_LLM=0` 时，真实模型调用记为 SKIP。要跑模型调用，在宿主机和沙箱里都提供 `FACTORY_API_KEY`。

## E2B

E2B 预置模板 id 是 `droid`。使用 E2B 提供者时，客户端读取 `ABX_E2B_API_KEY`。

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(
    template="droid",
    provider="e2b",
    env={"FACTORY_API_KEY": "fk-..."},
)
print(sandbox.run("droid", prompt="列出当前目录"))
```

`FACTORY_API_KEY` 是 Droid 调模型用的密钥；`ABX_E2B_API_KEY` 是创建 E2B 沙箱用的密钥。两者都不要写进仓库。
