# muse

[中文](README.zh-CN.md)

## What it does

Run the unchanged official Meta Muse Code1.4.11-R6667.1 native headless agent, original miniswe tools and native runtime records on one owned Express computer. Coding uses an explicitly configured compatible Responses model. The authored local relay supplies the selected model catalogue and keeps the upstream key out of native/tool environments; Responses requests and streams pass unchanged. This is the original Muse binary, not a same-named substitute. [Original documentation](https://dev.meta.ai/docs/muse-code).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13, root-owned original native ELF384809176bytes with its published SHA256, Python stdlib relay/process controls, published server package 0.4.0a6. No new Python/Node dependencies. [Dockerfile](Dockerfile), [provenance](upstream.json), [upstream notice](UPSTREAM-NOTICE.md), [design](../docs/design/muse.md). The template source license does not relicense the original upstream artifact.

## Problem solved

Provide genuine original Muse file/tool execution through named SDK/HTTP commands with private per-call configuration and verified ownership. A generic compatible gateway lacks the original CLI's required `/muse-code/models`: the narrow local relay supplies that metadata, then forwards original `/responses` bytes to exactly the configured endpoint with no tool/model translation. No vendor/account/subscription fallback.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Responses**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export MUSE_MODEL_API_KEY='<your-model-api-key>'
export MUSE_MODEL_BASE_URL='https://model.example.invalid/v1'
export MUSE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//muse --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" muse --json-args '{"prompt":"Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.","command_timeout":300}'
```

Returns native completion status, model/tool call counts and buffered output; inspect the generated `hello.py` independently.

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
            result = await client.commands.run('muse', prompt='Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.', command_timeout=300)
            print(result)
            Path('hello.py').write_bytes(await sb.files.read_bytes('/home/user/app/hello.py'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/muse`

```json
{
  "prompt": "Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.",
  "command_timeout": 300
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| muse_version | none | `Muse Code 1.4.11 (1.4.11-R6667.1)` after exact original ELF verification; no model |
| muse_native_check | none | `{original_native:true,headless_json:true,anonymous_api_key_stdin:true,no_session_log:true}` from actual headless help; no model |
| muse_setup_check | none | mode `original-native-muse-explicit-responses`, native_present/model_key_set/model_base_set/model_set flags; model_account_verified:false/provider_default_fallback:false/catalog_relay:true; no values/network |
| muse | prompt: required nonempty string1..32768UTF8bytes/noNUL; cwd: string default empty, max4096bytes, existing resolved directory inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final stdout, native_completed, actual model_calls/native_tool_results, exit_code0, original binary/version/model/protocol and completed relay_calls. Original tools may edit caller project files; no raw transcript |

Fixed original argv: `exec --json --api-key-stdin --provider meta --model <configured> --preset miniswe --reasoning-effort minimal --max-model-steps16 --no-session-log --disable-reminders --no-foreign-personal-context --disable-web-tools --yolo --workspace <contained-project>`. Original settings schema_version1, endpoint_transport base_url/auth bearer and agents.execution_capacity1 are private per call. Original miniswe has no available subagent_spawn; no delegated model/tool tree is selected. Caller project instructions may load after the explicit trust flag.

Native completion requires exact correlated original model/usage/terminal records, positive completed model calls, no failed/cancelled/child calls and nonempty final text. Inspect generated files independently before using model edits. Model requests32maximum,2MiB each,4MiB per response,16native model steps; native stdout/stderr256KiB each. Issued relay requests drain before completion. Owned close/process cleanup may add up to50seconds; SDK timeout should be at least command_timeout+80. Concurrent model calls fail busy.

## Configuration

Muse requires streaming Responses API support; the code appends `/responses` to the base. A gateway exposing only `/chat/completions` cannot serve this entry.

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| MUSE_MODEL_API_KEY | empty; required for coding | Key for the explicitly selected compatible endpoint; retained only in parent relay |
| MUSE_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS Responses base, max2048characters, no userinfo/query/fragment; literal-loopback HTTP only for authored fixtures |
| MUSE_MODEL | empty; required for coding | Actual upstream model identifier,1..200allowed identifier characters |
| WORKSPACE | `/home/user/app` | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Captured at commands.py import; presence flags do not prove authentication. Key max8192/no control characters. Native receives only a fresh per-call local relay token by anonymous stdin. The parent relay uses the upstream key only for the exact approved Responses endpoint, rejects redirects and wrong route/token/model, and retains no transcript. Native/tools use a minimal environment and private HOME/cache/config; caller project artifacts persist. Same-user OS access remains; cwd containment and environment filtering are not another tenant boundary. `--yolo` selects the disposable outer sandbox as the execution boundary.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx download "$SANDBOX_ID" /home/user/app/hello.py ./hello.py
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000,8GiB image rootfs budget, no KVM/Docker/GPU or extra privileges. Original artifact downloads384.8MB; model requests need approved egress. Memory usage depends on the task. Other providers, interactive sessions, retained resume, voice/local weights, MCP/plugin services and Meta-hosted subscriptions are outside this profile.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/muse.md).

## Issues

[Template Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71) owns this delivery. [Template bugs](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); original Muse behavior belongs to its upstream support. Never attach credentials or raw private transcripts.

## License

Authored template code/documentation: [Apache-2.0](../LICENSE). Original Meta artifact terms/notices remain separate; see [attribution](UPSTREAM-NOTICE.md). No upstream open-source license, vendor endorsement or hosted-model account is asserted.
