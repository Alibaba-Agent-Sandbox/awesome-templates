# qoder

> [中文版](#中文) | [English](#english)

---

## English

Sandbox runtime for the Qoder AI coding assistant — an intelligent development sandbox combining Python 3.12 and Node.js 22.

### Environment

This template comes preinstalled with the following tools and dependencies:

| Category | Details |
|----------|---------|
| **Base image** | python:3.12-slim |
| **Python** | Python 3.12 + venv (at `/opt/venv`) |
| **Node.js** | Node.js 22.x + npm |
| **Python packages** | `httpx`, `rich`, `pyyaml` |
| **System tools** | git, curl, wget, ripgrep, jq, build-essential, openssh-client |
| **Resources** | 2 CPU / 4096 MB memory |

### Installation

**Install from a local path:**

```bash
abx template install ./qoder --registry-type local
```

**Install from GitHub:**

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qoder
```

### Usage

Create a sandbox instance:

```bash
abx create --template qoder
```

Run development tasks inside the sandbox:

```bash
abx exec <sandbox-id> -- python3 -c "print('Hello from Qoder sandbox')"
abx exec <sandbox-id> -- node -e "console.log('Node.js ready')"
```

Using the Python SDK:

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(
    template="qoder",
    env={"WORKSPACE": "/app"}
)

result = sandbox.commands.run("python3 --version && node --version")
print(result.stdout)
```

### Configuration

#### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WORKSPACE` | Working directory inside the sandbox. Default `/app`. | No |

#### Custom Configuration

To install extra dependencies on top of this template, run the following after the sandbox is created:

```bash
abx exec <sandbox-id> -- pip install <package-name>
abx exec <sandbox-id> -- npm install -g <package-name>
```

### Notes

- **Working directory**: `WORKSPACE` defaults to `/app`.
- **Dual runtimes**: The environment supports both Python 3.12 and Node.js 22 — pick whichever fits your project.
- **Virtual environment**: Python packages are installed in `/opt/venv`; no manual activation is needed since `PATH` is preconfigured.
- **SSH support**: `openssh-client` is preinstalled, enabling Git-over-SSH operations.

---

## 中文

Qoder AI 编程助手的沙箱运行环境，集成 Python 3.12 与 Node.js 22 的智能开发沙箱。

### 环境说明

本模板预装以下工具和依赖：

| 类别 | 内容 |
|------|------|
| **基础镜像** | python:3.12-slim |
| **Python** | Python 3.12 + venv 虚拟环境（位于 `/opt/venv`） |
| **Node.js** | Node.js 22.x + npm |
| **Python 包** | `httpx`、`rich`、`pyyaml` |
| **系统工具** | git、curl、wget、ripgrep、jq、build-essential、openssh-client |
| **资源配置** | 2 CPU / 4096 MB 内存 |

### 安装方式

**从本地安装：**

```bash
abx template install ./qoder --registry-type local
```

**从 GitHub 安装：**

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qoder
```

### 使用示例

创建沙箱实例：

```bash
abx create --template qoder
```

在沙箱中执行开发任务：

```bash
abx exec <sandbox-id> -- python3 -c "print('Hello from Qoder sandbox')"
abx exec <sandbox-id> -- node -e "console.log('Node.js ready')"
```

使用 Python SDK：

```python
from agent_sandbox import Sandbox

sandbox = Sandbox.create_sync(
    template="qoder",
    env={"WORKSPACE": "/app"}
)

result = sandbox.commands.run("python3 --version && node --version")
print(result.stdout)
```

### 配置说明

#### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `WORKSPACE` | 沙箱内工作目录，默认 `/app` | 否 |

#### 自定义配置

如需在模板基础上安装额外依赖，可在创建沙箱后执行：

```bash
abx exec <sandbox-id> -- pip install <package-name>
abx exec <sandbox-id> -- npm install -g <package-name>
```

### 注意事项

- **工作目录**：`WORKSPACE` 默认为 `/app`。
- **双运行时**：环境同时支持 Python 3.12 和 Node.js 22，可根据项目需求选择。
- **虚拟环境**：Python 包安装在 `/opt/venv` 中，使用时无需手动激活，`PATH` 已自动配置。
- **SSH 支持**：已安装 `openssh-client`，支持 Git SSH 协议操作。

## Deploy and local e2e

Install and register this template:

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qoder
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

