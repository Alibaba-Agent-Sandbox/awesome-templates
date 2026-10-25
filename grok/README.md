# grok

## What it does

Runs genuine official xAI `@xai-official/grok@1.0.62` headless coding. The native Rust binary reads anonymous stdin through --prompt-file /dev/stdin, uses its real tools and returns buffered JSON plus actual exit code. An explicitly configured approved compatible model is selected. This is xAI Grok Build, not the unrelated community grok-dev CLI; compatible-model success does not qualify xAI-hosted Grok models or subscriptions.

[Official xAI source snapshot](https://github.com/xai-org/grok-build/tree/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8), [native custom models](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md), [headless protocol](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Python3.13, SHA256-pinned official Node24.16.0 and npm integrity-locked Grok Build1.0.62 with its unmodified Linuxx64 native Rust binary. Native binary SHA2562a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa is checked before every native invocation. Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a; non-root user, app/home workspace and port9000. [Dockerfile](Dockerfile), [dependency lock](package-lock.json), [design](../docs/design/grok.md).

## Problem solved

Make the real Grok Build coding agent available through named commands without interactive login, shared developer config or a host-installed CLI. The actual package/help/source tag were inspected; no assumed CLI flags or substitute agent is used. The selected provider/base/model remain explicit and model-generated code runs only inside the caller's newly owned disposable sandbox during acceptance.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./grok --yes
abx run <sandbox-id> grok_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('grok_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/grok_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"native_version": "1.0.62"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Return / side effects |
| --- | --- | --- |
| grok_version | none | Actual pinned native version, `{"native_version":"1.0.62"}`; no model/auth |
| grok_setup_check | none | mode `openai-compatible-byok`; base_url_set/api_key_set/model_set booleans; xai_account_required:false; no network/secret values |
| grok | prompt: required nonempty string1..32768UTF-8 bytes, no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"1.0.62"}`; native tool execution and workspace file changes |

Fixed native flags select --output-format json, --always-approve, --no-plan, --no-subagents, --disable-web-search, --sandbox off, --model abx-approved, --max-turns20 and --prompt-file /dev/stdin. The tools allowlist contains read_file/search_replace/grep/list_dir/run_terminal_cmd; Agent is denied. Native sandbox off leaves tool OS authority inside the caller’s trusted disposable outer sandbox; cwd containment is only an argument boundary. Native tool approvals are automatic; no rollback is promised. Prompt and model key values never enter argv.

Native output is capped256KiB per stream, with whole-process-group/pidfd/unique-owner descendant cleanup on success/failure/timeout/overflow. Calls serialize; overlap fails busy. The caller's original HOME is not used. Explicit model key/base values and JSON-escaped variants are redacted before returning output. Retain only the requested workspace artifacts; owned runtime HOME/config/cache/session/team files are removed after the call.


## Configuration

| Name | Required / default | Meaning |
| --- | --- | --- |
| GROK_MODEL_API_KEY | model required; empty | Approved compatible endpoint key; only forwarded as native ABX_GROK_MODEL_KEY |
| GROK_MODEL_BASE_URL | model required; empty | Explicit HTTPS API base, literal localhost HTTP for authored development only; no userinfo/query/fragment; max2048characters |
| GROK_MODEL | model required; empty | Actual model identifier, max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing workspace root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

Values are captured when commands.py loads. A private0600 config.toml stores explicit model/base and env_key="ABX_GROK_MODEL_KEY" without the key value. Custom api_backend="chat_completions" prevents selecting a hosted vendor model. Private GROK_HOME/HOME/cache/session state is removed after each call; auto-update, leader, telemetry/trace upload, memory and background workflows are disabled. Native shell_environment_policy inherits core with default secret exclusion; no caller cloud/GitHub/vendor account token is forwarded. Agent tools still have OS authority in the disposable sandbox.

## Resources

Linuxx64 only,2vCPU,4096MB, port9000, about10GiB Express rootfs;8GiB image budget enforced. No nested Docker/KVM/GPU is required for this CLI slice. Compatible model tool calling and authorized network egress are required for coding. No hosted Grok Build/extension/other-provider acceptance or workload memory estimate is claimed.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q grok/test_commands.py grok/test_model_controller.py
python scripts/check_template.py grok --strict
python scripts/check_docs.py
```

Actual official binary reports `grok1.0.62 (1474f9cbdd91)` and matching SHA256. Public source snapshot2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 documents the custom model/headless contracts; it is not claimed as the binary build commit. The real Python SDK named command is followed by independent HTTP source/artifact/original-tests and fresh post-return held-out checks on a newly owned cloud target. JSON requires end_turn, positive actual num_turns and real session/request IDs; a text marker alone is insufficient. Local fixture controls and keyless help/version are not native model/cloud passes.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [template spec](../docs/template-spec.md). Keep source pins, contract version, translations and immutable acceptance records consistent.

## Issues

[Template Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Keep credentials/private logs out of public reports.

## License

Wrapper and official xAI Grok Build: Apache-2.0. [Repository license](../LICENSE), [upstream license](UPSTREAM-LICENSE.md), [official binary third-party notices](THIRD_PARTY_NOTICES.md). Distribution dependencies retain their notices; no hosted subscription, model or trademark rights are implied.
