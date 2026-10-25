# Tau2 retail benchmark

[中文](README.zh-CN.md).

## What it does

Runs the original Tau2 v1.0.1 text retail agent and user simulator, returns the
native reward and a sanitized trajectory, then independently replays that
trajectory through the original evaluator without a model key. This is a retail
slice: other domains, voice, knowledge tasks and tasks requiring a natural-language
judge are refused. A single task score does not measure the full benchmark.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

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
all completion, source, score and strict replay acceptance gates remain required.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./tau2-bench --yes
abx run <sandbox-id> tau2_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('tau2_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/tau2_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"native_version": "1.0.1", "domain": "retail", "task_count": 114}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

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
Python3.13 compatibility dependency: [audioop-lts PSF-2.0](AUDIOOP-LICENSE.txt).
