# Aider

## 做什么

真实调用官方 `aider-chat==0.86.2` CLI。默认 **ask 只读模式**；只有显式
`allow_write=true` 才允许回写指定文件。工作目录必须属于已有 git 仓库。
每轮只把白名单文件复制进临时 git 工作区，完成后检查原文件未被并行修改，
再回写选中的结果，不自动提交。它不是交互式 Aider 的全部功能替代品。

## 技术栈

Alibaba FC base `v0.0.49` 的 Python 3.13 server 与 Node 20 保持原状。
Aider 官方要求 Python `>=3.10,<3.13`，因此单独安装经过 SHA256 校验的
python-build-standalone **3.12.12 / 20260211**，并在 `/opt/aider` 的独立
venv 中安装固定 Aider。server 使用源码构建的 wheel，或 Dockerfile 中的
固定 SDK commit。无需浏览器、Node 升级或另一套 HTTP server。

## 解决的问题

在沙箱中执行有边界的代码审查和修改，不把 Aider 的整套 Python 依赖装进
调用方环境，也不默认将整个仓库、配置与凭据发送给模型。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

```bash
abx template install alibaba-agent-sandbox/awesome-templates//aider
abx template deploy ./aider -y
abx create --template <template-id>
abx exec <sandbox-id> --background --env AIDER_API_KEY=REPLACE_ME \
  --env AIDER_BASE_URL=https://example.invalid/v1 --env AIDER_MODEL=your-model \
  -- agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py
abx exec <sandbox-id> -- agent-sandbox-server healthcheck --port 9010
abx run <sandbox-id> aider_setup_check --server-port 9010
abx exec <sandbox-id> -- sh -c 'mkdir -p /home/user/app/project && cd /home/user/app/project && git init -q'
# 先用 abx upload 上传 calculator.py。
abx run <sandbox-id> aider --server-port 9010 --json-args '{"prompt":"解释此文件","cwd":"/home/user/app/project","files":"[\"calculator.py\"]"}'
abx run <sandbox-id> aider --server-port 9010 --json-args '{"prompt":"修复 calculator.py 并创建 REPORT.md","cwd":"/home/user/app/project","files":"[\"calculator.py\",\"REPORT.md\"]","allow_write":true,"command_timeout":180}'
abx exec <sandbox-id> -- sh -c 'cd /home/user/app/project && git diff -- calculator.py'
abx kill <sandbox-id>
```

等待 9010 healthcheck 成功并确认三个配置布尔值均为 true。CLI env 与 JSON prompt
会进入宿主 argv；需要避免凭据进入宿主 argv/history 时，使用下方 SDK 进程 env。
退出码零只说明 CLI 完成，不代表代码正确；自行检查 diff 并执行独立测试。

## 快速开始（Python SDK）

`agent-sandbox-client` 发行版未发布时使用[配对固定源码安装](../docs/python-client-installation.md)。
`pip install agent-sandbox` 是无关项目，不是这里的 client。

```python
import asyncio
import json
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600)
    stream = None
    server_task = None
    try:
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py",
            env={"AIDER_API_KEY": os.environ["AIDER_API_KEY"],
                 "AIDER_BASE_URL": os.environ["AIDER_BASE_URL"],
                 "AIDER_MODEL": os.environ["AIDER_MODEL"],
                 "ABX_SERVER_BASE_DIR": "/home/user/app"}, timeout=600)
        async def drain():
            async for _ in stream:
                pass
        server_task = asyncio.create_task(drain())
        for attempt in range(30):
            try:
                state = await sb.run("aider_setup_check", server_port=9010, timeout=10)
            except Exception:
                if attempt == 29:
                    raise
                await asyncio.sleep(1)
                continue
            if not all(state[name] for name in ("api_key_set", "base_url_set", "model_set")):
                raise RuntimeError("the configured server did not receive all settings")
            break
        await sb.commands.run("mkdir -p /home/user/app/project && cd /home/user/app/project && git init -q")
        await sb.files.write("/home/user/app/project/calculator.py", "def add(a,b): return a-b\n")
        result = await sb.run("aider", prompt='修复 add 并创建 REPORT.md', cwd="/home/user/app/project",
            files=json.dumps(["calculator.py", "REPORT.md"]), allow_write=True,
            server_port=9010, command_timeout=180, timeout=210)
        print(result["changed_files"])
        print(await sb.files.read("/home/user/app/project/REPORT.md"))
    finally:
        await sb.kill()
        if server_task is not None:
            server_task.cancel()
            await asyncio.gather(server_task, return_exceptions=True)
        if stream is not None:
            await stream.cancel()

asyncio.run(main())
```

