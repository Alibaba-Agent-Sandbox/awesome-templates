# Tau2 retail benchmark

[中文](README.zh-CN.md)

## What it does

Runs the original Tau2 v1.0.1 text retail agent and user simulator, returns the
native reward and a sanitized trajectory, then independently replays that
trajectory through the original evaluator without a model key. This is a retail
slice: other domains, voice, knowledge tasks and tasks requiring a natural-language
judge are refused. A single task score does not measure the full benchmark.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Original MIT-licensed [source at the pinned revision](https://github.com/sierra-research/tau2-bench/tree/fc0055dc4e0a316c3f83133267fbd6faaa770992),
Python 3.13, isolated hash-locked dependencies, LiteLLM1.81.11, and Agent Sandbox
server. [Dockerfile](Dockerfile), [requirements.lock](requirements.lock),
[upstream.json](upstream.json), [design](../docs/design/tau2-bench.md).
The official source archive is 92,081,935 bytes with controller-measured SHA256
`7a227036d07fdeb088dbd0c99fdb40ee9b9e0ebc06aadbc4dec1217b3383e57e`.
The authoritative digest is in `upstream.json`; this is a measured archive digest,
not an upstream-published checksum. Source execution uses fixed
`PYTHONPATH=/opt/tau2/src`; it does not assert publication of a PyPI Tau2 package.
The unchanged [frozen export](requirements.upstream.lock) retains platform markers;
`python tau2-bench/select_lock.py` selects its Linux CPython3.13 entries without
changing package versions or hashes. The image enforces this Python profile.
An explicit [compatibility lock](requirements.compat.lock) additionally pins
PSF-2.0 `audioop-lts==0.2.2`: Python3.13 removed `audioop`, which this original
upstream imports even for text tasks. Its [license](AUDIOOP-LICENSE.txt) is retained.
Selected data includes the original shared user-simulator guidelines as well as
the retail domain; no replacement instructions are supplied.

## Problem solved

`tau2_run(domain)` returns `score` and `log_path` as requested; `artifact_path`
is the same owned sanitized trajectory path, with byte count and SHA256.
Provides bounded, reproducible access to an original benchmark task and its native
evaluation, with a separately downloadable trajectory and independent strict
replay. Both agent and simulated user use the explicitly configured model service.
Text communication uses the original native default `enforce_communication_protocol=False`;
task completion and native replay are reported separately.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export TAU2_MODEL_API_KEY='<your-model-api-key>'
export TAU2_MODEL_BASE_URL='https://model.example.invalid/v1'
export TAU2_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=750
abx template launch Alibaba-Agent-Sandbox/awesome-templates//tau2-bench --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" tau2_run --json-args '{"domain":"retail","task_id":"0","max_steps":30,"command_timeout":600}'
```

Returns native `score`, termination reason and sanitized trajectory `artifact_path`. Both the agent and simulated user make billable model calls; reward 1 is not guaranteed.

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
            result = await client.commands.run('tau2_run', domain='retail', task_id='0', max_steps=30, command_timeout=600)
            print(result)
            Path('tau2-trajectory.json').write_bytes(await sb.files.read_bytes(result['artifact_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/tau2_run`

```json
{
  "domain": "retail",
  "task_id": "0",
  "max_steps": 30,
  "command_timeout": 600
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 750 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result and side effects |
| --- | --- | --- |
| `tau2_version` | None | Native source version/revision, retail domain and original task count; no model call. |
| `tau2_setup_check` | None | Configuration-presence booleans and `native-retail-agent-and-user` mode; no secret values or model call. |
| `tau2_run` | `domain: str="retail"` (only retail); `task_id: str="0"` (1–3 decimal digits, must exist); `max_steps: int=30` (5–60, no bool); `command_timeout: int=600` seconds (30–900, no bool) | Native `score`, `log_path`/`artifact_path` aliases, termination/message/tool counts, source revision, artifact bytes/SHA256. Calls both models and writes one private owned result directory. Rejects tasks with nonempty NL assertions before model calls. |
| `tau2_verify_artifact` | Required `path: str` (at most 4096 UTF-8 bytes, existing regular trajectory inside workspace, 1–8MiB); `task_id: str="0"` | Keyless native strict replay, matched reward and artifact SHA256; no artifact mutation. Deadline120 seconds. |

Version deadline is60 seconds. Inputs travel through anonymous stdin, output is
bounded to256KiB per stream. All native processes use a serialized owned process
group, nonce and pidfd cleanup. Deadline, nonzero exit, incomplete trajectory,
invalid source/task, reward mismatch or malformed output fails the command.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. The agent and user simulator share these settings; the endpoint must support tool calls.

| Variable | Required/default | Meaning |
| --- | --- | --- |
| `TAU2_MODEL_API_KEY` | Required for run; empty | Model key, at most8192 characters, no CR/LF/NUL. |
| `TAU2_MODEL_BASE_URL` | Required for run; empty | Explicit HTTPS compatible base URL, at most2048 characters; literal local HTTP permitted for synthetic fixtures. No userinfo, query or fragment. |
| `TAU2_MODEL` | Required for run; empty | Explicit model identifier, at most200 allowed identifier characters. |
| `WORKSPACE` | `/home/user/workspace` | Existing writable result root. |
| `ABX_SERVER_TOKEN` | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Settings are captured at server import. Both native participants receive the same
explicit `openai/` model and `api_base`; the key is supplied only to the private
worker environment from anonymous stdin. No credential is written into argv or
configuration. Operator cloud/GitHub keys and binary overrides are excluded.
Private HOME, temporary native logs and descendants are removed on every path;
successful trajectories remain caller-owned. Exact key and endpoint strings are
recursively scrubbed from trajectory keys and values. Replay has no model key.
Telemetry and model-price network refresh are disabled; unknown native price
metadata returning zero is not a billing estimate or proof of free execution.

The working directory is `/home/user/workspace`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with artifact_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./tau2-trajectory.json
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU,2048MiB RAM, port9000, non-root `user`; no Docker daemon, KVM, GPU or extra
capabilities. Rootfs budget is about10GiB; build refuses a rootfs above8GiB. The
92MB archive contributes about38MB selected source/retail data plus dependencies.
Both agent and user incur model calls; steps are bounded5–60, each model request
has a60-second timeout, and the command deadline is30–900 seconds. A successful
trajectory of at most8MiB remains in its exclusive `abx_tau2_result_<nonce>`
directory; remove only that directory after reading it. Failed partial results
are deleted. Kill and independently confirm absence of your outer cloud resources.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/tau2-bench.md).

## Issues

[Template request59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59).
Template defects: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper: [Apache-2.0](../LICENSE). Original Tau2 source and selected retail data:
retained [MIT notice](UPSTREAM-LICENSE.md). Preserve upstream notices when distributing.
Python3.13 compatibility dependency: [audioop-lts PSF-2.0](AUDIOOP-LICENSE.txt).
