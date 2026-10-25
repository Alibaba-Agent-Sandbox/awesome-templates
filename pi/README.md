# Pi

## What it does

Run the official [Pi coding CLI](https://github.com/earendil-works/pi) in Alibaba's sandbox base image. This template exposes one ephemeral print-mode task against an OpenAI-compatible model endpoint. It is an independent template, with no E2B template registration dependency.

## Stack

`@earendil-works/pi-coding-agent@1.3.0` (MIT), SHA256-verified Node.js 24.16.0, platform Python 3.13 and Agent Sandbox server. The committed package-lock freezes all 118 npm dependencies; `npm ci --ignore-scripts --omit=dev` installs them. Official fd 10.5.0 and ripgrep 15.2.0 musl archives are SHA256-verified. [Dockerfile](Dockerfile) · [template.yaml](template.yaml).

## Problem solved

Use Pi through typed sandbox commands with a deadline, isolated model configuration and explicit permission to modify sandbox files.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./pi --yes
abx run <sandbox-id> pi_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('pi_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/pi_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "1.3.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

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

### Additional current-version platform-step acceptance

[Actual native steps](evidence/express-2026-10-20T130320Z.json): official READY, Python SDK creation, current CLI/SDK smoke and independently confirmed owned sandbox/template cleanup. This step receipt covers version/tools smoke; its separate image/model receipt retains its original scope.

### 2026-10-20 full step checkpoint: template1.0.1

[Real current-version steps](evidence/express-2026-10-20T155246Z.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155246Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 10 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
