# Pi

## What it does

Run the official [Pi coding CLI](https://github.com/earendil-works/pi) in Alibaba's sandbox base image. This template exposes one ephemeral print-mode task against an OpenAI-compatible model endpoint. It is an independent template, with no E2B template registration dependency.

## Stack

`@earendil-works/pi-coding-agent@1.3.0` (MIT), SHA256-verified Node.js 24.16.0, platform Python 3.13 and Agent Sandbox server. The committed package-lock freezes all 118 npm dependencies; `npm ci --ignore-scripts --omit=dev` installs them. Official fd 10.5.0 and ripgrep 15.2.0 musl archives are SHA256-verified. [Dockerfile](Dockerfile) · [template.yaml](template.yaml).

## Problem solved

Use Pi through typed sandbox commands with a deadline, isolated model configuration and explicit permission to modify sandbox files.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

```bash
abx template install alibaba-agent-sandbox/awesome-templates//pi
abx create --template <template-id> --env PI_BASE_URL="$PI_BASE_URL" --env PI_MODEL="$PI_MODEL" --env PI_API_KEY="$PI_API_KEY"
abx run <sandbox-id> pi --arg prompt="Review this project"
abx run <sandbox-id> pi --arg prompt="Fix the failing calculation" --arg allow_tools=true
```

## Quick start (Python SDK)

Install `agent-sandbox-client`; see [source installation](../docs/python-client-installation.md).

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
        envs={key: os.environ[key] for key in ("PI_BASE_URL", "PI_MODEL", "PI_API_KEY")})
    try:
        print(await sb.run("pi", prompt="Fix the failing calculation",
                           allow_tools=True, command_timeout=600, timeout=660))
    finally:
        await sb.kill()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/pi" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Review this project","allow_tools":false,"command_timeout":600}'
```

Arguments are the JSON body, with no `args` wrapper. Success is `{"result":"buffered output"}`. The provider gateway token and optional server bearer token are separate; omit unset headers. HTTP 400 means invalid arguments, 401 authentication, 404 unknown command, and 500 missing configuration, execution failure or timeout. SDK HTTP `timeout` does not cancel the model process; `command_timeout` bounds its lifetime.

## Command reference

| Command | Parameters | Result |
|---|---|---|
| pi_version | none | Installed version string. |
| pi_tools_check | none | Actually execute official read/find/grep/ls offline on disposable files; returns `read/find/grep/ls OK`. |
| pi_setup_check | none | Installed/version/pin, boolean key/endpoint/model presence, workspace. No credentials or endpoint value. |
| pi | prompt: string required; cwd: string = ""; allow_tools: boolean = false; command_timeout: integer = 600 | Buffered, credential-redacted text. Deadline 1–1800 seconds. |

`cwd` must already exist; relative paths resolve under `WORKSPACE`. It is not a filesystem containment boundary. Prompt text is sent through stdin, with no shell interpolation or secret CLI flag.

## Configuration

Set `PI_BASE_URL` to a compatible chat-completions endpoint, `PI_MODEL` to its model ID, and `PI_API_KEY` to its key. All three are required. URLs with embedded credentials, query strings or fragments are refused. No interactive login occurs. Key names in metadata have empty values.

Each task creates a private temporary `models.json` using upstream's `$PI_API_KEY` interpolation, and removes that directory after success, failure or cancellation. User configuration and sessions are not reused. `--offline` disables automatic catalog/startup network traffic; the requested model call still uses the endpoint. Extensions, MCP, skills, context files, themes and prompt templates are disabled.

The image explicitly provides pinned `fd` and `rg`; offline mode therefore needs no runtime tool download. `pi_tools_check` runs all four default tool implementations without a model, and is part of the image/provider smoke.

The default tools are exactly `read,grep,find,ls`. `allow_tools=true` explicitly adds `edit,write,bash`, granting the model permission to change and execute code throughout this sandbox user's accessible files. Pi's `--no-approve` ignores trust-gated project configuration; it does not restrict tools. The tool allowlist controls this wrapper's default behavior; the sandbox remains the isolation boundary. Do not expose writable model execution to untrusted callers.

On Linux, the wrapper owns a new process group, drains both output streams and stops that group before reaping its leader on success, error, deadline or Python cancellation. Children that deliberately create a new session escape this process-group boundary. Disconnecting an HTTP client is not a cancellation API.

## Resources

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`. No Docker, KVM or additional privileges. RPC sessions, interactive TUI and extension/package installation are outside this command surface.

## Verified

Version1.0.1 explicitly repairs non-root workspace-directory ownership. Current-version provider acceptance must be rerun. Earlier receipts establish only their original versions/hashes/scopes and are preserved below.

## Historical verification

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

No provider has a passing image deployment recorded for this template. Earlier source-runtime checks at b2857609735c1da8529ba8ecf3d065076cdfb542 with official Pi 1.3.0 and `qwen3.8-flash` passed independent source/test/artifact acceptance. The later offline-tool/lock fixes need their own image/cloud verification; the earlier run does not establish cloud L2 or image L3. See [verification](../.agents/evidence/verify/2026-10-16-pi-runtime.md).

## Secondary development

```bash
python3 scripts/check_template.py pi
python3 -m pytest -q pi/test_commands.py pi/test_e2e_protocol.py pi/test_cli_protocol.py pi/test_install_tools.py
python3 scripts/run_local_e2e.py
```

Local checks default to no model. Set `E2E_REQUIRE_CLI=1` to require the pin; `E2E_REQUIRE_LLM=1` forces real coding acceptance using the target's configuration. The verifier seeds failing source/tests, invokes Pi with writable tools, downloads changed source and new artifacts, checks original tests are intact, then independently reruns isolated unittest and held-out inputs. A response marker alone fails. `E2E_COMMAND_TIMEOUT` controls the model deadline; `E2E_SERVER_TOKEN` is the optional server bearer credential and `E2E_TOKEN` is the gateway token.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py pi` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[Contribution rules](../CONTRIBUTING.md) · [specification](../docs/template-spec.md) · [design](../docs/design/pi.md).

## Issues

[Template Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41). File server/client defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized versions and reproduction steps.

## License

Apache-2.0 template code; upstream Pi is MIT. Official fd archives retain LICENSE-MIT and LICENSE-APACHE; ripgrep archives retain LICENSE-MIT, UNLICENSE and COPYING (MIT/Unlicense). Complete extracted release directories remain under `/opt/pi-tools/`; npm dependencies retain their license files. [LICENSE](../LICENSE).
