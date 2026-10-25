# qm

## What it does

Run unchanged original QM0.1.0 exported Pi harness and original tool context on one owned Express computer, using an authored backend built on the real Agent Sandbox Node.js HTTP SDK. Coding uses an explicitly approved compatible model. Original full multiplayer core/web/Slack/Postgres durability/cron/subscription features are not started or qualified. Original default Docker backend is not used. This is a bounded original-library integration, not a shell program named qm or a replacement agent. [Original source](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13. SHA256-pinned original Node24.16.0 archive/executable, full original QM source0.1.0/immutable commit and original npm integrity lock. Original Node SDK0.1.0 source90b5187dca84fca78d75d3045896482540641c72 built with its original lock/build script; npm0.1.0 returned404 on2026-10-21, so no npm release is assumed. Server34e7e011c5569f77b7f605e65313be7498f6cf02. [Dockerfile](Dockerfile), [provenance](upstream.json), [QM lock](package-lock.json), [SDK lock](sdk-package-lock.json), [design](../docs/design/qm.md).

## Problem solved

Run genuine exported original QM functionality with actual SDK-backed tools without nested Docker or cloud credentials in model tools. Native package/source/import checks, SDK round trips and actual model file/task acceptance are separate gates. The Node SDK is an in-sandbox HTTP client; outer creation/kill belongs to the caller's Python Sandbox SDK. One caller project per backend; attach/provision does not create another cloud VM.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./qm --yes
abx run <sandbox-id> qm_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('qm_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/qm_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"qm_version": "0.1.0", "node_version": "24.16.0", "sdk_version": "0.1.0"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000, enforced8GiB image rootfs budget. No Docker/KVM/GPU/root capabilities. Actual native dependencies and the bounded Express profile pass below; peak memory was not measured and declared memory is not a workload estimate. Package/source download and SDK endpoint access are needed; coding additionally requires approved model tool calling/egress. No other provider or full multiplayer durability is claimed.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q qm-sandbox/test_runtime.py qm-sandbox/test_commands.py
python -m pytest -q qm/test_terminal.py
python scripts/check_template.py qm --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py qm --sandbox-create sdk --http --asset-transport oss
```

For original SDK HTTP fixtures, run `python qm-sandbox/prepare_sdk_tests.py /tmp/qm-sdk-tests-<unique-run>`, then `ABX_QM_TEST_SDK_ENTRY=/tmp/qm-sdk-tests-<unique-run>/dist/index.js node --test qm-sandbox/test_adapter.mjs`. Node>=20 suffices for SDK-only unit fixtures; actual original QM requires the pinned Node24.16.0 profile. Without that explicit original SDK build, these HTTP fixture tests are skipped, never a native/backend pass.

Original sources/locks/notices remain authoritative. Native workers execute only on a newly owned disposable target for actual acceptance; source-only checks explicitly skip missing native runtime and never opt in to a model. The coding controller requires positive original model/tool and completed SDK counts, preserved original tests, changed source, new report/exact nonce, complete original3plus4held-out post-return cases and fresh ACK. A marker/configuration/version alone is insufficient. Backend acceptance separately checks original tool context/real SDK file/execution and independent target bytes/absence.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), project/documentation standards and source-bound evidence rules. Keep both README languages, design, catalog, API, immutable pins and indexed engineering records consistent. Preserve every failure and independently verified resource recovery.

## Issues

Track [Issue44](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/44). Template/native adapter issues belong here; Python server/client to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), Node HTTP client to [nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues), CLI to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized versions/scope, never keys/private endpoints/raw prompts or reasoning.

## License

Authored wrapper/backend Apache-2.0; original QM MIT, original Node and SDK retain their licenses/notices. [Original distribution notice](UPSTREAM-NOTICE.md), [QM license](UPSTREAM-QM-LICENSE). Complete original notices stay installed; no third-party relicensing.
