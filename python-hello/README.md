# python-hello

[中文](./README.zh-CN.md)

## What it does

A small Python development sandbox that greets callers, executes inline Python or uploaded scripts, and runs pytest. It also demonstrates a hidden command and a custom GET route. Named commands run on port 9000 through `agent-sandbox-server`.

## Stack

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Python 3.13 and Node.js 20. `abx template deploy` resolves the defaults to `cn-hangzhou` and `v0.0.49`.
- Server pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`; an SDK wheel injected during deployment takes precedence.
- `pytest==8.4.2` is installed in the image for the `test` command.
- Non-root runtime `user`, working directory `/home/user/app`, generation 2. The platform launches the YAML `start_cmd` and probes `ready_cmd`.

## Problem solved

Use this template to learn the named-command contract or to upload a Python program, execute it, and test it through the same sandbox. Inline code, script paths and pytest paths all use one workspace. This avoids scripts accidentally executing in `/app` while uploaded files live elsewhere.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

Run from this repository with an already configured Express provider:

```bash
abx template deploy ./python-hello -y
abx create --template <template-id> -y
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> run_script --json-args '{"code":"print(21 * 2)"}'
abx upload <sandbox-id> ./main.py /home/user/app/main.py
abx run <sandbox-id> run --arg file=main.py
abx upload <sandbox-id> ./test_main.py /home/user/app/test_main.py
abx run <sandbox-id> test --arg path=test_main.py
```

The deploy result supplies `<template-id>`; create supplies `<sandbox-id>`. `hello` returns `Hello, Ada!`; `run_script` returns `42\n`. The source and test files are your own files. `abx run` invokes a named command; use `abx exec` for shell commands. Clean up resources when finished:

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client` (import `agent_sandbox`). Until the matching release is available, use the [paired, pinned source installation](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
        print(await sb.run("run_script", code="print(21 * 2)"))
        await sb.files.write("/home/user/app/main.py", "print(6 * 7)\n")
        await sb.files.write(
            "/home/user/app/test_main.py",
            "def test_answer():\n    assert 6 * 7 == 42\n",
        )
        print(await sb.run("run", file="main.py", timeout=70))
        print(await sb.run("test", path="test_main.py", timeout=130))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`Sandbox.connect` attaches to an existing sandbox. `sb.run` returns the JSON `result` value; `sb.commands.run` is the process/shell API. The `timeout` in `sb.run` is the HTTP request timeout in seconds. The command execution deadlines are fixed below; a client timeout does not guarantee cancellation. Use process APIs for background work, reconnecting and cancellation.

## Quick start (HTTP POST)

Set `ABX_SERVER_URL` to `sb.network.get_url(9000)` for the sandbox, or `http://127.0.0.1:9000` for a local server. On Express, the port-9000 server does not require the sandbox gateway token: do not forward the envd `X-Access-Token` to an anonymous server.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello" \
  --header 'Content-Type: application/json' \
  --data '{"name":"Ada"}'
# {"result":"Hello, Ada!"}
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/run_script" \
  --header 'Content-Type: application/json' \
  --data '{"code":"print(21 * 2)"}'
# {"result":"42\n"}
```

The body is the direct JSON argument object, without an `args` wrapper. `POST /commands/run` with `{"file":"main.py"}` executes an uploaded script; `POST /commands/test` with `{"path":"test_main.py"}` runs an uploaded test. Both return `{"result":"<stdout>"}` when successful. `GET /commands` discovers public commands, and `GET /hello/Ada` returns `{"greeting":"Hello, Ada!"}`.

Server authentication is separate from provider authentication. If you set `ABX_SERVER_TOKEN` inside the sandbox, include `Authorization: Bearer $ABX_SERVER_TOKEN` on protected requests; `/health` is exempt from server-token authentication. For the SDK use `sb.server_at(9000, token=server_token).commands.run(...)` with the token supplied securely by your application. A provider whose gateway requires an access header also needs that header (for example `X-Access-Token` from `sb.network.get_access_headers()`), in addition to the server bearer token. Only Express has historical provider evidence for this template; other providers remain unverified.

Missing or invalid arguments return HTTP 400, failed authentication 401, unknown commands 404, and execution failures 500. Errors contain `error` and `type`. Named-command stdout is buffered until completion. The HTTP client timeout controls how long the caller waits; it does not cancel work on the server.

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
| `ABX_SERVER_TOKEN` | No | Empty | Optional server bearer authentication; inject at sandbox creation. |
| `WORKSPACE` | No | Directory containing `commands.py` | Existing directory used by all Python subprocesses; override alongside your upload paths. |
| `ABX_SERVER_BASE_DIR` | No | `/home/user` | File API path boundary; a custom workspace must be inside the configured boundary. This does not restrict arbitrary Python execution. |
| `ABX_SERVER_PORT` | No | `9000` | Local `python3 commands.py` port; cloud `start_cmd` explicitly uses 9000. |
| `LANG` | No | `C.UTF-8` | Unicode process output. |

Supply secret values via your existing secure configuration and `Sandbox.create(envs=...)`; store only empty secret declarations in YAML. Do not log tokens or upload credential files.

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

Version1.1.1 explicitly repairs non-root workspace-directory ownership. Current-version provider acceptance must be rerun. Earlier receipts establish only their original versions/hashes/scopes and are preserved below.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing run recorded for this template.

This statement concerns version **1.1.0**. Historical [Express evidence from 2026-10-15](./evidence/express-2026-10-15.json) proves only `hello` through CLI and SDK on **1.0.0**. It does not validate this new base image, pytest, file operations, or scripts. `tested_on` stays empty until a new provider run passes. Local HTTP checks are L0; they do not establish an image build or cloud acceptance.

</details>

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
