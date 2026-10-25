# opencode

OpenCode (`sst/opencode`) in an Agent Sandbox. The image installs npm package `opencode-ai@1.19.0`. Named commands call that CLI. The primary call is headless `opencode run`. `opencode serve` is a second HTTP server on port 4096.

## What it does

`text` combines text from every assistant step, including intermediate commentary.
For strict final-response checks, inspect the last completed `step_finish` with
reason `stop` in `stdout`, scoped to the returned session. The verifier also
requires independent code, artifact and exact-session continuation checks.

`agent-sandbox-server` listens on port 9000 and registers commands that run `opencode`. `opencode_run` executes one non-interactive `opencode run --format json` and returns the assistant text, sanitized JSON events, and the session id. `opencode_version` and `opencode_setup_check` check the pinned binary and `opencode.json` without calling a model.

`opencode_serve_start` starts `opencode serve` on port 4096 bound to `0.0.0.0`. That process is OpenCode's own HTTP API (`GET /global/health`). Resolve it with `await sb.network.resolve(4096)` and preserve the returned gateway headers alongside OpenCode authentication. The platform `start_cmd` does not start it.

`opencode` is the previous command name. It runs the same argv as `opencode_run` and returns the sanitized JSON-event stdout string.

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

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./opencode --yes
abx run <sandbox-id> opencode_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('opencode_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/opencode_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "1.19.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns | Upstream |
|---|---|---|---|
| `opencode_run` | see the table below | object | `opencode run --pure --format json --auto ...` |
| `opencode` | same as `opencode_run` | string (sanitized JSON events) | same argv as `opencode_run` |
| `opencode_version` | none | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | none | `"ok"` | `opencode --version` plus a read of `opencode.json` |
| `opencode_serve_start` | `port` integer, default `4096`; `hostname` string, default `0.0.0.0` | object | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | none | object | localhost `GET /global/health` |
| `opencode_serve_stop` | none | `"stopped"` | `SIGTERM` to the process this template started |

`opencode_run` parameters:

| Parameter | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `prompt` | string | yes | | Positional argv after `--`; never interpolated into a shell string. |
| `model` | string | no | `OPENCODE_MODEL`, else `dashscope/qwen3.8-flash` | `--model`, form `provider/model`. |
| `agent` | string | no | empty (CLI primary agent, `build`) | `--agent` when non-empty. |
| `session` | string | no | empty | `--session` to continue that session id. |
| `continue_session` | boolean | no | `false` | `--continue` (last session). Pass a JSON boolean. |
| `cwd` | string | no | `/home/user/app` (the module directory for local runs) | `--dir` and the child working directory. Must be an existing directory. |

`opencode_run` returns:

| Field | Meaning |
|---|---|
| `text` | Concatenated `type: text` parts from the JSON events. |
| `stdout` | JSON events with secret environment values redacted, one event per line. |
| `session_id` | `sessionID` from those events, or empty. |
| `model` | Selector that was passed to `--model`. |
| `agent` | Agent name that was passed, or empty. |
| `cwd` | Directory that was passed to `--dir`. |

A missing `prompt` is HTTP 400. A non-zero CLI exit is HTTP 500 `{"error","type":"RuntimeError"}`. CLI error output is omitted, so prompts, tool arguments, and credentials are not copied into error messages. Successful event values redact known environment secrets. Serve logs are discarded. Timeout is 600 seconds. Stdin is `/dev/null`.

`opencode_serve_start` returns `running`, `port`, `hostname`, `pid`, `healthy`, and `version`. It waits until `GET http://127.0.0.1:<port>/global/health` returns `{"healthy": true, "version": "1.19.0"}`. The target-side health probe supports `OPENCODE_SERVER_PASSWORD` and requires the pinned version. Resolve the public endpoint and gateway headers with `await sb.network.resolve(port)`; the localhost address is internal. A second start with the same port and hostname returns the current status. Start/status/stop are serialized by an in-process lock. Stop signals only the Popen child owned by this interpreter and verifies its process group; old PID files are never read. Restarting the command server does not adopt an older serve process; recycle the sandbox to clean up such a process.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_LLM_API_KEY` | for a DashScope call | empty | `{env:ABX_LLM_API_KEY}` in `opencode.json`. Inject at create. |
| `ABX_LLM_BASE_URL` | for a DashScope call | empty | OpenAI-compatible base URL, including the `/v1` path. `{env:ABX_LLM_BASE_URL}`. |
| `OPENCODE_MODEL` | no | `dashscope/qwen3.8-flash` | Used when `model` is empty. |
| `OPENCODE_API_KEY` | no | empty | OpenCode Zen credential when `model` is `opencode/<id>`. |
| `OPENCODE_SERVER_PASSWORD` | no | empty | Basic auth password for `opencode serve`. The CLI warns when it is unset. |
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |
| `OPENCODE_CONFIG` | no | `/home/user/app/opencode.json` | Config file the child process reads. |
| `OPENCODE_DISABLE_AUTOUPDATE` | no | `true` in the image | Stops the pinned CLI from upgrading itself. |
| `ABX_SERVER_PORT` | no | `9000` | Port `start()` binds for a local `python3 commands.py`. |

`opencode.json` defines provider `dashscope` with npm package `@ai-sdk/openai-compatible`. Model ids shipped in that file are `qwen3.8-flash` and `qwen3.8-max`. Another id under `dashscope/` is added to a temporary config for that one `opencode_run`. A model on a different provider uses the config file as written; put that provider in `opencode.json` or pass a `model` the file already allows.

Before `template launch`, securely export the secret variables declared empty in the manifest so the application reads them at startup. Keep values out of images, YAML and logs.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| ports | 9000 (command server), 4096 (`opencode serve`, only after `opencode_serve_start`) |
| disk | platform rootfs, about 10G on Express |

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical2.0.1 image/model qualification

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.0.1; actual SDK-created image, CLI/SDK commands,28strict real-model assertions and independent sandbox/template/registry cleanup | [2026-10-20](evidence/express-2026-10-20.json) · [model](evidence/model-image-2026-10-20T142001Z.json) |

The exact-source CI image is independently verified before registration. The actual model edits existing source, creates a new artifact and passes unchanged original tests, fresh held-out assertions and exact-session continuation. The matching runtime also has [real platform-step basic acceptance](evidence/verification-steps-2026-10-19T184023Z.json), which does not itself claim model acceptance. The image actually injects server e2cb27e; the older standalone Docker fallback is a separate build path. See [current acceptance](../.agents/evidence/verify/2026-10-20-native-coding-sdk-acceptance.md) for provenance, limits and historical failures.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

The command bodies live in `commands.py`. `opencode_run` builds an argv list; keep prompts and model ids as list elements. Pin every new installer in the Dockerfile (`npm install -g name@version` or `pip install name==version`).

To change the default model, edit `OPENCODE_MODEL` in `template.yaml` and the `model` field in `opencode.json`, and add the id under `provider.dashscope.models` when the provider is `dashscope`. The id has to exist on the endpoint `ABX_LLM_BASE_URL` points at.

Copy `_skeleton` only when starting a different template. This directory is the OpenCode entry. Fill changes against [docs/template-spec.md](../docs/template-spec.md) and [docs/design/opencode.md](../docs/design/opencode.md).

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py opencode` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

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

## Local acceptance and model acceptance

Run `python3 -m pytest opencode/test_commands.py opencode/test_e2e_protocol.py -q` for regressions. For real HTTP L0, install `opencode-ai@1.19.0` on the server, start this template, and run `E2E_BASE_URL=<target-url> E2E_WORKSPACE=<target-workspace> E2E_RUN_LLM=0 python3 opencode/e2e_test.py`. The target must have the pinned CLI; missing tools fail. Tests exercise real target-side Python through `/shell`, download the produced file, and start/check/stop OpenCode serve. The tester never uses its own `opencode` or probes its own localhost to infer a remote target's state. `opencode_setup_check` never writes configuration or starts a service.

L0 success is not model acceptance. L3 is explicitly NOT RUN by default. Enable both `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1` with model configuration already injected into the server. L3 uploads a broken existing calc.py and fixed test_calc.py, reproduces the failure, and asks the real agent to fix the source and create report.txt plus acceptance.txt. It downloads the source/tests/artifacts, requires the original tests to be byte-identical, reruns all three tests remotely with an explicit project cwd, and checks additional held-out assertions.

After the coding checks pass, the verifier makes a second `opencode_run` call with the exact returned `session_id` in `session`, never global `continue_session`. That turn must read the existing report and source and create a previously absent resume.json containing the original report's actual SHA-256 and the results of additional `add` calls. The controller computes the expected digest and sums independently without placing them in the prompt, downloads the new artifact, requires the same returned session ID, checks that source/tests/report/acceptance bytes remain unchanged, and reruns held-out assertions remotely. Wrong-session replies, missing or incorrect resume artifacts, and mutations of the original files fail acceptance. The verifier then removes only its unique project directory. A marker response or new file alone cannot pass. No client-side model key is needed to test a preconfigured remote server. Set `ABX_SERVER_TOKEN` for application Bearer authentication; provider gateway headers use `E2E_GATEWAY_HEADERS_JSON`. `/code/run` is an optional SDK dev-tools endpoint; capability metadata alone does not enable it. These source/runtime checks do not establish Dockerfile L1 or template-deploy L2 acceptance.

External HTTP target requests respect environment proxy settings. The sandbox-internal loopback health check alone connects directly to its own serve process. The fake-remote protocol tests validate coding and exact-session continuation, including wrong-session/hash/calculation responses and file tampering, using actual local test subprocesses; they do not establish real model/provider acceptance.

On 2026-10-16 the Express source-runtime run passed all 28 HTTP checks with a real `dashscope/qwen3.8-flash` model, including the exact-session continuation above and both project/sandbox cleanup. This run uploaded source/configuration to an existing base sandbox and installed pinned dependencies there. Image build L1 and new-template deploy L2 remain unverified; `tested_on` stays empty. See the [verification record](../.agents/evidence/verify/2026-10-16-opencode-session-resume-clean-wheel.md).

Independent test and held-out processes run isolated Python, preload the standard
library and compile the actual source bytes. The three original tests must all
run successfully without skips or expected failures. Each post-agent verifier,
including the exact-session resume recheck, requires its own newly generated
completion acknowledgement. Static output, early zero exits and stale bytecode
cannot stand in for completed checks. This detects incomplete execution; it is
not an OS isolation boundary against hostile code with the same user authority.
Historical real-model results predate this guard; the hardened controller needs
its own actual-image/model run before that new acceptance is claimed.

### Template2.0.2 runtime ownership

A real non-root step run of2.0.1 passed version/setup but failed native serve startup/status/idempotence. A separate owned runtime probe reproduced PermissionDenied opening ~/.local/share/opencode/log/opencode.log. Root installation/version probes ran after the first HOME ownership handoff, while the final handoff covered only the app directory. Version2.0.2 recursively hands the template-owned app/.local/.config state to user after installation; it retains USER user and unchanged OpenCode1.19.0. Read-only setup now detects unwritable native state without reading logs or creating files. [Issue156](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/156) tracks the real regression and repeat. Older2.0.1 image/model receipts are historical and do not qualify2.0.2; new real2.0.2 step/full-HTTP verification passed15/0/0 in100.59s; [receipt](evidence/verification-steps-2026-10-20T160725Z.json).
