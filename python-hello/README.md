# python-hello

> [中文版](#中文) | [English](#english)

---

## English

A minimal Python development environment template.

### Installation

```bash
abx template install ./python-hello --registry-type local
```

### Usage

```bash
abx create --template python-hello
```

#### Named Commands (End-to-End)

After the container starts, `commands.py` runs automatically, listens on port 9000, and provides the following named commands:

```bash
# Greet
abx run <sandbox-id> hello --name Alice
# → Hello, Alice!

# Run Python code
abx run <sandbox-id> run_script --code "print(1+1)"
# → 2
```

Equivalent SDK usage:

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(template="python-hello")
result = sandbox.run_sync("hello", name="Alice")
print(result)  # Hello, Alice!
```

#### Upload / Download

```bash
abx upload <sandbox-id> ./local_file.txt /app/remote.txt
abx download <sandbox-id> /app/remote.txt ./local_file.txt
```

### Environment

- Base image: python:3.12-slim
- Python 3.12 and pip; in-sandbox package `agent-sandbox-server`
- Working directory: /app

---

## 中文

基础 Python 开发环境模板。

### 安装

```bash
abx template install ./python-hello --registry-type local
```

### 使用

```bash
abx create --template python-hello
```

#### 命名命令（端到端）

容器启动后会自动运行 `commands.py`，监听端口 9000，提供以下命名命令：

```bash
# 打招呼
abx run <sandbox-id> hello --name Alice
# → Hello, Alice!

# 执行 Python 代码
abx run <sandbox-id> run_script --code "print(1+1)"
# → 2
```

SDK 侧等价写法：

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(template="python-hello")
result = sandbox.run_sync("hello", name="Alice")
print(result)  # Hello, Alice!
```

#### 上传 / 下载

```bash
abx upload <sandbox-id> ./local_file.txt /app/remote.txt
abx download <sandbox-id> /app/remote.txt ./local_file.txt
```

### 环境

- 基础镜像: python:3.12-slim
- Python 3.12 and pip; in-sandbox package `agent-sandbox-server`
- 工作目录: /app

## Deploy and local e2e

Install and register this template:

```bash
abx template install alibaba-agent-sandbox/awesome-templates//python-hello
```

From this directory (build, push, and register):

```bash
abx deploy
```

From the repository root, with `agent-sandbox-server` and `httpx` installed:

```bash
python3 scripts/run_local_e2e.py
```

That starts `python3 commands.py` in this directory and runs `e2e_test.py`.

