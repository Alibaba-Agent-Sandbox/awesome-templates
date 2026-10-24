# appworld

[中文](README.zh-CN.md)

## What it does

Run original AppWorld0.1.3.post1 training worlds, APIs, SQLite state and native evaluator with an authored compatible-model API bridge. The bridge offers original API documentation and actual API calls; the historical paper agent baseline is not claimed. Result artifacts retain the upstream encrypted bundle format. This is a single-training-task slice, not a leaderboard score.

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13, isolated [full Python hash lock](requirements.lock), original appworld0.1.3.post1 wheel and original34,280,074-byte encrypted dataset. Servere2cb27e24fde0a67112f82b8d44af463445a5d1a, user runtime/port9000. [Dockerfile](Dockerfile), [immutable provenance](upstream.json), [design](../docs/design/appworld.md). Protected app source/data stay encrypted in distributable images.



Python3.13 compatibility: original SQLAlchemy1.4.54 has no matching wheel. Its unchanged SHA256-pinned source uses upstream DISABLE_SQLALCHEMY_CEXT=1 for pure Python; pinned setuptools80.9.0/wheel0.45.1 are installed from a separate hash lock before --no-build-isolation. All native/runtime requirements remain hash-pinned; SQLAlchemy2 is not substituted.

## Problem solved

Evaluate genuine AppWorld tasks on a disposable sandbox without nested Docker or an operator-installed benchmark. The [pinned upstream](https://github.com/StonyBrookNLP/appworld/tree/66ad8099e12188ece0d3fe45e661dbc01880813b) supports direct Python execution; Docker is optional. The wrapper retains original AppWorld execution safety defaults and uses the original evaluator rather than a fabricated score.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./appworld --workflow application --yes
abx run <sandbox-id> appworld_native_smoke --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('appworld_native_smoke'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/appworld_native_smoke`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "original AppWorld0.1.3.post1 native API and private cleanup OK"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

| Name | Requirement / default | Meaning |
| --- | --- | --- |
| APPWORLD_MODEL_API_KEY | model required; empty | Approved compatible endpoint key, anonymous stdin to native worker, never argv or child environment |
| APPWORLD_MODEL_BASE_URL | model required; empty | Explicit HTTPS base; literal loopback HTTP only for authored fixtures; no userinfo/query/fragment, max2048characters |
| APPWORLD_MODEL | model required; empty | Actual model identifier,1..200 safe characters |
| WORKSPACE | /home/user/workspace | Existing result root, captured at module startup |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

Configuration is captured at command-server startup. Key max8192characters/noCRLF/NUL. Worker environment excludes operator cloud/GitHub/model tokens; model settings travel via anonymous stdin into private memory. Original model execution guards remain enabled. Bridge validates allowed original app/API identifiers and renders JSON arguments as Python literals; it does not accept executable model Python. At most16tool calls execute per response;17..64calls receive complete rejection feedback without API execution and larger batches fail. At most3empty-choice responses across a task,8192response tokens,160native interactions,50API calls/interaction,30seconds/native execution,60seconds/model HTTP without SDK retries. Native inspect/API tool output is bounded; model context at most1MiB.

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000 and enforced image rootfs8GiB budget. No Docker/KVM/GPU. Private runtime copies and unpacks original protected code/data per call; no plaintext protected app/data is exported in the distributable image. Actual image/native dependencies and one original Express task pass below; workload peak memory remains unmeasured. Model calling requires authorized compatible Chat Completions/tool calling and network egress; no other provider or all-task qualification.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Keep original wheel/encrypted bundle/data hashes, runtime version, manifest and native evaluator consistent. Public source tag66ad8099e12188ece0d3fe45e661dbc01880813b is version correspondence, not proof of reproducible wheel construction. Training-only scope avoids held-out benchmark contamination. Every new model/task/profile requires real native evaluation. Preserve original protected licenses and encrypted distribution; result bundles use the original format and public upstream decryption mechanism, so they are not a confidentiality guarantee.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [design](../docs/design/appworld.md). Preserve immutable pass/fail receipts and independently confirmed owned cleanup.

## Issues

Tracked by [Issue70](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70). Template/controller issues belong here; client/server issues to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI issues to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Authored wrapper and original public AppWorld source: Apache-2.0. Protected AppWorld app/task/API/data portions and derivatives additionally require encrypted public redistribution. See [UPSTREAM-NOTICE](UPSTREAM-NOTICE.md) and the original bundled licenses. Never publish decrypted protected source, databases, task details or trajectories. No upstream baseline/leaderboard result is implied.
