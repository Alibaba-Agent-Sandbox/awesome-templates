# codex

在 Agent Sandbox 里以非交互方式运行 [OpenAI Codex CLI](https://github.com/openai/codex)。镜像钉死 `@openai/codex@0.162.1`。

## 做什么

`agent-sandbox-server`（端口 9000）上的命名命令调用 `codex exec`。`codex_exec` 返回 JSONL 事件（`thread.started`、`turn.*`、`item.*`）、最后一条助手消息，以及用于续跑的 `thread_id`。`codex_version` 打印 CLI 版本。`codex_setup_check` 探测 Codex 自己的 Linux 沙箱；bubblewrap、seccomp 或遗留 landlock 路径起不来时，报告 `--dangerously-bypass-approvals-and-sandbox`。`codex_config_write` 为 OpenAI 兼容的 `base_url` 写入 `$CODEX_HOME/config.toml`（只接受 `wire_api = "responses"`）。`codex_agents_write` 写入 `AGENTS.md`，Codex 会从工作目录读取它。

`codex` 是 `codex_exec` 的兼容别名（只有 `prompt` 和 `model`）。Codex 0.162.1 不接受旧的 `codex -p ... --output-format json`，也会拒绝 `--full-auto`。

独立的 `apply_patch` 二进制是另一个模板（issue #60）。Agents API 的 HTTP 服务是 `codex-agent-api`（issue #23）。见 [docs/design/codex.md](../docs/design/codex.md)。

## 技术栈

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template deploy` 把 `<region>` 换成 `cn-hangzhou`（或 `ALIBABA_CLOUD_REGION_ID`），把 `<tag>` 换成 `v0.0.49`（或 `ABX_BASE_IMAGE_TAG`）。
- 镜像自带 Node.js 20 和 Python 3.13。
- `@openai/codex@0.162.1`（`codex-cli 0.162.1`）。
- 构建上下文里没有 wheel 时，从 python-sdk 提交 `61c43e0be65a1f57aa09186d578e7b399e48429b` 安装 `agent-sandbox-server==0.3.0`。
- `git`、`ripgrep`、`jq`。不安装发行版 `bubblewrap`，让 Codex 使用 npm 包里自带的 `bwrap`。
- 工作目录 `/home/user/app`。工作区 `/home/user/workspace`。运行用户 `user`。镜像没有 `CMD` 或 `ENTRYPOINT`。

## 解决的问题

在沙箱里提供钉死版本的非交互 Codex CLI：JSON 事件、显式工作目录、会话续跑、面向 DashScope 风格 OpenAI 兼容端点的 provider 配置，以及不假设 landlock 或 user namespace 一定存在的沙箱探测。调用方用 `abx run` 或 `Sandbox.run`，而不是把 CLI 参数拼进 shell 字符串。

## 快速开始（CLI）

在本仓库检出目录，环境里已有 Express 凭证：

```bash
abx template deploy ./codex -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y \
  --env OPENAI_API_KEY=<key> \
  --env OPENAI_BASE_URL=<https://host/compatible-mode/v1> \
  --env CODEX_MODEL=qwen-plus
abx run <sandbox-id> codex_version
abx run <sandbox-id> codex_setup_check
abx run <sandbox-id> codex_exec --json-args '{"prompt":"总结工作区。","model":"qwen-plus"}'
```

`template.yaml` 里已经写了 `generation`、`start_cmd` 和 `ready_cmd`。

用完后删除沙箱和模板：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py codex` 会用唯一别名部署，跑 smoke 命令，只有通过后才写 evidence，并删除它创建的沙箱和模板。

## 快速开始（Python SDK）

客户端的 PyPI 名称是 `agent-sandbox-client`（`python3 -m pip install agent-sandbox-client`）。导入名仍是 `agent_sandbox`。`pip install agent-sandbox` 是另一个无关项目。

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(
        template="<template-id>",
        timeout=300,
        envs={
            "OPENAI_API_KEY": "<key>",
            "OPENAI_BASE_URL": "https://host/compatible-mode/v1",
            "CODEX_MODEL": "qwen-plus",
        },
    )
    try:
        print(await sb.run("codex_version"))
        print(await sb.run(
            "codex_exec",
            prompt="Reply with exactly: ABX_E2E_OK",
            model="qwen-plus",
            sandbox="auto",
        ))
    finally:
        await sb.kill()

asyncio.run(main())
```

`await sb.run("codex_exec", prompt="...")` 返回结果对象（`last_message`、`events`、`thread_id`）。`sb.commands.run` 是 shell API；沙箱生命周期管理使用上面的异步 `Sandbox.create` 示例。

用第一次结果里的 `thread_id` 续跑：

```python
await sb.run("codex_exec", prompt="继续。", resume="<thread_id>")
```

## 快速开始（HTTP POST）

对于 `http://127.0.0.1:9000` 可访问的服务（例如本地模板进程）：

```bash
curl --fail-with-body -X POST http://127.0.0.1:9000/commands/codex_exec \
  -H 'Content-Type: application/json' \
  --data '{"prompt":"总结工作区。","sandbox":"read-only","approval":"never","json_events":true,"timeout_s":120}'
```

远程沙箱使用 `sb.network.get_url(9000)` 返回的网关地址及其要求的认证。应用配置了 `ABX_SERVER_TOKEN` 时，使用应用的秘密管理机制在授权头传递 bearer token。响应将命令结果包在 `{"result": ...}` 中；工具事件和 stderr 会对已知秘密环境变量值脱敏。

执行成功返回 HTTP 200，正文为 `{"result":{"last_message":"...","events":[],"thread_id":"..."}}`。缺少必填参数或类型不符返回 HTTP 400；应用认证失败返回 HTTP 401。沙箱策略非法或上游执行失败返回 HTTP 500，正文为 `{"error":"...","type":"RuntimeError"}`（非法值使用 `ValueError`）。

`timeout_s` 默认为 300，接受 1 到 3600 的整数。HTTP 读取超时应大于此值并预留服务和网关开销。客户端或网关可能先超时，这不代表子进程已停止；服务端 Codex 超时返回 HTTP 500。命名命令只返回一份完整 JSON；需要实时输出时使用进程 API。

## 命令参考

| 命令 | 参数 | 返回 |
|---|---|---|
| `codex_version` | 无 | 字符串 `X.Y.Z` |
| `codex_setup_check` | 无 | 对象，探测结果和绕过标志 |
| `codex_exec` | 见下表 | 对象，事件和最后一条消息 |
| `codex_config_write` | `base_url`、`provider`、`env_key`、`model`、`wire_api`、`codex_home` | 对象，路径和 toml |
| `codex_agents_write` | `content`（必填）、`cwd` | 对象，`path` 和 `bytes` |
| `codex` | `prompt`（必填）、`model` | 与 `codex_exec` 相同的对象 |

`codex_exec` 参数：

| 名称 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `prompt` | string | 是 | | 指令。放在 `--` 之后，不经过 shell。 |
| `model` | string | 否 | 空 | `--model`。空则用配置或 CLI 默认模型。 |
| `cwd` | string | 否 | `WORKSPACE` | `-C` 工作根目录。 |
| `sandbox` | string | 否 | `auto` | `auto`、`bypass`、`read-only`、`workspace-write`、`danger-full-access`。 |
| `approval` | string | 否 | `never` | `untrusted`、`on-request`、`never`。使用绕过标志时忽略。 |
| `json_events` | boolean | 否 | true | `--json`，stdout 为 JSONL。 |
| `resume` | string | 否 | 空 | 会话 id，或 `last`。 |
| `resume_all` | boolean | 否 | false | 与 `resume=last` 一起使用 `--all`。 |
| `skip_git_repo_check` | boolean | 否 | true | `--skip-git-repo-check`。 |
| `ephemeral` | boolean | 否 | false | 不把会话落盘。 |
| `output_schema` | string | 否 | 空 | JSON Schema 文件路径。 |
| `agents_md` | string | 否 | 空 | 执行前写入 `cwd/AGENTS.md`。 |
| `timeout_s` | integer | 否 | 300 | 进程超时，1–3600 秒。 |

`POST /commands/codex_exec`，正文 `{"prompt":"hi"}`，返回 `{"result": { ... }}`。缺少 `prompt` 为 HTTP 400。非法的 `sandbox` 或 `codex` 非零退出为 HTTP 500 `{"error","type"}`。

`codex_config_write` 拒绝 `responses` 以外的 `wire_api`，也拒绝 provider id `openai`、`ollama`、`lmstudio`。文件里 `supports_websockets = false`，兼容端点走 HTTPS。

`sandbox=auto` 在探测成功时使用 `workspace-write`，失败时回退到 `--dangerously-bypass-approvals-and-sandbox`。`sandbox=bypass` 显式选择该标志。它跳过 Codex 的 bubblewrap/seccomp 沙箱和审批提示，隔离边界此时由 Express 容器提供。显式指定 `read-only`、`workspace-write` 或 `danger-full-access` 而 Linux 沙箱探测失败时，命令会拒绝执行；拒绝发生在写入工作区、git、provider 配置和 `AGENTS.md` 之前，绝不会静默改成 bypass。探测本身可能创建独立的 `sandbox-probe` 状态目录。

`codex_config_write` 的参数为 `base_url`（默认依次取 `ABX_LLM_BASE_URL`、`OPENAI_BASE_URL`）、`provider`（默认 `compatible`）、`env_key`（变量名）、`model`、`wire_api`（只支持 `responses`）及 `codex_home`（默认 `CODEX_HOME` 或 `~/.codex`）。它会以 `0600` 模式覆盖 `config.toml`。`codex_agents_write` 接受必填 `content` 及可选 `cwd`，会覆盖 `cwd/AGENTS.md`。

## 配置

| 名称 | 必填 | 默认 | 作用 |
|---|---|---|---|
| `OPENAI_API_KEY` | 否 | 空 | 内置 OpenAI provider 的密钥，或兼容 provider 的 `env_key`。 |
| `CODEX_API_KEY` | 否 | 空 | Codex 自己的 API key 变量。仅在没有自定义 `base_url` 时，从 `OPENAI_API_KEY` 复制。 |
| `ABX_LLM_API_KEY` | 否 | 空 | 为 `ABX_LLM_BASE_URL` 写配置时优先使用的密钥变量名。 |
| `OPENAI_BASE_URL` | 否 | 空 | OpenAI 兼容基址，例如 DashScope 的 `/compatible-mode/v1`。 |
| `ABX_LLM_BASE_URL` | 否 | 空 | 与 `OPENAI_BASE_URL` 相同。两者都设置时用这个。 |
| `CODEX_MODEL` | 否 | 空 | 写入 `config.toml` 的 `model`；`codex_exec` 未传 `model` 时使用。 |
| `CODEX_HOME` | 否 | `/home/user/.codex` | `config.toml` 和会话目录。 |
| `WORKSPACE` | 否 | `/home/user/workspace` | 默认 `cwd`。镜像里有一份起始 `AGENTS.md`。 |
| `ABX_SERVER_TOKEN` | 否 | 空 | 设置后客户端发送 `Authorization: Bearer`。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 的端口。 |

密钥用 `abx create --env` 或 `Sandbox.create(envs=...)` 注入。不要写进镜像。

设置了 base URL 且 `config.toml` 不存在时，`codex_exec` 会创建它。`codex_config_write` 会覆盖该文件。Codex 0.162.1 不会发送 Chat Completions；`wire_api = "chat"` 是硬错误。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | 平台 rootfs，Express 上大约 10G |

较长的 agent 运行可能需要比这项声明更多的内存。平台可能忽略 memory 字段并使用自己的规格。

## 源码运行验证

2026-10-16，修改后的命令源码和固定 Codex 0.162.1 在 `alicloud-express`
完成真实模型编程任务：远端读取代码/产物、独立 Fibonacci 断言及单独重跑 unittest。
HTTP 检查全部 16 项通过，本次沙箱已删除。源码和运行包的哈希见
[证据](evidence/runtime-express-2026-10-16.json)，另有[检查日志](evidence/runtime-express-2026-10-16.log)。
本次使用现有平台基础沙箱并在运行时安装依赖；Dockerfile 镜像构建和新模板部署尚未验收。

## 已验证

尚未记录任何通过的提供方测试。

## 二次开发

升级 CLI 时三处一起改：Dockerfile 里的 `npm install -g @openai/codex@X.Y.Z`、`commands.py` 里的 `PINNED_VERSION`、`template.yaml` 里 `codex_version` 的 smoke 期望值。改完先看 `codex exec --help`。0.162.1 已经没有 `--full-auto` 和 `--output-format`。

在 `commands.py` 里用 `@command` 增加命名命令。上游 argv 用列表传递。`start()` 只放在 `if __name__ == "__main__"` 下面。

要把 Codex 指到别的 OpenAI 兼容 Responses 端点，调用 `codex_config_write`，或在第一次 `codex_exec` 之前设置 `OPENAI_BASE_URL` / `ABX_LLM_BASE_URL`。项目规则用 `codex_agents_write` 写入 `AGENTS.md`，或直接放在工作区。

嵌套沙箱探测在 `commands.py` 的 `sandbox_status()`。不要 apt 安装 `bubblewrap`，除非确认 Codex 会使用那个 `bwrap`：CLI 会优先用 `PATH` 上的 `bwrap`，而不是自带的 helper。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.md](../docs/template-spec.md)。设计说明：[docs/design/codex.md](../docs/design/codex.md)。

