# SWE local evaluation slice

[中文](README.zh-CN.md)

## What it does

Runs official `mini-swe-agent==2.4.6` against the genuine SWE-bench Verified instance `pallets__flask-5014`. Prepares the pinned Flask base plus original benchmark tests, reproduces 1 failure and 59 passes, lets an explicitly authorized agent edit source, and evaluates its patch in a fresh checkout and venv. Retrieves a source patch and a JSON report.

This single-instance portability slice does not run the official Docker harness, reproduce its complete original dependency/system environment, or produce a SWE-bench score. Evaluation now pins the instance’s original Python 3.11.10; the dependencies and Debian base below remain a separately tested environment. SWE-agent, SWE-rebench, arbitrary dataset instances and batch benchmarks are outside this slice.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba base `v0.0.49` (resolved by the builder), Python 3.13 server/agent, independent official-SHA Python 3.11.10 evaluation runtime, existing Node.js 20, mini-swe-agent 2.4.6, LiteLLM 1.82.6, pytest 8.3.5. Published server package. See [Dockerfile](./Dockerfile) for all pins. No nested Docker, system installs at runtime or full dataset download.

## Problem solved

Separates an actual source repair from an agent saying it finished. The evaluator reconstructs the original snapshot and test patch, imports only the supported `src/flask/blueprints.py` diff, and requires exactly all 60 declared test identities. Editing agent-side tests or printing a marker cannot supply a passing report. `resolved_slice` is a result for this environment, never an official benchmark score.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

Fill in model settings before launch: the API key, endpoint and model ID must belong to the same model service and region. `https://model.example.invalid/v1` is a placeholder; replace it with your vendor API base, not a web chat URL. Use a model ID actually available at that endpoint.

This entry uses a model API key: no browser OAuth login is required, and your local logged-in account is not imported. See Configuration for protocol requirements. This template uses **Chat Completions**; an “OpenAI-compatible” label alone does not establish support for that API.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SWE_API_KEY='<your-model-api-key>'
export SWE_BASE_URL='https://model.example.invalid/v1'
export SWE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=1200
abx template launch Alibaba-Agent-Sandbox/awesome-templates//swe --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" swe_prepare --json-args '{}'
```

Returns a `run_id` and the failing baseline for `pallets__flask-5014`; keep the run ID for the coding and evaluation calls below.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

Copy the prepared `run_id` into `RUN_ID`. Use `allow_execution:true` only when authorizing model-generated shell execution. The following runs the repair, evaluates a fresh copy, exports the report/patch and removes that run. Inspect actual test outcomes; HTTP 200 is not a guarantee of a successful repair.

```bash
export RUN_ID='paste-run-id'
abx run "$SANDBOX_ID" swe_run_agent --json-args "{\"run_id\":\"$RUN_ID\",\"allow_execution\":true,\"max_steps\":30,\"command_timeout\":600}"
abx run "$SANDBOX_ID" swe_evaluate --arg run_id="$RUN_ID"
abx run "$SANDBOX_ID" swe_report --arg run_id="$RUN_ID"
# Download returned report and patch paths before cleanup
abx download "$SANDBOX_ID" '<returned-report-path>' ./report.json
abx download "$SANDBOX_ID" '<returned-patch-path>' ./repair.patch
abx run "$SANDBOX_ID" swe_cleanup --arg run_id="$RUN_ID"
```

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

This is the complete SDK version of the CLI repair flow. Launch the instance, set `SANDBOX_ID`, save as `use_template.py` and run `python3 use_template.py`. `allow_execution=True` explicitly authorizes model-generated shell execution. It saves the report and patch locally, removes the owned run and closes connections. Delete the outer sandbox afterward as described below.

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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=1200
        )
        try:
            prepared = await client.commands.run("swe_prepare")
            print(prepared)
            run_id = prepared["run_id"]
            try:
                print(await client.commands.run("swe_run_agent", run_id=run_id,
                    allow_execution=True, max_steps=30, command_timeout=600))
                report = await client.commands.run("swe_evaluate", run_id=run_id)
                print(report)
                Path("report.json").write_bytes(
                    await sb.files.read_bytes(report["report_path"]))
                Path("repair.patch").write_bytes(
                    await sb.files.read_bytes(report["patch_path"]))
            finally:
                await client.commands.run("swe_cleanup", run_id=run_id)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/swe_prepare`

