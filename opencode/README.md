# opencode

OpenCode (`sst/opencode`) in an Agent Sandbox. The image installs npm package `opencode-ai@1.19.0`. Named commands call that CLI. The primary call is headless `opencode run`. `opencode serve` is a second HTTP server on port 4096.

## What it does

`agent-sandbox-server` listens on port 9000 and registers commands that run `opencode`. `opencode_run` executes one non-interactive `opencode run --format json` and returns the assistant text, the raw JSON events, and the session id. `opencode_version` and `opencode_setup_check` check the pinned binary and `opencode.json` without calling a model.

`opencode_serve_start` starts `opencode serve` on port 4096 bound to `0.0.0.0`. That process is OpenCode's own HTTP API (`GET /global/health`). Reach it with `sb.network.get_url(4096)`. The platform `start_cmd` does not start it.

`opencode` is the previous command name. It runs the same argv as `opencode_run` and returns the raw stdout string.

## Stack

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`. Python 3.13 and Node.js 20 come from that image.
- `opencode-ai@1.19.0` (npm `latest` on 2026-10-15). The package binary is `opencode`. Upstream is [sst/opencode](https://github.com/sst/opencode).
- `agent-sandbox-server` from python-sdk commit `61c43e0be65a1f57aa09186d578e7b399e48429b` when the build context has no wheel. A wheel injected by `abx template deploy` wins. The PyPI release `agent-sandbox-server==0.3.0` predates that commit and is not installed.
- git and ripgrep.
- Work directory `/home/user/app`. Runtime user `user`. No image `CMD` or `ENTRYPOINT`.
- Generation 2. `start_cmd` is `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`. `ready_cmd` is `agent-sandbox-server healthcheck --port 9000`.

## Problem solved

Gives a caller a pinned OpenCode CLI inside a sandbox, with one JSON command for a headless turn and an optional OpenCode HTTP server on a sandbox port. Provider settings point at an OpenAI-compatible endpoint. The keys this environment uses are `ABX_LLM_API_KEY` and `ABX_LLM_BASE_URL` (DashScope compatible-mode). The image does not contain those values.

## Quick start (CLI)

From a checkout of this repository, with Express credentials in the environment:

```bash
abx template deploy ./opencode -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y \
  --env ABX_LLM_API_KEY=<key> \
  --env ABX_LLM_BASE_URL=<openai-compatible-base-url>
abx run <sandbox-id> opencode_version
abx run <sandbox-id> opencode_setup_check
abx run <sandbox-id> opencode_run --json-args '{"prompt":"Reply with exactly ABX_E2E_OK","model":"dashscope/qwen3.8-flash"}'
abx run <sandbox-id> opencode_serve_start
```

`template.yaml` already stores `generation`, `start_cmd`, and `ready_cmd`. The flags repeat them so the command stands alone.

`--json-args` is required for `continue_session` (boolean) and `port` (integer). `--arg` values are strings.

Remove the sandbox and the template when you are done:

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py opencode` deploys, runs the smoke commands (`opencode_version`, `opencode_setup_check`), writes evidence only after a pass, and deletes that sandbox and that template.

