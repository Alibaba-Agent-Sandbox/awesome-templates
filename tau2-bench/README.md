# Tau2 retail benchmark

[中文](README.zh-CN.md).

## What it does

Runs the original Tau2 v1.0.1 text retail agent and user simulator, returns the
native reward and a sanitized trajectory, then independently replays that
trajectory through the original evaluator without a model key. This is a retail
slice: other domains, voice, knowledge tasks and tasks requiring a natural-language
judge are refused. A single task score does not measure the full benchmark.

## Stack

Original MIT-licensed [source at the pinned revision](https://github.com/sierra-research/tau2-bench/tree/fc0055dc4e0a316c3f83133267fbd6faaa770992),
Python 3.13, isolated hash-locked dependencies, LiteLLM1.81.11, and Agent Sandbox
server. [Dockerfile](Dockerfile), [requirements.lock](requirements.lock),
[upstream.json](upstream.json), [design](../docs/design/tau2-bench.md).
The official source archive is 92,081,935 bytes with controller-measured SHA256
`7a227036d07fdeb088dbd0c99fdb40ee9b9e0ebc06aadbc4dec1217b3383e57e`.
The authoritative digest is in `upstream.json`; this is a measured archive digest,
not an upstream-published checksum. Source execution uses fixed
`PYTHONPATH=/opt/tau2/src`; it does not assert publication of a PyPI Tau2 package.

## Problem solved

Provides bounded, reproducible access to an original benchmark task and its native
evaluation, with a separately downloadable trajectory and independent strict
replay. Both agent and simulated user use the explicitly configured model service.

## Quick start (CLI)

Install the verified native CLI and configure your own Express provider using the
[steps guide](../docs/platform-steps.md). Replace the placeholders below with this
run's unique output directory and owned resource IDs. Publish the source commit
before preparing immutable COPY steps. Steps do not prove a Docker image build.

```bash
python scripts/prepare_steps.py tau2-bench --asset-transport oss --output /tmp/tau2-steps-<unique-run> --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/tau2-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> tau2_version
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Named commands use `abx run`; `--native` selects the verified native CLI backend.
The version response must report native version `1.0.1`, domain `retail` and
`task_count: 114`. The canonical non-model deploy/SDK-create/HTTP/cleanup runner is:

```bash
ABX='abx --native' python scripts/run_steps_e2e.py tau2-bench --sandbox-create sdk --http --asset-transport oss
```

Require official READY and independently verify absence of every owned sandbox,
template and private asset object after use. Preserve private recovery journals
when cleanup is uncertain. Configure the model only through the process
environment described below; do not put keys in CLI arguments.

## Quick start (Python SDK)

Install the paired `agent-sandbox-client` using the
[pinned client guide](../docs/python-client-installation.md). The placeholder
template must belong to you. These examples are source-checked, pending cloud
qualification. `tau2_run` requires a server started with the three model settings.

```python
from agent_sandbox.api.sandbox import Sandbox

async def example():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=1200)
    try:
        print(await sb.run("tau2_version", timeout=90))
        # After starting the server with the explicit model environment:
        # result = await sb.run("tau2_run", domain="retail", task_id="0",
        #     max_steps=30, command_timeout=600, timeout=660)
        # trajectory = await sb.files.read_bytes(
        #     result["artifact_path"], max_bytes=8 * 1024 * 1024)
        # print(await sb.run("tau2_verify_artifact",
        #     path=result["artifact_path"], task_id="0", timeout=150))
    finally:
        await sb.kill()
```

A create-time environment does not reconfigure a prewarmed server; follow
[runtime environment](../docs/runtime-environment.md) and inspect
`tau2_setup_check` before model execution.

## Quick start (HTTP POST)

Use your own server URL and its Bearer token in environment variables. Never
publish them. Direct JSON arguments go to the named route, without an `args` wrapper.

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/tau2_version" -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' -d '{}'
```

The JSON envelope is `{"result":{"native_version":"1.0.1","domain":"retail","task_count":114}}`. For `tau2_run`, POST
`{"domain":"retail","task_id":"0","max_steps":30,"command_timeout":600}`;
for `tau2_verify_artifact`, POST `{"path":"<returned-artifact-path>","task_id":"0"}`.
Schema/type/missing/unknown argument errors use HTTP400, authentication HTTP401,
unknown commands HTTP404, and semantic/native execution failures HTTP500. Commands
are buffered. Set client HTTP timeout beyond the execution deadline; disconnecting
the client does not cancel the server operation.

## Command reference