## 快速开始（HTTP POST）

通过 `sb.network.get_url(9010)` 获得 server 地址。JSON 直接放参数对象，
不要再套 `args`：

```http
POST /commands/aider
Content-Type: application/json
Authorization: Bearer REPLACE_ME

{"prompt":"解释 calculator.py","cwd":"/home/user/app/project","files":"[\"calculator.py\"]","allow_write":false,"command_timeout":180}
```

结果结构为 `{"result":{"stdout":"...","stderr":"...","exit_code":0,"changed_files":[]}}`。
只有配置了 `ABX_SERVER_TOKEN` 才需要示例 bearer；provider gateway 认证是另一层。
SDK 使用 `sb.server_at(9010, token=...)`。不要把 envd token 当作 server bearer。
缺少必填参数、参数类型或请求格式错误返回 400，认证错误 401，未知命令 404，
语义校验、上游失败或超时返回 500，包含 `error` 与 `type`，不回显上游错误原文。

命名命令缓冲完整输出。`command_timeout` 约束拥有的 CLI 进程组，SDK 的
`timeout` 只是 HTTP 等待时间，应该更长。客户端断线不会自动取消命令。
长后台任务使用 process API，显式停止进程或销毁自己的沙箱。包装层超时或
Python 取消会终止自己的进程组，并删除临时消息、配置和 stage。

## 命令参考

| 命令 | 参数 | 返回与真实调用 |
| --- | --- | --- |
| `aider_version` | 无 | 字符串 `aider 0.86.2`；真实执行 `aider --version` |
| `aider_setup_check` | 无 | 安装/配置/home 阻断布尔值、固定版本和工作目录；不返回 key 或 endpoint |
| `aider` | 必填 `prompt: string`，1–100000 字符；`cwd: string=""`；`files: string="[]"`，内容是最多 32 个相对路径组成的 JSON 数组；`allow_write: boolean=false`；`command_timeout: integer=600`，范围 1–1800 | 脱敏 stdout/stderr、exit_code 与 changed_files 字典 |

每个文件最多 1 MiB。拒绝绝对路径、遍历、重复项、文件或父目录符号链接，以及
`.git`、`.env`、`.aider` 路径。尚不存在的选中路径表示新产物。未选中的 stage 输出丢弃。
显式设置 `yes-always: false` 禁用自动确认，受控 stdin 持续回答 `n` 直到进程退出，
使上游拒绝创建或编辑未加入 stage 的路径。固定版本的 config false 单独使用时
确认状态仍是未设置，而 EOF 会接受默认 Yes，因此不能用空 stdin 代替明确拒绝。
检测到并行修改会拒绝回写，但不能把它视为对恶意并行写者的隔离机制。
写入按单个文件原子替换，保留旧文件权限，不是跨全部文件的事务。
默认 ask 即使 stage 被修改也不会回写。

真实 argv 使用 `--chat-mode ask|whole`、`--message-file`、明确文件、model/base/settings，
并关闭自动提交、自动 lint/test、shell 建议、URL 检测、浏览器、analytics 与更新。
固定文字前缀使以 `/` 或 `!` 开头的 prompt 仍作为模型文本，避免上游 slash/bang
命令分派。prompt 和 API key 不出现在 argv；key 只通过子进程环境传递。

## 配置

| 名称 | 默认与含义 |
| --- | --- |
| `AIDER_API_KEY` | 空；必需兼容 API 凭据 |
| `AIDER_BASE_URL` | 空；必需 HTTP(S) endpoint，不允许内嵌凭据、query、fragment |
| `AIDER_MODEL` | 空；必需 model ID，自动加 LiteLLM `openai/` 前缀 |
| `WORKSPACE` | `/home/user/app`；默认工作目录 |
| `ABX_SERVER_TOKEN` | 空；可选 server 认证 |

**预热进程边界：** `Sandbox.create(envs=...)` 配置 envd 及后续原生进程，
不会追溯修改已启动的 9000 命名命令 server 环境。必须从镜像已安装的原 commands
启动自有 9010 server，通过 `commands.start(env=...)` 明确注入配置并消费 stream，
CLI/SDK/HTTP 均使用该端口。示例不更改 HOME、不覆盖镜像源码；销毁自有沙箱
时两个 server 一并停止。

