# muse

## What it does

Run the unchanged official Meta Muse Code1.4.11-R6667.1 native headless agent, original miniswe tools and native runtime records on one owned Express computer. Coding uses an explicitly configured compatible Responses model. The authored local relay supplies the selected model catalogue and keeps the upstream key out of native/tool environments; Responses requests and streams pass unchanged. This is the original Muse binary, not a same-named substitute. [Original documentation](https://dev.meta.ai/docs/muse-code).

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13, root-owned original native ELF384809176bytes with its published SHA256, Python stdlib relay/process controls, pinned server34e7e011c5569f77b7f605e65313be7498f6cf02. No new Python/Node dependencies. [Dockerfile](Dockerfile), [provenance](upstream.json), [upstream notice](UPSTREAM-NOTICE.md), [design](../docs/design/muse.md). The template source license does not relicense the original upstream artifact. A task-owned local gzip cache can be rehashed and streamed to private OSS without a second384.8MB operator disk copy; the target still checks unchanged original bytes.

## Problem solved

Provide genuine original Muse file/tool execution through named SDK/HTTP commands with private per-call configuration and verified ownership. A generic compatible gateway lacks the original CLI's required `/muse-code/models`: the narrow local relay supplies that metadata, then forwards original `/responses` bytes to exactly the configured endpoint with no tool/model translation. No vendor/account/subscription fallback.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./muse --yes
abx run <sandbox-id> muse_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('muse_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/muse_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "Muse Code 1.4.11 (1.4.11-R6667.1)"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| muse_version | none | `Muse Code 1.4.11 (1.4.11-R6667.1)` after exact original ELF verification; no model |
| muse_native_check | none | `{original_native:true,headless_json:true,anonymous_api_key_stdin:true,no_session_log:true}` from actual headless help; no model |
| muse_setup_check | none | mode `original-native-muse-explicit-responses`, native_present/model_key_set/model_base_set/model_set flags; model_account_verified:false/provider_default_fallback:false/catalog_relay:true; no values/network |
| muse | prompt: required nonempty string1..32768UTF8bytes/noNUL; cwd: string default empty, max4096bytes, existing resolved directory inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final stdout, native_completed, actual model_calls/native_tool_results, exit_code0, original binary/version/model/protocol and completed relay_calls. Original tools may edit caller project files; no raw transcript |

Fixed original argv: `exec --json --api-key-stdin --provider meta --model <configured> --preset miniswe --reasoning-effort minimal --max-model-steps16 --no-session-log --disable-reminders --no-foreign-personal-context --disable-web-tools --yolo --workspace <contained-project>`. Original settings schema_version1, endpoint_transport base_url/auth bearer and agents.execution_capacity1 are private per call. Original miniswe has no available subagent_spawn; no delegated model/tool tree is selected. Caller project instructions may load after the explicit trust flag.

Native completion requires exact correlated original model/usage/terminal records, positive completed model calls, no failed/cancelled/child calls and nonempty final text. Coding acceptance additionally requires positive original tool results and independent artifacts/tests. Model requests32maximum,2MiB each,4MiB per response,16native model steps; native stdout/stderr256KiB each. Issued relay requests drain before completion. Owned close/process cleanup may add up to50seconds; SDK timeout should be at least command_timeout+80. Concurrent model calls fail busy.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| MUSE_MODEL_API_KEY | empty; required for coding | Key for the explicitly selected compatible endpoint; retained only in parent relay |
| MUSE_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS Responses base, max2048characters, no userinfo/query/fragment; literal-loopback HTTP only for authored fixtures |
| MUSE_MODEL | empty; required for coding | Actual upstream model identifier,1..200allowed identifier characters |
| WORKSPACE | `/home/user/app` | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

Captured at commands.py import; presence flags do not prove authentication. Key max8192/no control characters. Native receives only a fresh per-call local relay token by anonymous stdin. The parent relay uses the upstream key only for the exact approved Responses endpoint, rejects redirects and wrong route/token/model, and retains no transcript. Native/tools use a minimal environment and private HOME/cache/config; caller project artifacts persist. Same-user OS access remains; cwd containment and environment filtering are not another tenant boundary. `--yolo` selects the disposable outer sandbox as the execution boundary.

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000,8GiB image rootfs budget, no KVM/Docker/GPU or extra privileges. Original artifact downloads384.8MB; model requests need approved egress. The bounded actual image/step/fullHTTP/model slice passes below; peak memory was not measured. Other providers, interactive sessions, retained resume, voice/local weights, MCP/plugin services and Meta-hosted subscriptions are outside this profile.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q muse/test_commands.py muse/test_relay.py muse/test_terminal.py
python scripts/check_template.py muse --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py muse --sandbox-create sdk --http --asset-transport oss
```

Use fixed non-executable replies for local relay/parser fixtures. Native/generated-code acceptance runs only on a fresh explicitly owned cloud target. Preserve original binary and notices, exact bounds, redirect refusal, anonymous input and process/relay cleanup. Formal coding checks require changed source, original test bytes, new report/exact nonce, original3plus4held-outs/fresh post-return ACK and independent owned absence.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include owner note/evidence and both README languages; merge only after actual required checks/review pass.

## Issues

[Template Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71) owns this delivery. [Template bugs](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); original Muse behavior belongs to its upstream support. Never attach credentials or raw private transcripts.

## License

Authored template code/documentation: [Apache-2.0](../LICENSE). Original Meta artifact terms/notices remain separate; see [attribution](UPSTREAM-NOTICE.md). No upstream open-source license, vendor endorsement or hosted-model account is asserted.
