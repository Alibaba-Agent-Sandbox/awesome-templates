# code-server

[中文](README.zh-CN.md)

## What it does

Runs the pinned code-server browser IDE with mandatory password authentication, owned start/status/stop and isolated configuration, user data and extensions. Caller IDE settings stay intact.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49; official code-server4.141.0 standalone Linux x86_64/aarch64 assets with bundled upstream Node/VS Code runtime. [assets.json](assets.json) fixes URLs, byte lengths and official SHA256. Bundled license notices are preserved. Published server package; generation2/non-root user.

## Problem solved

A real browser IDE for editing sandbox workspaces without local Docker, KVM, desktop display or a model key.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

Replace the password placeholder with a unique password of at least 12 bytes. It does not replace `ABX_SERVER_TOKEN`.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CODE_SERVER_PASSWORD='<choose-a-long-unique-password>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//code-server --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" code_server_start --json-args '{"port":8443,"timeout_s":60}'
```

Returns `running: true`, `port: 8443`, `auth: password`. Resolve port 8443 and log in to the IDE with `CODE_SERVER_PASSWORD`.

The IDE is separate from the port 9000 command API. Resolve it with `await sb.network.resolve(8443)` and open it through the [preview guide](../docs/preview-proxy.md), preserving gateway authentication. Extension marketplace/Git remote accounts require their own login; local credentials are not inherited. IDE files live under `/home/user/app`; they survive IDE stop and disappear when the sandbox is deleted.

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
            result = await client.commands.run('code_server_start', port=8443, timeout_s=60)
            print(result)
        finally:
            try:
                await client.commands.run('code_server_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/code_server_start`

```json
{
  "port": 8443,
  "timeout_s": 60
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/code_server_stop` with `{}`.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| code_server_version | none | actual installed version string |
| code_server_start | password: str optional empty=server CODE_SERVER_PASSWORD; port: int=8443,1024..65535 excluding9000; cwd: str empty=WORKSPACE,existing workspace directory; timeout_s: int=60,1..120 | {port,running:true,auth:password} after actual health |
| code_server_status | none | {running:false}, or {running:true,port,auth:password} |
| code_server_stop | none | {running:false} only after owned processes exit, kernel listener absence and private-state cleanup |
| code_server_self_test | none; existing owned IDE must be stopped | CODE_SERVER_OK after real password rejection/login/workbench and cleanup |

Passwords require12..256 UTF-8 bytes without NUL. Occupied ports and duplicate starts fail before launch. Stop never kills a process by generic name. Failed startup/cleanup does not report success. An inherited random owner marker and Linux pidfds pin owned upstream workers before signaling; kernel listener absence is independently checked.

## Configuration

For an operator-local SDK preview that preserves upstream TLS, see the [local preview operation](../docs/preview-proxy.md).


WORKSPACE defaults to /home/user/app. CODE_SERVER_PASSWORD and ABX_SERVER_TOKEN are empty manifest placeholders. The former can be supplied per call; the latter protects the9000 command API and does not replace IDE authentication on8443. See [prewarmed environment](../docs/runtime-environment.md). Private directories/config are0700/0600. Cloud/model keys are not inherited by the IDE. Update checks and telemetry are disabled.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx run "$SANDBOX_ID" code_server_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU/2048MB; command API9000 and IDE8443. Other port choices require separate provider forwarding. Image build enforces at most8GiB visible rootfs with du -sx; download budget240seconds and exact asset lengths. Startup is bounded to120seconds, inspection/child output are bounded. Stop removes this IDE instance's config/user data/extensions; workspace files remain.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/code-server.md).

## Issues

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53); CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template: Apache-2.0; code-server: MIT. Preserve official bundled LICENSE/third-party notices, including VS Code/Node components. User-installed extensions retain their own licenses. [Upstream release](https://github.com/coder/code-server/releases/tag/v4.141.0).
