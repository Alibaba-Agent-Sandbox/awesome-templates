# opencode

Agent Sandbox 里的 OpenCode（`sst/opencode`）。镜像安装 npm 包 `opencode-ai@1.19.0`。命名命令调用这个 CLI。主调用是无头的 `opencode run`。`opencode serve` 是端口 4096 上的另一套 HTTP 服务。

## 做什么

`agent-sandbox-server` 监听端口 9000，并注册调用 `opencode` 的命令。`opencode_run` 执行一次非交互的 `opencode run --format json`，返回助手文本、原始 JSON 事件和会话 id。`opencode_version` 和 `opencode_setup_check` 检查钉死的二进制和 `opencode.json`，不调用模型。

`opencode_serve_start` 在端口 4096 上启动 `opencode serve`，绑定 `0.0.0.0`。该进程是 OpenCode 自己的 HTTP API（`GET /global/health`）。用 `sb.network.get_url(4096)` 访问。平台的 `start_cmd` 不会启动它。

`opencode` 是以前的命令名。它和 `opencode_run` 使用同一组 argv，返回原始 stdout 字符串。

## 技术栈

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template deploy` 把 `<region>` 换成 `ALIBABA_CLOUD_REGION_ID` 或 `cn-hangzhou`，把 `<tag>` 换成 `ABX_BASE_IMAGE_TAG` 或 `v0.0.49`。Python 3.13 和 Node.js 20 来自该镜像。
- `opencode-ai@1.19.0`（2026-10-15 的 npm `latest`）。包提供的命令名是 `opencode`。上游是 [sst/opencode](https://github.com/sst/opencode)。
- 构建上下文里没有 wheel 时，从 python-sdk 提交 `61c43e0be65a1f57aa09186d578e7b399e48429b` 安装 `agent-sandbox-server`。`abx template deploy` 注入的 wheel 优先。PyPI 上的 `agent-sandbox-server==0.3.0` 早于该提交，镜像不安装它。
- git 和 ripgrep。
- 工作目录 `/home/user/app`。运行用户 `user`。镜像没有 `CMD` 或 `ENTRYPOINT`。
- Generation 2。`start_cmd` 是 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`。`ready_cmd` 是 `agent-sandbox-server healthcheck --port 9000`。

## 解决的问题

在沙箱里提供钉死版本的 OpenCode CLI：一条 JSON 命令完成一次无头对话，并可选地在沙箱端口上打开 OpenCode 自己的 HTTP 服务。供应商配置指向 OpenAI 兼容端点。本环境使用的密钥是 `ABX_LLM_API_KEY` 和 `ABX_LLM_BASE_URL`（DashScope 兼容模式）。镜像里不写入这些值。

## 快速开始（CLI）

在本仓库检出目录，环境里放好极速版凭证：

```bash
abx template deploy ./opencode -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y \
  --env ABX_LLM_API_KEY=<密钥> \
  --env ABX_LLM_BASE_URL=<OpenAI兼容的base-url>
abx run <sandbox-id> opencode_version
abx run <sandbox-id> opencode_setup_check
abx run <sandbox-id> opencode_run --json-args '{"prompt":"Reply with exactly ABX_E2E_OK","model":"dashscope/qwen3.8-flash"}'
abx run <sandbox-id> opencode_serve_start
```

`template.yaml` 已经写了 `generation`、`start_cmd` 和 `ready_cmd`。上面的参数把它们重复一遍，这样命令可以单独阅读。

`continue_session`（布尔）和 `port`（整数）要用 `--json-args`。`--arg` 的值都是字符串。

用完后删除沙箱和模板：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py opencode` 会部署、运行冒烟命令（`opencode_version`、`opencode_setup_check`），只有通过之后才写 evidence，然后删除这次创建的沙箱和模板。

## 快速开始（Python SDK）

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(
        template="<template-id>",
        timeout=300,
        envs={
            "ABX_LLM_API_KEY": "<密钥>",
            "ABX_LLM_BASE_URL": "<OpenAI兼容的base-url>",
        },
    )
    try:
        print(await sb.run("opencode_version"))
        result = await sb.run(
            "opencode_run",
            prompt="Reply with exactly ABX_E2E_OK",
            model="dashscope/qwen3.8-flash",
        )
        print(result["text"], result["session_id"])
        await sb.run(
            "opencode_run",
            prompt="Say ABX_E2E_OK again",
            session=result["session_id"],
        )
        await sb.run("opencode_serve_start")
        print(sb.network.get_url(4096))
    finally:
        await sb.kill()

asyncio.run(main())
```

`await sb.run("opencode_run", prompt="...")` 返回的字典包含 `text`、`stdout`、`session_id`、`model`、`agent` 和 `cwd`。`sb.commands.run` 是 shell，不是这个命名命令。python-sdk 0.3.0 上 `Sandbox.create_sync` 会抛出 `TypeError`（[python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)）；使用 `await Sandbox.create`。

`opencode_run` 是主 API：一次请求、一份 JSON、无头 CLI。`opencode serve` 给已经使用 OpenCode HTTP API 的客户端。两者都在镜像里。沙箱启动时只有端口 9000 上的命令服务。

## 命令参考

