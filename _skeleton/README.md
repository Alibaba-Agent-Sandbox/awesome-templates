# _skeleton

Scaffold for a new Agent Sandbox template. Copy this directory, then replace the command and the metadata. It is not a catalog entry.

## What it does

Registers one named command, `hello`, on `agent-sandbox-server` at port 9000. The command returns `Hello, <name>!`.

## Stack

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`.
- `agent-sandbox-server` from python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505` when the build context has no wheel: `pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40-hex>.tar.gz#subdirectory=server-sdk"`. A wheel injected by `abx template deploy` wins. `agent-sandbox-server==X.Y.Z` is the other allowed pin once that release exists on PyPI. `0.3.0` was not on PyPI on 2026-10-15.
- Work directory `/home/user/app`. Runtime user `user`.
- Python 3.13 and Node.js 20 come from the base image.
- The platform starts the process with `start_cmd`. The Dockerfile stops after `USER` and `EXPOSE`.

## Problem solved

Gives a new template one directory that already satisfies [docs/template-spec.md](../docs/template-spec.md), so the layout, the server contract, and the README sections are not reinvented.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./_skeleton --workflow application --yes
abx run <sandbox-id> hello --json-args '{"name": "Express"}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('hello', name='Express'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/hello`, with `Content-Type: application/json` and this direct argument object:

```json
{"name": "Express"}
```

Expected response for this check:

```json
{"result": "Hello, Express!"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| hello | `name`: string, optional, default `World` | string | Say hello. |

`POST /commands/hello` with body `{"name":"Ada"}` returns `{"result":"Hello, Ada!"}`. A missing required argument is HTTP 400. An exception inside the function is HTTP 500 with `{"error","type"}`.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Port `start()` binds for a local `python3 commands.py`. |

Provide secret values before the command server starts; use create-time env only when the provider starts that server with it. See [runtime environment](../docs/runtime-environment.md). Do not write them into the image, the Dockerfile, or a log.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

No provider has a passing run recorded for this template.

## Secondary development

Copy `_skeleton` to a kebab-case directory whose name matches `^[a-z0-9][a-z0-9-]*$`. Set `template.yaml` `name` to that directory name. Replace `hello` with commands that call the upstream program, and pin every installed version in the Dockerfile. Fill `docs/design/<name>.md` from [docs/design/_TEMPLATE.md](../docs/design/_TEMPLATE.md). Add one `awesome-templates.yaml` entry. Run `python3 scripts/check_template.py <dir>`.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
