# python-hello

[中文](README.zh-CN.md)

## What it does

A small Python development sandbox that greets callers, executes inline Python or uploaded scripts, and runs pytest. It also demonstrates a hidden command and a custom GET route. Named commands run on port 9000 through `agent-sandbox-server`.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` supplies Python 3.13 and Node.js 20. `abx template deploy` resolves the defaults to `cn-hangzhou` and `v0.0.49`.
- `pytest==8.4.2` is installed in the image for the `test` command.
- Non-root runtime `user`, working directory `/home/user/app`, generation 2. `abx template launch` executes the YAML `start_cmd` and probes `ready_cmd`.

## Problem solved

Use this template to learn the named-command contract or to upload a Python program, execute it, and test it through the same sandbox. Inline code, script paths and pytest paths all use one workspace. This avoids scripts accidentally executing in `/app` while uploaded files live elsewhere.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" run_script --json-args '{"code":"from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath(\"summary.txt\").write_text(f\"total={total:.2f}\\n\")\nprint(f\"total={total:.2f}\")"}'
```

Returns stdout `total=51.30` and creates `summary.txt` for download.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('run_script', code='from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath("summary.txt").write_text(f"total={total:.2f}\\n")\nprint(f"total={total:.2f}")')
            print(result)
            Path('summary.txt').write_bytes(await sb.files.read_bytes('/home/user/app/summary.txt'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/run_script`

```json
{
  "code": "from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath(\"summary.txt\").write_text(f\"total={total:.2f}\\n\")\nprint(f\"total={total:.2f}\")"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

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

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx download "$SANDBOX_ID" /home/user/app/summary.txt ./summary.txt
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

### Explicit portable image profile

For OpenSandbox, select `--build-profile portable` with
`abx template launch`. `Dockerfile.portable` pins the Python base by digest,
creates its non-root user and installs the pinned command server directly. The
default Dockerfile retains its Express platform placeholders; providers do not
rewrite either recipe or inject a wheel. Template launch starts the
server through `exec.run` after creation. The selected profile and exact source
bytes form the launch identity. A profile declaration is not a real-backend pass.

Python consumes a prepared immutable image with `agent_sandbox.api.template.launch_template(manifest, provider="opensandbox", reference=image_digest, application_token=token)`. Pass the original manifest so its startup, readiness and services remain intact; use the returned session to invoke commands and close it to destroy its owned sandbox. Python does not prepare source images.

## Resources

2 vCPU, 2048 MB RAM, port 9000, and the provider's root filesystem (about 10G on Express). No GPU, Docker, KVM or model API key is needed. Large jobs can exceed memory or the command deadline; use a suitable process API/provider for those jobs.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/python-hello.md).

## Issues

Template issue: [awesome-templates#21](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/21). File template bugs in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), Python client/server bugs in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI bugs in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Use `[templates]` for SDK/CLI issue titles and include a secret-free repro, provider, generation and source revision.

## License

Apache-2.0. See [LICENSE](../LICENSE).
