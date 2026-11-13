# _skeleton

Scaffold for a new Agent Sandbox template. Copy this directory, then replace the command and the metadata. It is not a catalog entry.

This branch uses YAML v1 and needs matching development builds; published CLI0.5.10 does not support this format. Template attributes are under `sandbox.agent.template`. Runtime defaults belong to the Dockerfile; pass private values explicitly when creating an instance. See this page’s configuration section for their purpose and credential sources. See the [configuration specification](../docs/template-spec.md).

## What it does

Registers one named command, `hello`, on `agent-sandbox-server` at port 9000. The command returns `Hello, <name>!`.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template build` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`.
- Work directory `/home/user/app`. Runtime user `user`.
- Python 3.13 and Node.js 20 come from the base image.
- `abx deploy` starts the process with the template's `sandbox.agent.template.startCommand`. The Dockerfile stops after `USER` and `EXPOSE`.

## Problem solved

Gives a new template one directory that already satisfies [docs/template-spec.md](../docs/template-spec.md), so the layout, the server contract, and the README sections are not reinvented.

## Quick start (CLI)

`abx deploy` only prepares the template. Download this directory, run deployment from it, then replace `<prepared-template-id>` with the returned template ID and run `run.py`. The script creates an instance and explicitly starts the application with this page’s runtime settings. It generates an application token and stores it privately in `.sandbox-session.json`, without printing it. Existing session files are never overwritten; use `--session` for another run.


Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Save that ID in `ABX_SANDBOX_ID` below.

```bash
export ABX_PROVIDER=alicloud-express
abx deploy ./_skeleton --yes
python3 -m pip install "agent-sandbox-client==0.4.0a7"
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command run "$ABX_SANDBOX_ID" hello --json-args '{"name": "Express"}'
```

`deploy` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client==0.4.0a7` in a virtual environment and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

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

Edit resource values under `sandbox.agent.template` in `template.yaml` and image defaults in the Dockerfile. `run.py` reads runtime values from the process environment, limited to its explicit `RUNTIME_ENV_NAMES`. Empty placeholders do not put credentials into the image. Application startup belongs to `run.py`, after creation, so dynamic authentication is not frozen in a template snapshot. External SDK/HTTP clients can read `application_token` from the private `.sandbox-session.json`, or reuse an explicitly supplied `ABX_SERVER_TOKEN`.

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | No | Generated by `run.py` | Generated by run.py unless explicitly supplied; external clients read the private session file. |
| `ABX_SERVER_PORT` | no | `9000` | Port `start()` binds for a local `python3 commands.py`. |

Provide secret values before the command server starts; use create-time env only when the provider starts that server with it. See [runtime environment](../docs/runtime-environment.md). Do not write them into the image, the Dockerfile, or a log.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

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
