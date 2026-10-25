# amp

Sourcegraph Amp CLI in an Agent Sandbox. The image pins `@ampcode/cli` and serves named commands on port 9000.

## What it does

Installs the Amp CLI (`amp`) and registers four commands:

| Command | What it runs |
|---|---|
| `amp_version` | `amp version` |
| `amp_setup_check` | `amp version`, then reads existing settings without changing them |
| `amp_execute` | `amp --no-color --no-notifications --no-ide -x <prompt>` |

`amp_execute` adds `--stream-json` when `stream_json` is true. The HTTP response is the full stdout after the process exits. It is not a live stream.

`amp_execute` checks `AMP_API_KEY` before it starts the CLI. If the variable is missing or blank, the command returns an error that names `AMP_API_KEY` and says the CLI would otherwise start a device-login flow. Probed on 2026-10-15: `amp -x` with no key prints a device-login URL and waits. This command does not do that.

Amp does not accept a DashScope key, `ABX_LLM_API_KEY`, or an OpenAI-compatible base URL. The token is an Amp access token from [ampcode.com settings](https://ampcode.com/settings/security#access-token).

`--dangerously-allow-all` is a flag the `0.0.1792022479-ge66e24` binary accepts. `amp --help` on that version does not list it in the options section. The help text documents the settings key `amp.dangerouslyAllowAll`. `amp_execute` adds that flag only when `dangerously_allow_all=true` is explicitly requested. Existing caller-owned settings remain unchanged; inspect their effective permission flag with `amp_setup_check`. The image default is false.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`.
- Node.js 20 from that image, used only to run `npm`. The `amp` binary is a glibc ELF from the optional package `@ampcode/cli-linux-x64` at the same version.
- `@ampcode/cli@0.0.1792022479-ge66e24`, from `npm view @ampcode/cli version` on 2026-10-15. The previous directory pin was `0.0.1791964847-g13f24a`. The base image sets npm's registry to `registry.npmmirror.com`, which returned 404 for `@ampcode/cli-linux-x64` at this version, so the Dockerfile installs from `https://registry.npmjs.org`. `amp version` runs in the image build and fails the build if the native binary was not unpacked.
- git and ripgrep.
- Work directory `/home/user/app`. Runtime user `user`. The platform starts `start_cmd`. The Dockerfile has no `CMD` or `ENTRYPOINT`.

## Problem solved

A generation-2 sandbox can run a pinned Amp CLI without a TUI, inspect the version and existing settings without a key or configuration writes, and refuse a live turn when `AMP_API_KEY` is absent instead of blocking on device login.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./amp --yes
abx run <sandbox-id> amp_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('amp_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/amp_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.0.1792022479-ge66e24"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `amp_version` | none | string | First token of `amp version`, for example `0.0.1792022479-ge66e24`. |
| `amp_setup_check` | none | object | `installed`, `package`, `version`, `api_key_set`, `settings_path`, `settings_exists`, `dangerously_allow_all`, `updates_mode`. No files are written. An absent file reports false and `default`. |
| `amp_execute` | `prompt` string, required. `stream_json` boolean, optional, default `false`; `dangerously_allow_all` boolean, optional, default `false`. | string | Stdout of `amp -x`. `--stream-json` when `stream_json` is true. |

`POST /commands/amp_execute` with `{"prompt":"hi"}` returns `{"result":"<stdout>"}` when the CLI exits 0. A missing `prompt` is HTTP 400. A missing `AMP_API_KEY`, a missing binary, or a non-zero `amp` exit is HTTP 500 `{"error","type"}`. `api_key_set` is a boolean. The secret is not returned. Success and error output redact configured secret values, including JSON-escaped values. The command kills its owned process group after 600 seconds; client timeouts alone do not cancel it.

The image ships this default JSON. Inspection and execution never create or overwrite settings:

```json
{
  "amp.dangerouslyAllowAll": false,
  "amp.updates.mode": "disabled",
  "amp.notifications.enabled": false
}
```

The path is `AMP_SETTINGS_FILE`, or `$WORKSPACE/.e2e_amp/settings.json` when `WORKSPACE` is set, or `/home/user/.config/amp/settings.json` when `HOME` is `/home/user`. The image sets `AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json`.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Required | Default | Purpose |
|---|---|---|---|
| `AMP_API_KEY` | for `amp_execute` | empty | Amp access token. Not a DashScope or OpenAI key. Declared empty in `template.yaml`. |
| `AMP_URL` | no | `https://ampcode.com/` | Amp service URL. The CLI's own default. Not set by the image. |
| `AMP_SETTINGS_FILE` | no | `/home/user/.config/amp/settings.json` in the image | Caller-owned settings file inspected without writes. |
| `AMP_LOG_FILE` | no | `/home/user/.cache/amp/logs/cli.log` in the image | CLI log path. |
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Port for a local `python3 commands.py`. |

Before `template launch`, securely export the secret variables declared empty in the manifest so the application reads them at startup. Keep values out of images, YAML and logs.

Outside the image, set `AMP_SETTINGS_FILE` or `WORKSPACE` before starting `commands.py`. Otherwise a process whose `HOME` is not `/home/user` inspects `.e2e_amp/settings.json` in the current directory. The directory is not created.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

A live agent turn with tools was not measured. The keyless commands (`amp_version`, `amp_setup_check`) fit this size. The `amp` binary is about 130 MB.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

The version pin is `@ampcode/cli@0.0.1792022479-ge66e24` in the Dockerfile (`AMP_CLI_VERSION`) and the `amp_version` smoke expect in `template.yaml`. After `npm view @ampcode/cli version`, update both, plus `PINNED_VERSION` in `e2e_test.py`, and re-run `amp version` so the smoke string is the first token of that output.

`amp_execute` builds an argv list. Do not interpolate the prompt into a shell string. Keep the `AMP_API_KEY` check in front of `subprocess` so a missing key cannot block on device login. Keep setup read-only and permission bypass explicitly opt-in. Run `python -m pytest amp/test_commands.py` from the repository root; `python scripts/run_local_e2e.py` checks local HTTP behavior without claiming model acceptance. With a compatible key on the target, `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python amp/e2e_test.py` runs the coding acceptance: seeded failing source, actual edits, downloaded artifacts, preserved tests, isolated target unittest and held-out assertions. Set `E2E_BASE_URL` and `E2E_WORKSPACE` to the target server/workspace. This opt-in acceptance explicitly grants tool approval to edit its unique disposable project; a response marker alone never passes.

To add a command, register another `@command` function that calls `amp` with an argv list. `start()` stays under `if __name__ == "__main__"`.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py amp` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

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

### 2026-10-20 full step checkpoint: template1.2.0

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T154625Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 7 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