在仓库根目录执行 `python3 -m unittest discover -s codex -p test_commands.py -v`、`python3 scripts/check_template.py codex` 和 `python3 scripts/run_local_e2e.py`。单元测试覆盖显式权限、自动回退、结果脱敏和误判成功的 marker。L0 检查 HTTP 命令契约并可能跳过模型任务，不代表 L1 镜像构建、L2 云端执行或 L3 Agent 验收已通过。

对于本地或远程模板服务，双方进程已配置获授权的模型环境后，执行 `E2E_BASE_URL=http://127.0.0.1:9000 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_MODEL=<model> python3 codex/e2e_test.py` 做 L3。Agent 必须创建 Fibonacci 实现及 unittest 文件，成功执行工具命令并写出 `acceptance.txt`。测试要求最后的助手消息为 marker，核验产物，独立断言 Fibonacci 结果和负数拒绝行为，并重跑生成的测试。只聊天或在工具事件里回显 marker 均不通过。产物通过远程文件 API 读取，独立断言和测试通过远程 shell API 执行。`E2E_WORKSPACE` 应设为服务端文件根目录内可写的目录（默认 `/home/user/workspace`），服务要求认证时还应设置 `E2E_TOKEN`。每次使用唯一目录，清理时只删除该目录。只记录真实通过的 provider evidence，单独报告模型跳过。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。
