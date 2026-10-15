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

`await sb.run("codex_exec", prompt="...")` 返回结果对象（`last_message`、`events`、`thread_id`）。`sb.commands.run` 是 shell，不是这条命名命令。python-sdk 0.3.0 上 `Sandbox.create_sync` 会抛 `TypeError`（[python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)）；请用 `await Sandbox.create`。

用第一次结果里的 `thread_id` 续跑：

```python
await sb.run("codex_exec", prompt="继续。", resume="<thread_id>")
```

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

`codex_setup_check` 的 `use_bypass` 为 true 时，`codex_exec` 加上 `--dangerously-bypass-approvals-and-sandbox`。该标志跳过 Codex 的 bubblewrap/seccomp 沙箱和审批提示。隔离边界是 Express 容器。探测成功时，`sandbox=auto` 使用 `--sandbox workspace-write` 和 `approval_policy="never"`。

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

## 已验证

尚未记录任何通过的提供方测试。

## 二次开发

升级 CLI 时三处一起改：Dockerfile 里的 `npm install -g @openai/codex@X.Y.Z`、`commands.py` 里的 `PINNED_VERSION`、`template.yaml` 里 `codex_version` 的 smoke 期望值。改完先看 `codex exec --help`。0.162.1 已经没有 `--full-auto` 和 `--output-format`。

在 `commands.py` 里用 `@command` 增加命名命令。上游 argv 用列表传递。`start()` 只放在 `if __name__ == "__main__"` 下面。

要把 Codex 指到别的 OpenAI 兼容 Responses 端点，调用 `codex_config_write`，或在第一次 `codex_exec` 之前设置 `OPENAI_BASE_URL` / `ABX_LLM_BASE_URL`。项目规则用 `codex_agents_write` 写入 `AGENTS.md`，或直接放在工作区。

嵌套沙箱探测在 `commands.py` 的 `sandbox_status()`。不要 apt 安装 `bubblewrap`，除非确认 Codex 会使用那个 `bwrap`：CLI 会优先用 `PATH` 上的 `bwrap`，而不是自带的 helper。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.md](../docs/template-spec.md)。设计说明：[docs/design/codex.md](../docs/design/codex.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。
