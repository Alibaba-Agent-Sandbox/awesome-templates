# python-hello

[中文](./README.zh-CN.md)

## What it does

A small Python development sandbox that greets callers, executes inline Python or uploaded scripts, and runs pytest. It also demonstrates a hidden command and a custom GET route. Named commands run on port 9000 through `agent-sandbox-server`.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Python 3.13 and Node.js 20. `abx template deploy` resolves the defaults to `cn-hangzhou` and `v0.0.49`.
- `pytest==8.4.2` is installed in the image for the `test` command.
- Non-root runtime `user`, working directory `/home/user/app`, generation 2. The platform launches the YAML `start_cmd` and probes `ready_cmd`.

## Problem solved

Use this template to learn the named-command contract or to upload a Python program, execute it, and test it through the same sandbox. Inline code, script paths and pytest paths all use one workspace. This avoids scripts accidentally executing in `/app` while uploaded files live elsewhere.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./python-hello --yes
abx run <sandbox-id> hello --json-args '{"name": "Express"}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

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

All arguments below are strings with no template-defined length limit. Paths may be relative to the workspace or absolute and must be accessible by `user`; code runs with that user's permissions. These commands intentionally execute supplied Python. Give access only to trusted callers.

| Command | Parameters | Default / required | Result | Execution deadline |
|---|---|---|---|---|
| `hello` | `name: str` | Optional, `World` | `Hello, <name>!` | No subprocess |
| `run_script` | `code: str` | Required | Python stdout | 30 seconds |
| `run` | `file: str` | Optional, `main.py` | Script stdout | 60 seconds |
| `test` | `path: str` | Optional, `.` | pytest stdout | 120 seconds |
| `_debug_info` | None | Hidden from discovery, callable | Object with `python` and `system` | No subprocess |

`run_script` invokes the server's Python executable with `-c`; `run` passes the file as an argv element; `test` uses `python -m pytest -p no:cacheprovider <path>`. Shell interpolation is not used. Nonzero exits (including pytest finding no tests), process startup failures and execution deadlines return HTTP 500 with a fixed diagnostic and the exit code when available. Failure messages omit argv, source code and captured output; successful stdout is returned by design and can contain data printed by your program. `test` requires your uploaded tests; the image contains no sample tests. Empty strings are accepted as strings and may produce subprocess errors.

## Configuration

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `WORKSPACE` | No | Directory containing `commands.py` | Existing directory used by all Python subprocesses; override alongside your upload paths. |
| `ABX_SERVER_BASE_DIR` | No | `/home/user` | File API path boundary; a custom workspace must be inside the configured boundary. This does not restrict arbitrary Python execution. |
| `ABX_SERVER_PORT` | No | `9000` | Local `python3 commands.py` port; cloud `start_cmd` explicitly uses 9000. |
| `LANG` | No | `C.UTF-8` | Unicode process output. |

Before `template launch`, securely export the secret variables declared empty in the manifest so the application reads them at startup. Keep values out of images, YAML and logs.

## Resources

2 vCPU, 2048 MB RAM, port 9000, and the provider's root filesystem (about 10G on Express). No GPU, Docker, KVM or model API key is needed. Large jobs can exceed memory or the command deadline; use a suitable process API/provider for those jobs.

## Runtime verification

On 2026-10-16, the current command source with pytest 8.4.2 passed the external
HTTP suite (20 PASS lines, no failures) on `alicloud-express`, including actual
script/pytest execution and remote file transfer. The owned sandbox was deleted.
[Runtime evidence](evidence/runtime-express-2026-10-16.json) records source/package
hashes; the [check log](evidence/runtime-express-2026-10-16.log) records assertions.
This uses runtime-installed dependencies in the platform base sandbox and does
not verify this revision's Dockerfile build or newly deployed template.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This historical run used the pinned e2cb27e server-source override matching the then-current image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

Add a typed function with `@command("name")` in `commands.py` and keep `start()` under the main guard. Return a JSON-serializable value and raise on failed subprocesses. Keep tool arguments in an argv list. Pin new dependencies in the early Docker install layer and copy commands last so code edits reuse installed packages. Update both READMEs, YAML smoke cases and [design](../docs/design/python-hello.md) together.

From the repository root with the development server, `httpx`, pytest and PyYAML installed:

```bash
python3 scripts/check_template.py python-hello
python3 -m pytest python-hello/test_command_errors.py -q
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py python-hello
```

The local runner starts the server with a real workspace and exercises file upload/download/list/delete, uploaded scripts, a passing pytest case and a deliberately failing pytest case. File failures fail acceptance instead of being skipped. The Express harness requires configured credentials plus Docker, writes evidence only after successful CLI/SDK smoke cases, and cleans up the sandbox/template it creates. An Express smoke pass alone does not run every local regression remotely.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py python-hello` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and the [template specification](../docs/template-spec.md). Record image-build, cloud and local results separately; keep historical evidence unchanged.

## Issues

Template issue: [awesome-templates#21](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/21). File template bugs in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), Python client/server bugs in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI bugs in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Use `[templates]` for SDK/CLI issue titles and include a secret-free repro, provider, generation and source revision.

## License

Apache-2.0. See [LICENSE](../LICENSE).

### Explicit portable image profile

For OpenSandbox, select `--build-profile portable` with
`abx template launch`. `Dockerfile.portable` pins the Python base by digest,
creates its non-root user and installs the pinned command server directly. The
default Dockerfile retains its Express platform placeholders; providers do not
rewrite either recipe or inject a wheel. Template launch starts the
server through `exec.run` after creation. The selected profile and exact source
bytes form the launch identity. A profile declaration is not a real-backend pass.

Python consumes a prepared immutable image with `agent_sandbox.api.template.launch_template(manifest, provider="opensandbox", reference=image_digest, application_token=token)`. Pass the original manifest so its startup, readiness and services remain intact; use the returned session to invoke commands and close it to destroy its owned sandbox. Python does not prepare source images.