| 命令 | 参数 | 返回 | 上游 |
|---|---|---|---|
| `opencode_run` | 见下表 | 对象 | `opencode run --pure --format json --auto ...` |
| `opencode` | 与 `opencode_run` 相同 | 字符串（原始 JSON 事件） | 与 `opencode_run` 相同的 argv |
| `opencode_version` | 无 | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | 无 | `"ok"` | `opencode --version`，并读取 `opencode.json` |
| `opencode_serve_start` | `port` 整数，默认 `4096`；`hostname` 字符串，默认 `0.0.0.0` | 对象 | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | 无 | 对象 | 本机 `GET /global/health` |
| `opencode_serve_stop` | 无 | `"stopped"` | 向本模板启动的进程发 `SIGTERM` |

`opencode_run` 的参数：

| 参数 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `prompt` | 字符串 | 是 | | 最后一个 argv 元素。不拼进 shell 字符串。 |
| `model` | 字符串 | 否 | `OPENCODE_MODEL`，否则 `dashscope/qwen3.8-flash` | `--model`，格式 `provider/model`。 |
| `agent` | 字符串 | 否 | 空（CLI 主代理 `build`） | 非空时传 `--agent`。 |
| `session` | 字符串 | 否 | 空 | `--session`，继续该会话 id。 |
| `continue_session` | 布尔 | 否 | `false` | `--continue`（上一个会话）。传 JSON 布尔值。 |
| `cwd` | 字符串 | 否 | 存在 `/home/user/app` 时用它 | `--dir` 以及子进程工作目录。必须是已存在的目录。 |

`opencode_run` 的返回：

| 字段 | 含义 |
|---|---|
| `text` | JSON 事件里 `type: text` 片段拼起来的文本。 |
| `stdout` | 原始 stdout，一行一个 JSON 事件。 |
| `session_id` | 这些事件里的 `sessionID`，没有则为空。 |
| `model` | 传给 `--model` 的选择器。 |
| `agent` | 传给 `--agent` 的名字，没有则为空。 |
| `cwd` | 传给 `--dir` 的目录。 |

缺少 `prompt` 时 HTTP 400。CLI 非零退出时 HTTP 500，正文是 `{"error","type":"RuntimeError"}`。消息里不含密钥。超时 600 秒。标准输入是 `/dev/null`。

`opencode_serve_start` 返回 `running`、`port`、`hostname`、`pid` 和 `healthy`。它会等到 `GET http://127.0.0.1:<port>/global/health` 返回 `{"healthy": true, "version": "1.19.0"}`。对外地址是 `sb.network.get_url(port)`，不是这个 localhost 地址。同一端口上再次启动会返回当前状态。

## 配置

| 名称 | 必填 | 默认 | 作用 |
|---|---|---|---|
| `ABX_LLM_API_KEY` | 调用 DashScope 时需要 | 空 | `opencode.json` 里的 `{env:ABX_LLM_API_KEY}`。创建沙箱时注入。 |
| `ABX_LLM_BASE_URL` | 调用 DashScope 时需要 | 空 | OpenAI 兼容的 base URL，包含 `/v1` 路径。`{env:ABX_LLM_BASE_URL}`。 |
| `OPENCODE_MODEL` | 否 | `dashscope/qwen3.8-flash` | `model` 为空时使用。 |
| `OPENCODE_API_KEY` | 否 | 空 | `model` 为 `opencode/<id>` 时的 OpenCode Zen 凭证。 |
| `OPENCODE_SERVER_PASSWORD` | 否 | 空 | `opencode serve` 的基本认证密码。未设置时 CLI 会警告。 |
| `ABX_SERVER_TOKEN` | 否 | 空 | 设置后，端口 9000 需要 `Authorization: Bearer`。把 `token=` 传给 SDK 客户端。不设置则允许匿名调用。 |
| `OPENCODE_CONFIG` | 否 | `/home/user/app/opencode.json` | 子进程读取的配置文件。 |
| `OPENCODE_DISABLE_AUTOUPDATE` | 否 | 镜像里为 `true` | 阻止已钉死的 CLI 自行升级。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 时 `start()` 绑定的端口。 |

`opencode.json` 定义供应商 `dashscope`，npm 包是 `@ai-sdk/openai-compatible`。文件里带的模型 id 是 `qwen3.8-flash` 和 `qwen3.8-max`。`dashscope/` 下的其他 id 会在那一次 `opencode_run` 里写进临时配置。其他供应商的模型沿用现有配置文件；把该供应商写进 `opencode.json`，或传入文件已经允许的 `model`。

密钥放在 `abx create --env` 或 `Sandbox.create(envs=...)`。不要写进镜像。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| 端口 | 9000（命令服务），4096（`opencode serve`，仅在 `opencode_serve_start` 之后） |
| 磁盘 | 平台 rootfs，极速版大约 10G |

## 已验证

尚未记录任何通过的提供方测试。

## 二次开发

命令实现在 `commands.py`。`opencode_run` 组装 argv 列表；提示词和模型 id 保持为列表元素。新的安装步骤在 Dockerfile 里钉死版本（`npm install -g name@version` 或 `pip install name==version`）。

要改默认模型，编辑 `template.yaml` 里的 `OPENCODE_MODEL` 和 `opencode.json` 的 `model`。供应商是 `dashscope` 时，把 id 加到 `provider.dashscope.models`。该 id 必须存在于 `ABX_LLM_BASE_URL` 指向的端点。

只有在做另一个模板时才复制 `_skeleton`。本目录就是 OpenCode 条目。改动对照 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md) 和 [docs/design/opencode.md](../docs/design/opencode.md)。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。OpenCode CLI 是构建时安装的上游软件。