```json
{}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 1200 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

Then request in order:

- `POST /commands/swe_run_agent`: `{"run_id":"<returned-run-id>","allow_execution":true,"max_steps":30,"command_timeout":600}`
- `POST /commands/swe_evaluate`: `{"run_id":"<returned-run-id>"}`
- `POST /commands/swe_report`: `{"run_id":"<returned-run-id>"}`
- `POST /commands/swe_cleanup`: `{"run_id":"<returned-run-id>"}`

## Command reference

| Command | Parameters | Result / execution |
|---|---|---|
| `swe_version` | none | Actual `mini --help` and installed distribution version; no key |
| `swe_setup_check` | none | Boolean runtime/key/base/model availability, no secret values |
| `swe_prepare` | `instance_id: str = "pallets__flask-5014"` | Opaque `run_id`, independently reproduced baseline; other instances rejected |
| `swe_run_agent` | `run_id: str` required; `allow_execution: bool = false`; `max_steps: int = 12` (1–30); `command_timeout: int = 300` (30–900) | Actual `mini -c <installed default.yaml or mini.yaml> -c <private config.yaml> -o <private trajectory>`; requires explicit shell permission; returns model-call count and Submitted status |
| `swe_evaluate` | `run_id: str` required | Fresh base + original tests + supported source diff; exact test states, counts, `resolved_slice`, `official_benchmark_score: false`, patch/report artifact paths |
| `swe_report` | `run_id: str` required | Last evaluation and artifact paths; refuses before evaluation |
| `swe_cleanup` | `run_id: str` required | Deletes only that owned run; returns true |

Malformed types/unknown arguments return HTTP 400. Invalid instance/run ID, missing explicit permission/settings, upstream failure, missing test identities or deadlines return HTTP 500 with sanitized errors. A failed test is a real report with `resolved_slice: false`; collection errors produce no score. Same-run operations use an exclusive lock and refuse conflicts. Operations are synchronous; an HTTP client disconnect is not a cancellation API. Set the command deadline or destroy the owned sandbox to stop work.

## Configuration

This entry calls compatible Chat Completions. Include the vendor API prefix (often `/v1`) in the base; do not append `/chat/completions`. The default text protocol requires upstream-formatted bash actions and submission; it does not automatically switch to native tool calls.

| Variable | Requirement / default | Meaning |
| --- | --- | --- |
| `SWE_API_KEY` | Required for model execution | Your compatible model-service API key. |
| `SWE_BASE_URL` | Required for model execution | Chat Completions API base, for example your vendor HTTPS `/v1` endpoint. |
| `SWE_MODEL` | Required for model execution | Bare model ID at that endpoint; wrapper supplies the LiteLLM `openai/` prefix. |
| `SWE_MODEL_PROTOCOL` | `text` in the shipped manifest | `toolcall` uses upstream native bash function calls; endpoint/model must support tools. `text` uses the upstream text protocol. |
| `ABX_SERVER_TOKEN` | Required | Independent application token. |

`SWE_MODEL_PROTOCOL` is nonempty `text` in the shipped manifest. When launching this template directly, a host `export SWE_MODEL_PROTOCOL=toolcall` does not override it. To use the native tool protocol, make your own template copy and change that field explicitly before following the [local-source guide](../docs/using-templates.md). The model key, base and model fields are empty and accept the exports shown above.

Model-generated shell commands have sandbox-user filesystem and network authority. Use a disposable sandbox and trusted tasks. The agent is limited to the bundled Flask instance; the evaluation slice is not the full official Docker benchmark. Export model settings before launch; a later local export does not reconfigure the running application.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB, command port 9000. One pinned Flask instance, with separate agent and Python 3.11.10 evaluation environments. Each run and independent evaluation copies its environment; files occupy disk until `swe_cleanup` or sandbox deletion.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/swe.md).

## Issues

[Template Issue #35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35) owns this partial implementation and remaining official/full deployment gates. SDK/server problems belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI problems in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper Apache-2.0. mini-swe-agent 2.4.6 is MIT; Flask is BSD-3-Clause. SWE-bench Verified metadata/test patch follows the dataset's MIT license. Bundled CPython retains its distribution license files. Provenance and upstream license links are in [NOTICE](./NOTICE.md); upstream source archives retain their own license files.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
