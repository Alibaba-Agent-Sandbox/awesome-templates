# appworld

[中文](README.zh-CN.md)

## What it does

Run original AppWorld0.1.3.post1 training worlds, APIs, SQLite state and native evaluator with an authored compatible-model API bridge. The bridge offers original API documentation and actual API calls; the historical paper agent baseline is not claimed. Result artifacts retain the upstream encrypted bundle format. This is a single-training-task slice, not a leaderboard score.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13, isolated [full Python hash lock](requirements.lock), original appworld0.1.3.post1 wheel and original34,280,074-byte encrypted dataset. Published server package, user runtime/port9000. [Dockerfile](Dockerfile), [immutable provenance](upstream.json), [design](../docs/design/appworld.md). Protected app source/data stay encrypted in distributable images.



Python3.13 compatibility: original SQLAlchemy1.4.54 has no matching wheel. Its unchanged SHA256-pinned source uses upstream DISABLE_SQLALCHEMY_CEXT=1 for pure Python; pinned setuptools80.9.0/wheel0.45.1 are installed from a separate hash lock before --no-build-isolation. All native/runtime requirements remain hash-pinned; SQLAlchemy2 is not substituted.

## Problem solved

Evaluate genuine AppWorld tasks on a disposable sandbox without nested Docker or an operator-installed benchmark. The [pinned upstream](https://github.com/StonyBrookNLP/appworld/tree/66ad8099e12188ece0d3fe45e661dbc01880813b) supports direct Python execution; Docker is optional. The wrapper retains original AppWorld execution safety defaults and uses the original evaluator rather than a fabricated score.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export APPWORLD_MODEL_API_KEY='<your-model-api-key>'
export APPWORLD_MODEL_BASE_URL='https://model.example.invalid/v1'
export APPWORLD_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=750
abx template launch Alibaba-Agent-Sandbox/awesome-templates//appworld --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" appworld_run --json-args '{"max_steps":30,"command_timeout":600}'
```

Returns the selected training task, native `score`, `success` and encrypted `artifact_path`; a model is not guaranteed to solve a task.

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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=750
        )
        try:
            result = await client.commands.run('appworld_run', max_steps=30, command_timeout=600)
            print(result)
            Path('appworld-result.zip').write_bytes(await sb.files.read_bytes(result['artifact_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/appworld_run`

```json
{
  "max_steps": 30,
  "command_timeout": 600
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 750 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters / bounds | Result / effects |
| --- | --- | --- |
| appworld_version | none | native_version0.1.3.post1, source_commit, data_sha256, protected_bundles_encrypted:true; actual fixed package/data hashes, no unpack/model |
| appworld_setup_check | none | mode, base_url_set/api_key_set/model_set booleans; no network/setup |
| appworld_native_smoke | none | Exact smoke string after original training-world initialization/native API and owned private-process cleanup; no model |
| appworld_run | task:string default empty, max64 safe identifier characters; empty selects first original train task; max_steps:int1..40 default30; command_timeout:int30..900seconds default600; booleans rejected | score0.0/1.0 (all native tests), success, num_tests/pass_count, task, original native/source/data identity, model/model_steps, bridge_api_calls/native_api_calls, task_completed, artifact_path/log_path aliases, artifact_bytes/artifact_sha256/artifact_encrypted, training_task_count; owns one new result directory |
| appworld_verify_artifact | path:required workspace-contained existing encrypted file, max4096UTF8 bytes,1..64MiB; task:string default empty uses bound artifact task, otherwise original train task ID | verified:true, task, original_evaluator:true, model_credentials_used:false, score/success/num_tests/pass_count; independent original evaluator on reloaded saved databases, no model call |

Native operations serialize and reject overlap. Requests at most32KiB; native stdout/stderr256KiB per stream. Whole process group/nonce/pidfd cleanup and private HOME/package/data/cache removal run on success/failure/timeout/overflow. Results are buffered. Successful encrypted artifacts persist in an exclusive0700 workspace directory with0600 file; caller or sandbox deletion removes them. Failed partial result directories are removed. Verify bounds the encrypted artifact64MiB,4096ZIP members and512MiB expanded; paths/symlinks/outside-experiment members are rejected.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. The model and endpoint must support Chat Completions tool calls.

| Name | Requirement / default | Meaning |
| --- | --- | --- |
| APPWORLD_MODEL_API_KEY | model required; empty | Approved compatible endpoint key, anonymous stdin to native worker, never argv or child environment |
| APPWORLD_MODEL_BASE_URL | model required; empty | Explicit HTTPS base; literal loopback HTTP only for authored fixtures; no userinfo/query/fragment, max2048characters |
| APPWORLD_MODEL | model required; empty | Actual model identifier,1..200 safe characters |
| WORKSPACE | /home/user/workspace | Existing result root, captured at module startup |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Configuration is captured at command-server startup. Key max8192characters/noCRLF/NUL. Worker environment excludes operator cloud/GitHub/model tokens; model settings travel via anonymous stdin into private memory. Original model execution guards remain enabled. Bridge validates allowed original app/API identifiers and renders JSON arguments as Python literals; it does not accept executable model Python. At most16tool calls execute per response;17..64calls receive complete rejection feedback without API execution and larger batches fail. At most3empty-choice responses across a task,8192response tokens,160native interactions,50API calls/interaction,30seconds/native execution,60seconds/model HTTP without SDK retries. Native inspect/API tool output is bounded; model context at most1MiB.

The working directory is `/home/user/workspace`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with artifact_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./appworld-result.zip
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB, Linux x64, port 9000. No Docker, KVM or GPU required. Each call initializes a private runtime; model tasks require the external compatible model service and egress. Training-task slice only; no full benchmark leaderboard result is implied.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/appworld.md).

## Issues

Tracked by [Issue70](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70). Template/controller issues belong here; client/server issues to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI issues to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Authored wrapper and original public AppWorld source: Apache-2.0. Protected AppWorld app/task/API/data portions and derivatives additionally require encrypted public redistribution. See [UPSTREAM-NOTICE](UPSTREAM-NOTICE.md) and the original bundled licenses. Never publish decrypted protected source, databases, task details or trajectories. No upstream baseline/leaderboard result is implied.
