# code-server

## What it does

Runs the pinned code-server browser IDE with mandatory password authentication, owned start/status/stop and isolated configuration, user data and extensions. Caller IDE settings stay intact.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49; official code-server4.141.0 standalone Linux x86_64/aarch64 assets with bundled upstream Node/VS Code runtime. [assets.json](assets.json) fixes URLs, byte lengths and official SHA256. Bundled license notices are preserved. Server SDK is pinned to e2cb27e; generation2/non-root user.

## Problem solved

A real browser IDE for editing sandbox workspaces without local Docker, KVM, desktop display or a model key.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./code-server --yes
abx run <sandbox-id> code_server_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('code_server_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/code_server_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "4.141.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

For an operator-local SDK preview that preserves upstream TLS, see the [local preview operation](../docs/preview-proxy.md). Direct-domain and sdk-local controller results are recorded separately.


WORKSPACE defaults to /home/user/app. CODE_SERVER_PASSWORD and ABX_SERVER_TOKEN are empty manifest placeholders. The former can be supplied per call; the latter protects the9000 command API and does not replace IDE authentication on8443. See [prewarmed environment](../docs/runtime-environment.md). Private directories/config are0700/0600. Cloud/model keys are not inherited by the IDE. Update checks and telemetry are disabled.

## Resources

2vCPU/2048MB; command API9000 and IDE8443. Other port choices require separate provider forwarding. Image build enforces at most8GiB visible rootfs with du -sx; download budget240seconds and exact asset lengths. Startup is bounded to120seconds, inspection/child output are bounded. Stop removes this IDE instance's config/user data/extensions; workspace files remain.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

For local tools use install_runtime.py --prefix in your own directory. Image builds explicitly enable --check-rootfs; Docker host statvfs usage is not image size. Prepare [platform steps](../docs/platform-steps.md): `python scripts/prepare_steps.py code-server --output /tmp/ide-steps`; actual acceptance: `python scripts/run_steps_e2e.py code-server`. Update asset/version assertions and both docs together. WebSocket/terminal interaction needs its own recorded test; authenticated HTML alone does not certify it.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [spec](../docs/template-spec.md) and [design](../docs/design/code-server.md). Test real authentication, wrong passwords, cross-request state and kernel/process readback. A successful TCP connect to an empty proxied port is not a listener proof.

## Issues

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53); CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template: Apache-2.0; code-server: MIT. Preserve official bundled LICENSE/third-party notices, including VS Code/Node components. User-installed extensions retain their own licenses. [Upstream release](https://github.com/coder/code-server/releases/tag/v4.141.0).

### Additional current-version platform-step acceptance

[Actual steps](evidence/express-2026-10-20T135352Z.json) and [external HTTP attempt](evidence/verification-steps-2026-10-20T135352Z.json): official READY, Python SDK creation, CLI/SDK smoke and 5 HTTP PASS / 0 FAIL / 0 SKIP. Model calls remain NOT_RUN in this receipt. Independent sandbox/template and private same-account asset-cache object/bucket cleanup passed before publication. Earlier image/model receipts retain their own scope.