兼容配置使用 `extra_body.enable_thinking=false`，用于已验证的 Qwen 兼容路由；
扩展其他后端时调整并重新验收。key 不写入 stage 文件；选中源码仍会发往模型服务。

**原生 home 限制：** 固定上游源码总是先搜索 home 默认文件，再追加
`--config` / `--env-file`，这两个参数不能承诺完全隔离。已有 home
`.aider.conf.yml`、`.env`、model settings/metadata、OAuth key 文件时启动前拒绝。
包装层不替换 `HOME`、不修改共享 profile、不导入项目配置；
`PYTHON_DOTENV_DISABLED=1` 禁用 dotenv 加载。上游自己的 cache/install 与
analytics-disabled 状态可能保留在该专用沙箱原生 `.aider`，随实例整体销毁。
不要在共享宿主 home 中执行真实调用。

## 资源

2 vCPU、2048 MiB、9000 端口。Python 3.11 Linux x86-64 的 metadata 解析共
108 个兼容发行包、118 MiB 压缩 wheel；这不是实际镜像安装体积。
独立 Python 3.12 的 x86-64 压缩归档约 32 MiB。镜像验收另行记录。

## 已验证

[Express 实际镜像补充验收](evidence/image-runtime-2026-10-16-configured.json)
已通过：实际 CI 构建镜像的官方 READY、源码/server 字节溯源、SDK/HTTP/CLI
版本与配置目标、真实 CLI 正负控，以及 qwen3.8-flash 真实编程 21 项检查，
包括独立测试和取回的产物。模型 server 在 9010，预热 9000 是独立进程。
自有 helper、实例、模板、registry 均已清理并回查。
保留[首轮失败记录](evidence/image-runtime-2026-10-16-attempt1.json)。

[加固验收器后的镜像复验](evidence/image-runtime-hardened-2026-10-16.json)
使用 `f76687e` 验收器与同一不可变镜像，真实模型检查 21 项通过，零失败、零跳过。
直接编译源码、完整执行原始测试及新的完成确认值，可以拒绝提前退出和旧缓存造成的误通过。
七项自有资源清理检查和单独的官方模板严格缺席回查均通过；旧记录保留，
其真实模型结果发生在这次完成性校验加固之前。

目录仍是 experimental，`tested_on: []`：canonical
`scripts/express_e2e.py` → `abx template deploy` 的 L2 wrapper 尚未通过。
其他 provider 未验。参见[设计](../docs/design/aider.md)。

## 二次开发

修改 `commands.py` 后补充带边界的新命令、API 表、中英文文档和正负控。
保留白名单、原文件校验和进程组清理。升级 Python/Aider pin 必须重新查官方
metadata、真实 help/version，并重跑镜像与模型测试。保留安装依赖和 Python 归档许可证。

## 贡献

遵循[仓库规则](../CONTRIBUTING.md)，运行
`python3 scripts/check_template.py aider`、`python3 -m pytest aider -q` 与
`python3 scripts/run_local_e2e.py`。本地无 key 检查只有 L0。
真实 coding 需专用新沙箱、`E2E_REQUIRE_LLM=1`、独立测试与文件取回，不能只看 marker。
不改旧证据，不提交 key 或原始模型日志。

## 问题反馈

[模板 Issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50)。
SDK/server 问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，
CLI/deploy 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 glue 为 Apache-2.0。[Aider](https://github.com/Aider-AI/aider) 也采用 Apache-2.0；
安装依赖与 [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
保留各自 notices。参见[官方安装](https://aider.chat/docs/install.html)与
[兼容 API 指南](https://aider.chat/docs/llms/openai-compat.html)。

实际 CLI 负控（只在全新专用沙箱运行）：

```bash
python3 aider/verify_upstream_guards.py
```

此命令使用确定性的 loopback 模型验证 slash/bang 分派与未选中路径拒绝，
不代表真实模型 coding 或实际镜像部署通过。

### 独立测试完整执行

编程控制器在隔离的 Python 进程中直接编译实际源码，核验三个原始测试逐字节不变且全部执行成功，
拒绝跳过、预期失败或未完整执行的测试。测试和隐藏用例分别要求在 Agent 退出后才生成的独立完成确认。
静态 marker、提前退出及旧字节码不能证明通过。这些检查用于确认任务完成，不构成操作系统隔离边界。
原先真实模型证据作为历史保留；加固后的验证器须单独进行真实模型测试。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
