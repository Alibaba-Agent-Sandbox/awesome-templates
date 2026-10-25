# kimi-code

## What it does

Run official Kimi Code 2.2.0 for one headless prompt in an existing sandbox directory. Each turn gets private temporary Kimi settings and cleans its owned process group. Upstream prompt mode automatically permits tools, so the wrapper requires explicit allow_tools=True before launching it. Results are buffered stream-JSON text; this template does not provide resumable sessions.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49, pinned Node.js 24.16.0 (architecture-specific SHA256 verified), npm `@moonshot-ai/kimi-code@2.2.0` (MIT), and the exact public server SDK source in Dockerfile. This uses the current Node CLI, not the unrelated/older Python distribution.

## Problem solved

Give callers a reproducible Moonshot CLI inside one Express sandbox, with compatible-model configuration, typed commands, no interactive account login and explicit bounded tool execution.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./kimi-code --yes
abx run <sandbox-id> kimi_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('kimi_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/kimi_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "2.2.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns |
| --- | --- | --- |
| kimi_version | none | exact upstream version string |
| kimi_setup_check | none | installed/version/pinned_version, model/key/base flags and workspace; no credential values |
| kimi | prompt: required string, 1..65536 UTF-8 bytes; cwd: string, default configured workspace, must exist; command_timeout: integer, default 600, 1..1800 seconds; allow_tools: boolean, default false (must explicitly be true to launch upstream prompt mode) | buffered stream-JSON string; upstream nonzero exit, timeout or over-8-MiB output raises an error |

The CLI argv is `kimi --prompt PROMPT --output-format stream-json`. Upstream 2.2.0 rejects --prompt combined with --auto/--yolo and internally forces automatic tool permission; allow_tools must therefore be true or the wrapper refuses the turn. Values are separate argv elements. Kimi inherits filesystem/network authority of sandbox user; auto mode can edit files and execute commands. Do not grant it to untrusted tasks without reviewing that authority.

## Configuration

| Variable | Required | Default / purpose |
| --- | --- | --- |
| KIMI_MODEL_NAME | for model turns | actual provider model ID |
| KIMI_MODEL_API_KEY | for model turns | empty secret declaration; inject at process start |
| KIMI_MODEL_BASE_URL | for model turns | explicit authorized compatible endpoint; no implicit credential forwarding |
| KIMI_MODEL_PROVIDER_TYPE | no | openai; also kimi or anthropic, matching upstream 2.2.0 |
| WORKSPACE | no | /home/user/app |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Model variables are verified in the actual npm 2.2.0 runtime and its official [provider documentation](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md). Each invocation sets KIMI_CODE_HOME to an owned temporary directory, leaving caller settings intact, and excludes unrelated cloud/registry credential variables. Secret values and JSON-escaped variants are redacted from returned stdout/stderr. The wrapper does not promise a read-only prompt mode.

## Resources

2 vCPU, 2048 MiB, platform rootfs, port 9000. No KVM, Docker daemon, display or GPU is required. Node >=22.19 is required upstream and provided by the pinned build. No model key is baked into the image.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Preserve the upstream CLI rather than replacing it with an HTTP completion imitation. Keep argv, environment, version and both languages consistent. Run `python scripts/check_template.py kimi-code`, its unit tests and local HTTP verifier. Real model acceptance requires actual existing-source edits, a new report/exact artifact, unchanged original tests and fresh independent held-out acknowledgments. A version check is not model acceptance. Use [platform steps](../docs/platform-steps.md) with `python scripts/run_steps_e2e.py kimi-code` for real Express deployment.

## Contributing

See [contribution rules](../CONTRIBUTING.md) and [design](../docs/design/kimi-code.md). Update records and regression evidence in the same PR.

## Issues

Template issues belong to [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/48); SDK/server to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions and sanitized reproduction.

## License

Template wrapper: Apache-2.0, see [LICENSE](../LICENSE). Upstream Kimi Code: MIT, distributed through the pinned official npm package with its license retained.

### 2026-10-20 full step checkpoint: template1.0.0

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155159Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
