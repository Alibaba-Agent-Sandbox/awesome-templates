# prime-agent

## What it does

Runs the unchanged stable Prime Agent0.10.0 native Rust CLI with its original CPython REPL tool named `ipython`. Uses an explicitly approved compatible model and supported fixed kernel interpreter. This bounded headless coding slice does not qualify daemon sessions, recursive agents, subscription models or research benchmarks. [official release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0); [pinned native source](https://github.com/PrimeIntellect-ai/prime-agent/tree/763094e1b6a7c17450ee8399b06cda1853847ca5).

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Original Prime Agent `0.10.0`, the original CPython REPL backend and a fixed local kernel interpreter/dependency environment.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [upstream notice](UPSTREAM-NOTICE.md)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

This example uses the configured Chat Completions model with the original local CPython REPL backend. No Prime subscription or interactive login is required. The agent can execute Python and change project files; nested/delegated agents are disabled in this profile.

For the DashScope base below, create a Beijing-region key following [Model Studio API-key setup](https://www.alibabacloud.com/help/en/model-studio/get-api-key) and use a model allowed for that account. Other regions and Coding Plans use their matching keys/endpoints.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export PRIME_MODEL_API_KEY='<your-model-or-vendor-key>'
export PRIME_MODEL_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export PRIME_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//prime-agent --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" prime_agent --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","cwd":"/home/user/workspace","command_timeout":300}'
```

The task creates `generated_hello.py` and `GENERATED_REPORT.md` in `/home/user/workspace`. The example explicitly enables the required editing/tools; use an owned disposable sandbox. The SDK and HTTP examples are alternative ways to submit the same task; choose one.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('prime_agent', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', cwd='/home/user/workspace', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/prime_agent` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "cwd": "/home/user/workspace",
  "command_timeout": 300
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 420 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

### Export files and cleanup

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

Expected program output: `Hello from the sandbox`. Inspect actual files before using them; a successful-looking model response does not guarantee files exist. Files do not automatically update the template or your machine; export them before deleting the sandbox.

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| prime_agent_version | none | Actual checked binary/version: `{native_version:"0.10.0"}`; no model |
| prime_agent_kernel_check | none | Original CPython runtime protocol3,12 required imports: `{protocol_version:3,required_imports_checked:12}`; no model or bootstrap |
| prime_agent_setup_check | none | mode `original-native-prime-cpython-repl`; subscription_required:false; api_key_set/base_url_set/model_set booleans; read-only |
| prime_agent | prompt: required nonempty string1..32768UTF-8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"0.10.0",native_completed:bool}`; real original native tools may modify files |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| PRIME_MODEL_API_KEY | empty; required for coding | Approved compatible-model key |
| PRIME_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS base; literal local HTTP for authored fixtures only; no userinfo/query/fragment; max2048characters |
| PRIME_MODEL | empty; required for coding | Actual model identifier; max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Captured when commands.py loads. Private0700HOME/0600models.json uses apiKey="ABX_PRIME_MODEL_KEY", storing an environment reference instead of key bytes. No operator cloud/GitHub/vendor credentials are inherited. The fixed kernel launcher removes ABX_PRIME_MODEL_KEY before original CPython starts; same-user OS access means this is environment minimization, not credential isolation. Literal/JSON-escaped key and base values are redacted from returned output. Telemetry/traces/refinement/compaction/factory and discovery are disabled; rlmMaxDepth0 is set. Original print mode supplies no child host and therefore uses NoRlmChildren: no delegated agent is launched. No daemon mode is started. Custom model pricing is unspecified; zero defaults are not a free-service claim.

## Resources

2 vCPU, 2048 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/workspace`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges. This pinned installation targets Linux x86_64.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/prime-agent.md).

## Issues

Track [Issue69](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69). Report sanitized reproducible wrapper/native/provider failures with source/version. Never attach private keys/endpoints or raw prompts/model output.

SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Authored wrapper Apache-2.0. Original Prime Agent MIT; original PHOTON third-party notice Apache-2.0. [Distribution and attribution](UPSTREAM-NOTICE.md); full upstream notices remain installed without relicensing.
