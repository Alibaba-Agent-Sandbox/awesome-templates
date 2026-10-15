# amp

Sourcegraph Amp CLI in an Agent Sandbox. The image pins `@ampcode/cli` and serves named commands on port 9000.

## What it does

Installs the Amp CLI (`amp`) and registers four commands:

| Command | What it runs |
|---|---|
| `amp_version` | `amp version` |
| `amp_setup_check` | `amp version`, then writes the settings file described below |
| `amp_execute` | `amp --dangerously-allow-all --no-color --no-notifications --no-ide -x <prompt>` |
| `amp` | The previous name of `amp_execute`. Same arguments. |

`amp_execute` adds `--stream-json` when `stream_json` is true. The HTTP response is the full stdout after the process exits. It is not a live stream.

`amp_execute` checks `AMP_API_KEY` before it starts the CLI. If the variable is missing or blank, the command returns an error that names `AMP_API_KEY` and says the CLI would otherwise start a device-login flow. Probed on 2026-10-15: `amp -x` with no key prints a device-login URL and waits. This command does not do that.

Amp does not accept a DashScope key, `ABX_LLM_API_KEY`, or an OpenAI-compatible base URL. The token is an Amp access token from [ampcode.com settings](https://ampcode.com/settings/security#access-token).

`--dangerously-allow-all` is a flag the `0.0.1792022479-ge66e24` binary accepts. `amp --help` on that version does not list it in the options section. The help text documents the settings key `amp.dangerouslyAllowAll`. `amp_execute` passes the flag and `amp_setup_check` writes the settings key.

## Stack

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`.
- Node.js 20 from that image, used only to run `npm`. The `amp` binary is a glibc ELF from the optional package `@ampcode/cli-linux-x64` at the same version.
- `@ampcode/cli@0.0.1792022479-ge66e24`, from `npm view @ampcode/cli version` on 2026-10-15. The previous directory pin was `0.0.1791964847-g13f24a`. The base image sets npm's registry to `registry.npmmirror.com`, which returned 404 for `@ampcode/cli-linux-x64` at this version, so the Dockerfile installs from `https://registry.npmjs.org`. `amp version` runs in the image build and fails the build if the native binary was not unpacked.
- `agent-sandbox-server` from python-sdk commit `61c43e0be65a1f57aa09186d578e7b399e48429b` (PR #21). That distribution is not on PyPI.
- git and ripgrep.
- Work directory `/home/user/app`. Runtime user `user`. The platform starts `start_cmd`. The Dockerfile has no `CMD` or `ENTRYPOINT`.

## Problem solved

A generation-2 sandbox can run a pinned Amp CLI without a TUI, report the version and the settings file without a key, and refuse a live turn when `AMP_API_KEY` is absent instead of blocking on device login.

## Quick start (CLI)

From a checkout of this repository, with Express credentials in the environment:

```bash
abx template deploy ./amp -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> amp_version
abx run <sandbox-id> amp_setup_check
```

`template.yaml` already stores `generation`, `start_cmd`, and `ready_cmd`. A live turn needs an Amp access token. Pass it at create time. Do not bake it into the image:

```bash
abx create --template <template-id> -y --env AMP_API_KEY=<amp-access-token>
abx run <sandbox-id> amp_execute --arg prompt='Reply with exactly: ABX_E2E_OK'
```

`stream_json` is a boolean. Pass it with `--json-args`:

```bash
abx run <sandbox-id> amp_execute --json-args '{"prompt":"Reply with exactly: ABX_E2E_OK","stream_json":true}'
```

Remove the sandbox and the template when you are done:

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py amp` deploys a unique alias, runs the `smoke` commands (`amp_version` and `amp_setup_check`) through `abx run` and the Python SDK, writes evidence only after a pass, and deletes that sandbox and that template.

## Quick start (Python SDK)

Install the client from PyPI as `agent-sandbox-client` (`python3 -m pip install agent-sandbox-client`). The import is `agent_sandbox`. `pip install agent-sandbox` is an unrelated project.

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("amp_version"))
        print(await sb.run("amp_setup_check"))
        # AMP_API_KEY is an Amp access token, not a DashScope key.
        # print(await sb.run("amp_execute", prompt="Reply with exactly: ABX_E2E_OK"))
    finally:
        await sb.kill()

asyncio.run(main())
```

Create with the key when you want `amp_execute`:

```python
sb = await Sandbox.create(
    template="<template-id>",
    timeout=300,
    envs={"AMP_API_KEY": "<amp-access-token>"},
)
text = await sb.run("amp_execute", prompt="Reply with exactly: ABX_E2E_OK", stream_json=False)
```

`await sb.run(...)` returns the command's `result` value. `sb.commands.run` is a shell command, not one of these names. `Sandbox.create_sync` raises `TypeError` on python-sdk 0.3.0 ([python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)); use `await Sandbox.create`.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `amp_version` | none | string | First token of `amp version`, for example `0.0.1792022479-ge66e24`. |
| `amp_setup_check` | none | object | `installed`, `package`, `version`, `api_key_set`, `settings_path`, `dangerously_allow_all`, `updates_mode`. |
| `amp_execute` | `prompt` string, required. `stream_json` boolean, optional, default `false`. | string | Stdout of `amp -x`. `--stream-json` when `stream_json` is true. |
| `amp` | same as `amp_execute` | string | Previous command name. |

`POST /commands/amp_execute` with `{"prompt":"hi"}` returns `{"result":"<stdout>"}` when the CLI exits 0. A missing `prompt` is HTTP 400. A missing `AMP_API_KEY`, a missing binary, or a non-zero `amp` exit is HTTP 500 `{"error","type"}`. `api_key_set` is a boolean. The secret is not returned. `RuntimeError` text has the key redacted when it was set.

`amp_setup_check` writes this JSON (merging into an existing object):

```json
{
  "amp.dangerouslyAllowAll": true,
  "amp.updates.mode": "disabled",
  "amp.notifications.enabled": false
}
```

The path is `AMP_SETTINGS_FILE`, or `$WORKSPACE/.e2e_amp/settings.json` when `WORKSPACE` is set, or `/home/user/.config/amp/settings.json` when `HOME` is `/home/user`. The image sets `AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json`.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `AMP_API_KEY` | for `amp_execute` | empty | Amp access token. Not a DashScope or OpenAI key. Declared empty in `template.yaml`. |
| `AMP_URL` | no | `https://ampcode.com/` | Amp service URL. The CLI's own default. Not set by the image. |
| `AMP_SETTINGS_FILE` | no | `/home/user/.config/amp/settings.json` in the image | Settings file `amp_setup_check` writes. |
| `AMP_LOG_FILE` | no | `/home/user/.cache/amp/logs/cli.log` in the image | CLI log path. |
| `ABX_SERVER_TOKEN` | no | empty | When set inside the sandbox, clients send `Authorization: Bearer`. |
| `ABX_SERVER_PORT` | no | `9000` | Port for a local `python3 commands.py`. |

Set secrets on `abx create --env` or `Sandbox.create(envs=...)`. Do not write them into the image or the log.

Outside the image, set `AMP_SETTINGS_FILE` or `WORKSPACE` before starting `commands.py`. Otherwise a process whose `HOME` is not `/home/user` writes `.e2e_amp/settings.json` in the current directory.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

A live agent turn with tools was not measured. The keyless commands (`amp_version`, `amp_setup_check`) fit this size. The `amp` binary is about 130 MB.

## Verified

| Provider | Date (UTC) | Template version | SDK | What passed |
|---|---|---|---|---|
| alicloud-express | 2026-10-15 | 1.1.0 | 0.3.0 | L2. `python3 scripts/express_e2e.py amp` deployed generation 2, reached READY, and ran `amp_version` and `amp_setup_check` through `abx run` and `Sandbox.run`. |

L1: `docker build` of this Dockerfile printed `0.0.1792022479-ge66e24` from `amp version` and installed `agent-sandbox-server` from python-sdk commit `61c43e0be65a1f57aa09186d578e7b399e48429b`.

L0: `e2e_test.py` passed with `amp` on `PATH` (version and settings) and without it (the not-found error). `python3 scripts/run_local_e2e.py` passed this directory.

L3 was not run. This environment has no `AMP_API_KEY`. A DashScope or OpenAI-compatible key was not sent to Amp.

## Secondary development

The version pin is `@ampcode/cli@0.0.1792022479-ge66e24` in the Dockerfile (`AMP_CLI_VERSION`) and the `amp_version` smoke expect in `template.yaml`. After `npm view @ampcode/cli version`, update both, plus `PINNED_VERSION` in `e2e_test.py`, and re-run `amp version` so the smoke string is the first token of that output.

`amp_execute` builds an argv list. Do not interpolate the prompt into a shell string. Keep the `AMP_API_KEY` check in front of `subprocess` so a missing key cannot block on device login.

To add a command, register another `@command` function that calls `amp` with an argv list. `start()` stays under `if __name__ == "__main__"`.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md). Design notes are in [docs/design/amp.md](../docs/design/amp.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
