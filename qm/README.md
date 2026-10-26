# qm

[中文](README.zh-CN.md)

## What it does

Run unchanged original QM0.1.0 exported Pi harness and original tool context on one owned Express computer, using an authored backend built on the real Agent Sandbox Node.js HTTP SDK. Coding uses an explicitly approved compatible model. Original full multiplayer core/web/Slack/Postgres durability/cron/subscription features are not started or qualified. Original default Docker backend is not used. This is a bounded original-library integration, not a shell program named qm or a replacement agent. [Original source](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13. SHA256-pinned original Node24.16.0 archive/executable, full original QM source0.1.0/immutable commit and original npm integrity lock. Original Node SDK0.1.0 source63d7cd8ece221b9f968eef51eeb932ea334c90d3 built with its original lock/build script; The npm package is not published; this image builds the reviewed immutable SDK source. Published server package. [Dockerfile](Dockerfile), [provenance](upstream.json), [QM lock](package-lock.json), [SDK lock](sdk-package-lock.json), [design](../docs/design/qm.md).

## Problem solved

Run genuine exported original QM functionality with SDK-backed tools without nested Docker or cloud credentials in model tools. The Node SDK is an in-sandbox HTTP client; outer creation/kill belongs to the caller's Python Sandbox SDK. One caller project per backend; attach/provision does not create another cloud VM.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export QM_MODEL_API_KEY='<your-model-api-key>'
export QM_MODEL_BASE_URL='https://model.example.invalid/v1'
export QM_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//qm --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" qm --json-args '{"prompt":"Create hello.py in the current project. It must print Hello from QM. Run it and report the output.","command_timeout":300}'
```

Returns the original QM agent result and real SDK tool-call counters. Read `hello.py` independently to inspect the work.

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
            result = await client.commands.run('qm', prompt='Create hello.py in the current project. It must print Hello from QM. Run it and report the output.', command_timeout=300)
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

`POST /commands/qm`

```json
{
  "prompt": "Create hello.py in the current project. It must print Hello from QM. Run it and report the output.",
  "command_timeout": 300
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| qm_version | none | Actual checked `{qm_version:"0.1.0",node_version:"24.16.0",sdk_version:"0.1.0"}`; no model/network |
| qm_native_check | none | `{original_qm_harness:true,original_tool_context:true,actual_sdk_client:true}`; real original imports, no backend/model request |
| qm_setup_check | none | Read-only mode `original-qm-agent-sandbox-sdk-slice`, SDK base/token presence and optional model presence booleans; never secret values |
| qm_sdk_smoke | none | Exact string after original QM tool context/actual SDK file+execution+listing+removal round trip and owned fixture absence; no model; private transient files |
| qm | prompt: required nonempty string1..32768UTF8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final reply as stdout, actual source/qm/node/sdk identities, native_completed, original model_calls/native_tool_calls/native_tool_results, completed sdk_calls, stopped/pending_approvals and exit_code0; native tool file changes persist |

Requests serialize; overlap fails busy. Native process stdout/stderr256KiB each and anonymous request256KiB. Per SDK tool command: explicit Bash, minimal environment/private HOME,64KiB per returned stream, deadline1..120seconds and identity-pinned process-group/nonce/pidfd descendant cleanup. Backend exec allows up to50seconds startup/cleanup allowance; model wrapper up to90seconds. Give the client at least80seconds extra for backend exec and130seconds for qm. File library bytes max1MiB, public named text/read32KiB, directory names max1024and32KiBJSON. Larger values fail; no silent truncation. Resolved file paths stay inside the selected project; SDK helpers independently reject traversal/symlink escapes and root removal. Shell tools have the outer user's OS authority; cwd is not a separate OS security boundary.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. The model and endpoint must support the original QM tool-calling flow.

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/app | Existing caller project root, captured at startup |
| QM_SANDBOX_BASE_URL | http://127.0.0.1:9000 | Actual SDK data-plane server on the same owned computer; literal local HTTP only, no userinfo/query/fragment/path |
| QM_SANDBOX_TOKEN | empty; optional | SDK server's independent Bearer token; falls back to ABX_SERVER_TOKEN for the default same server |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |
| QM_MODEL_API_KEY | empty; required for qm | Approved compatible model key; anonymous stdin/private native memory |
| QM_MODEL_BASE_URL | empty; required for qm | Explicit HTTPS compatible Chat Completions API base; local HTTP for authored fixtures only; no userinfo/query/fragment, max2048characters |
| QM_MODEL | empty; required for qm | Actual model identifier, max200allowed characters; no default vendor fallback |

Captured when commands.py loads; read-only setup flags do not prove connectivity. SDK token max8192/noCRLF/NUL; model key max8192/no control characters. Node worker receives configuration by anonymous stdin and no model/cloud/GitHub credentials in its environment. Model/tool child Bash gets a separate minimal environment and private HOME; same-user OS access remains. Private native HOME/cache/settings/model-catalog/temporary workspace mirrors are removed after every call. Literal and JSON-escaped configured keys/bases/tokens are redacted from returned strings. Original QM native Pi builtins are disabled in favor of its original QM tools; no extensions/skills/context files or session children are loaded. Only execute/files read/write approval identities are enabled; no delegation, Slack/email delivery or control service. Caller project/artifacts persist until caller removes them or kills the outer sandbox.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx download "$SANDBOX_ID" /home/user/app/hello.py ./hello.py
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB, Linux x64, command port 9000. Runtime needs no nested Docker, KVM, GPU or root capabilities. The image build enforces an 8 GiB rootfs limit. The local SDK service must be reachable; project files and artifacts last for the outer sandbox lifetime. Model execution additionally needs the configured external service and egress.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/qm.md).

## Issues

Track [Issue44](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/44). Template/native adapter issues belong here; Python server/client to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), Node HTTP client to [nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues), CLI to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized versions/scope, never keys/private endpoints/raw prompts or reasoning.

## License

Authored wrapper/backend Apache-2.0; original QM MIT, original Node and SDK retain their licenses/notices. [Original distribution notice](UPSTREAM-NOTICE.md), [QM license](UPSTREAM-QM-LICENSE). Complete original notices stay installed; no third-party relicensing.