| Command | Parameters | Result and side effects |
| --- | --- | --- |
| `tau2_version` | None | Native source version/revision, retail domain and original task count; no model call. |
| `tau2_setup_check` | None | Configuration-presence booleans and `native-retail-agent-and-user` mode; no secret values or model call. |
| `tau2_run` | `domain: str="retail"` (only retail); `task_id: str="0"` (1–3 decimal digits, must exist); `max_steps: int=30` (5–60, no bool); `command_timeout: int=600` seconds (30–900, no bool) | Native reward, termination/message/tool counts, source revision, artifact path/bytes/SHA256. Calls both models and writes one private owned result directory. Rejects tasks with nonempty NL assertions before model calls. |
| `tau2_verify_artifact` | Required `path: str` (at most 4096 UTF-8 bytes, existing regular trajectory inside workspace, 1–8MiB); `task_id: str="0"` | Keyless native strict replay, matched reward and artifact SHA256; no artifact mutation. Deadline120 seconds. |

Version deadline is60 seconds. Inputs travel through anonymous stdin, output is
bounded to256KiB per stream. All native processes use a serialized owned process
group, nonce and pidfd cleanup. Deadline, nonzero exit, incomplete trajectory,
invalid source/task, reward mismatch or malformed output fails the command.

## Configuration

| Variable | Required/default | Meaning |
| --- | --- | --- |
| `TAU2_MODEL_API_KEY` | Required for run; empty | Model key, at most8192 bytes, no CR/LF/NUL. |
| `TAU2_MODEL_BASE_URL` | Required for run; empty | Explicit HTTPS compatible base URL, at most2048 characters; literal local HTTP permitted for synthetic fixtures. No userinfo, query or fragment. |
| `TAU2_MODEL` | Required for run; empty | Explicit model identifier, at most200 allowed identifier characters. |
| `WORKSPACE` | `/home/user/workspace` | Existing writable result root. |
| `ABX_SERVER_TOKEN` | Empty | Set a token for the exposed server. |

Settings are captured at server import. Both native participants receive the same
explicit `openai/` model and `api_base`; the key is supplied only to the private
worker environment from anonymous stdin. No credential is written into argv or
configuration. Operator cloud/GitHub keys and binary overrides are excluded.
Private HOME, temporary native logs and descendants are removed on every path;
successful trajectories remain caller-owned. Exact key and endpoint strings are
recursively scrubbed from trajectory keys and values. Replay has no model key.
Telemetry and model-price network refresh are disabled; unknown native price
metadata returning zero is not a billing estimate or proof of free execution.

## Resources

2 vCPU,2048MiB RAM, port9000, non-root `user`; no Docker daemon, KVM, GPU or extra
capabilities. Rootfs budget is about10GiB; build refuses a rootfs above8GiB. The
92MB archive contributes about38MB selected source/retail data plus dependencies.
Both agent and user incur model calls; steps are bounded5–60, each model request
has a60-second timeout, and the command deadline is30–900 seconds. A successful
trajectory of at most8MiB remains in its exclusive `abx_tau2_result_<nonce>`
directory; remove only that directory after reading it. Failed partial results
are deleted. Kill and independently confirm absence of your outer cloud resources.

## Verified

Experimental; `tested_on: []`. Image, Express steps, SDK/native model execution,
independent strict replay and owned cloud cleanup are **PENDING**. Local fixtures
cannot establish those passes. Examples are source-checked only. New runs must
preserve failures/skips and publish exact-source sanitized receipts before adding
provider claims.

## Secondary development

Run `python -m pytest -q tau2-bench/test_runtime.py`,
`python scripts/check_template.py tau2-bench`, and `python scripts/check_docs.py`.
The external `e2e_test.py` checks discovery, version, configuration and invalid
inputs. Set `E2E_REQUIRE_CLI=1` to require real native execution. Real model checks
require `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1` against a fresh cloud
server: original retail task0 must complete with reward1.0, actual agent/user/tool
messages, independently downloaded bytes/SHA, separate original strict replay,
fresh post-return acknowledgement and owned artifact cleanup. Generated/runtime
code executes only inside the cloud sandbox. Do not infer full-benchmark accuracy.
Dependency, source, data or task changes require fresh image and cloud receipts.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), the
[project standard](../docs/project-standards.md) and
[documentation standard](../docs/documentation-standards.md). Preserve the frozen
upstream lock and both licenses. Update translations, design, manifest and catalog
together; record real versus synthetic checks and owned cleanup separately.

## Issues

[Template request59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59).
Template defects: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper: [Apache-2.0](../LICENSE). Original Tau2 source and selected retail data:
retained [MIT notice](UPSTREAM-LICENSE.md). Preserve upstream notices when distributing.