## Quick start (Python SDK)

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(
        template="<template-id>",
        timeout=300,
        envs={
            "ABX_LLM_API_KEY": "<key>",
            "ABX_LLM_BASE_URL": "<openai-compatible-base-url>",
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

`await sb.run("opencode_run", prompt="...")` returns a dict with `text`, `stdout`, `session_id`, `model`, `agent`, and `cwd`. `sb.commands.run` is a shell command, not this named command. `Sandbox.create_sync` raises `TypeError` on python-sdk 0.3.0 ([python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)); use `await Sandbox.create`.

`opencode_run` is the primary API: one request, one JSON body, the headless CLI. `opencode serve` is for clients that already speak OpenCode's HTTP API. Both are in the image. Only the command server on port 9000 starts with the sandbox.

## Command reference

| Command | Parameters | Returns | Upstream |
|---|---|---|---|
| `opencode_run` | see the table below | object | `opencode run --pure --format json --auto ...` |
| `opencode` | same as `opencode_run` | string (raw JSON events) | same argv as `opencode_run` |
| `opencode_version` | none | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | none | `"ok"` | `opencode --version` plus a read of `opencode.json` |
| `opencode_serve_start` | `port` integer, default `4096`; `hostname` string, default `0.0.0.0` | object | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | none | object | localhost `GET /global/health` |
| `opencode_serve_stop` | none | `"stopped"` | `SIGTERM` to the process this template started |

`opencode_run` parameters:

| Parameter | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `prompt` | string | yes | | Last argv element. Not interpolated into a shell string. |
| `model` | string | no | `OPENCODE_MODEL`, else `dashscope/qwen3.8-flash` | `--model`, form `provider/model`. |
| `agent` | string | no | empty (CLI primary agent, `build`) | `--agent` when non-empty. |
| `session` | string | no | empty | `--session` to continue that session id. |
| `continue_session` | boolean | no | `false` | `--continue` (last session). Pass a JSON boolean. |
| `cwd` | string | no | `/home/user/app` when that directory exists | `--dir` and the child working directory. Must be an existing directory. |

`opencode_run` returns:

| Field | Meaning |
|---|---|
| `text` | Concatenated `type: text` parts from the JSON events. |
| `stdout` | Raw stdout, one JSON event per line. |
| `session_id` | `sessionID` from those events, or empty. |
| `model` | Selector that was passed to `--model`. |
| `agent` | Agent name that was passed, or empty. |
| `cwd` | Directory that was passed to `--dir`. |

A missing `prompt` is HTTP 400. A non-zero CLI exit is HTTP 500 `{"error","type":"RuntimeError"}`. The message does not include secret values. Timeout is 600 seconds. Stdin is `/dev/null`.

`opencode_serve_start` returns `running`, `port`, `hostname`, `pid`, and `healthy`. It waits until `GET http://127.0.0.1:<port>/global/health` returns `{"healthy": true, "version": "1.19.0"}`. The public URL is `sb.network.get_url(port)`, not that localhost address. A second start on the same port returns the current status.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_LLM_API_KEY` | for a DashScope call | empty | `{env:ABX_LLM_API_KEY}` in `opencode.json`. Inject at create. |
| `ABX_LLM_BASE_URL` | for a DashScope call | empty | OpenAI-compatible base URL, including the `/v1` path. `{env:ABX_LLM_BASE_URL}`. |
| `OPENCODE_MODEL` | no | `dashscope/qwen3.8-flash` | Used when `model` is empty. |
| `OPENCODE_API_KEY` | no | empty | OpenCode Zen credential when `model` is `opencode/<id>`. |
| `OPENCODE_SERVER_PASSWORD` | no | empty | Basic auth password for `opencode serve`. The CLI warns when it is unset. |
| `ABX_SERVER_TOKEN` | no | empty | When set, port 9000 requires `Authorization: Bearer`. Pass `token=` to the SDK client. Leave unset for anonymous calls. |
| `OPENCODE_CONFIG` | no | `/home/user/app/opencode.json` | Config file the child process reads. |
| `OPENCODE_DISABLE_AUTOUPDATE` | no | `true` in the image | Stops the pinned CLI from upgrading itself. |
| `ABX_SERVER_PORT` | no | `9000` | Port `start()` binds for a local `python3 commands.py`. |

`opencode.json` defines provider `dashscope` with npm package `@ai-sdk/openai-compatible`. Model ids shipped in that file are `qwen3.8-flash` and `qwen3.8-max`. Another id under `dashscope/` is added to a temporary config for that one `opencode_run`. A model on a different provider uses the config file as written; put that provider in `opencode.json` or pass a `model` the file already allows.

Set secret values on `abx create --env` or `Sandbox.create(envs=...)`. Do not write them into the image.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| ports | 9000 (command server), 4096 (`opencode serve`, only after `opencode_serve_start`) |
| disk | platform rootfs, about 10G on Express |

## Verified

No provider has a passing run recorded for this template.

## Secondary development

The command bodies live in `commands.py`. `opencode_run` builds an argv list; keep prompts and model ids as list elements. Pin every new installer in the Dockerfile (`npm install -g name@version` or `pip install name==version`).

To change the default model, edit `OPENCODE_MODEL` in `template.yaml` and the `model` field in `opencode.json`, and add the id under `provider.dashscope.models` when the provider is `dashscope`. The id has to exist on the endpoint `ABX_LLM_BASE_URL` points at.

Copy `_skeleton` only when starting a different template. This directory is the OpenCode entry. Fill changes against [docs/template-spec.md](../docs/template-spec.md) and [docs/design/opencode.md](../docs/design/opencode.md).

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE). The OpenCode CLI is upstream software installed at build time.
