# cline

## What it does

Runs genuine official `cline@3.0.73` in bounded headless JSON/yolo mode. The CLI reads a prompt from anonymous stdin, edits the selected workspace using its native tools and returns buffered NDJSON plus its actual exit code. It uses an explicitly configured OpenAI-compatible provider; a Cline hosted account is not selected. This is the CLI product, with no VS Code extension or desktop UI claim.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

Alibaba generation2 basev0.0.49/Python3.13, SHA256-pinned official Node24.16.0 and npm integrity-locked Cline3.0.73 with its unmodified Linuxx64 native binary/Bun runtime. Native binary SHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7 is checked before every native invocation. Published server package; non-root user, app/home workspace and port9000. [Dockerfile](Dockerfile), [dependency lock](package-lock.json), [design](../docs/design/cline.md).

## Problem solved

Make the real Cline coding agent available through named commands without interactive login, shared developer config or a host-installed CLI. The actual package/help/source tag were inspected; no assumed CLI flags or substitute agent is used. The selected provider/base/model remain explicit and model-generated code runs only inside the caller's newly owned disposable sandbox during acceptance.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./cline --yes
abx run <sandbox-id> cline_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('cline_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/cline_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"native_version": "3.0.73"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Return / side effects |
| --- | --- | --- |
| cline_version | none | Actual pinned native version, `{"native_version":"3.0.73"}`; no model/auth |
| cline_setup_check | none | mode `openai-compatible-byok`; base_url_set/api_key_set/model_set booleans; cline_account_required:false; no network/secret values |
| cline | prompt: required nonempty string1..32768UTF-8 bytes, no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"3.0.73"}`; native tool execution and workspace file changes |

The native argv fixes `--json --yolo --provider openai-compatible --model <configured> --cwd <resolved> --compaction off --retries 2 --timeout <seconds>`, plus per-call private `--config` and `--data-dir`. Prompt text enters anonymous stdin, never flags or a shell. Yolo is an unsupervised native act profile with tool auto-approval; native spawn/team tools are disabled by that upstream profile. It is not read-only or a filesystem/tenant boundary. Use trusted callers and a new disposable sandbox without valuable files/other credentials. Argument cwd containment does not remove the native agent's OS authority. Existing caller files may change; no rollback is promised.

Native output is capped256KiB per stream, with whole-process-group/pidfd/unique-owner descendant cleanup on success/failure/timeout/overflow. Calls serialize; overlap fails busy. The caller's original HOME is not used. Explicit model key/base values and JSON-escaped variants are redacted before returning output. Retain only the requested workspace artifacts; owned runtime HOME/config/cache/session/team files are removed after the call.

Pinned3.0.73 checks JSON mode before reading piped input. A fixed, non-secret positional sentence enables that preflight; the actual task still arrives only through anonymous stdin and is appended by upstream. Runtime1.0.1 corrects the real1.0.0 cloud failure; no user prompt or credential is placed in argv.

Runtime1.0.2 writes the provider profile at the exact native-resolved private data/settings/providers.json path: --data-dir overrides CLINE_PROVIDER_SETTINGS_PATH before native startup. Earlier1.0.1 was stopped after independent inspection found its intended base absent from the native-resolved profile. Routing is not qualified until a fresh synthetic-key native wire check confirms the exact owned endpoint before any approved real-model key is provided.

## Configuration

| Name | Required / default | Meaning |
| --- | --- | --- |
| CLINE_MODEL_API_KEY | model required; empty | Approved compatible endpoint key; only forwarded as native OPENAI_API_KEY |
| CLINE_MODEL_BASE_URL | model required; empty | Explicit HTTPS API base, literal localhost HTTP for authored development only; no userinfo/query/fragment; max2048characters |
| CLINE_MODEL | model required; empty | Actual model identifier, max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing workspace root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Values are captured when commands.py loads. The wrapper writes only provider/model/base metadata into private0600settings, not a model key value; native key resolution uses its documented environment support. Native state is private and removed on return/failure. Global telemetry/auto-update and runtime file logging are disabled; public/private model catalog refresh is disabled. Cline config/data/team/MCP paths are per-call and no caller GitHub/cloud keys, alternate binary override or Cline account token is forwarded. Host operator credentials never enter the native coding process.

## Resources

Linuxx64 only,2vCPU,4096MB, port9000, about10GiB Express rootfs;8GiB image budget enforced. No nested Docker/KVM/GPU is required for this CLI slice. Compatible model tool calling and authorized network egress are required for coding. No hosted Cline/extension/other-provider acceptance or workload memory estimate is claimed.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q cline/test_commands.py cline/test_model_controller.py
python scripts/check_template.py cline --strict
python scripts/check_docs.py
```

Pinned source `cli-v3.0.73`, commitc718573538d76310f464541617ab665108a6c999, defines actual JSON `run_result` with completed finishReason/iterations/text. The external controller invokes the actual paired Python SDK ServerClient.commands.run for the model command and uses independent HTTP files/shell verification. It requires that native terminal event, seeds existing buggy source, preserves original test bytes, downloads fresh report/nonce artifact, reruns complete controller-owned original tests and held-out cases with fresh post-return ACKs, and checks exact owned project absence. Generated source execution is refused on operator loopback and requires explicit owned-cloud opt-in. Required real-model execution never silently skips. Local authored process/NDJSON/credential fixtures prove verifier boundaries only. [Steps guide](../docs/platform-steps.md) covers exact source transfer and resource recovery.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [template spec](../docs/template-spec.md). Keep source pins, contract version, translations and immutable acceptance records consistent.

## Issues

[Template Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Keep credentials/private logs out of public reports.

## License

Wrapper and Cline: Apache-2.0. [Repository license](../LICENSE), [pinned upstream Cline license](UPSTREAM-LICENSE.md). Third-party runtime/dependencies retain their unmodified distribution notices; no hosted account or trademark rights are implied.
