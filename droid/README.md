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

`e2e_test.py` 用 httpx 检查 `GET /health`、`GET /commands` 是否列出 `droid`，以及缺少 `prompt` 时是否返回客户端错误（HTTP 4xx）。`E2E_RUN_LLM=0` 时模型调用记为 SKIP。带密钥的验收设置 `E2E_REQUIRE_LLM=1`，服务进程和测试进程都要有 `FACTORY_API_KEY`，输出里必须有 `ABX_E2E_OK`。密钥为空则 FAIL。

## E2B

E2B 上如果已经存在模板 id `droid`，创建沙箱时客户端读取 `ABX_E2B_API_KEY`。`FACTORY_API_KEY` 是 Droid 调模型用的密钥，在创建时注入沙箱。两者都不要写进仓库。E2B 没有沙箱内具名命令，`sandbox.run("droid", prompt=...)` 会得到 `E8004`。那张预置沙箱里要直接执行 `droid exec`，用 `sandbox.commands.run`。`sandbox.run("droid", prompt=...)` 只用在极速版发布后的本模板上。
