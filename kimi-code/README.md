# kimi-code

## What it does

Run official Kimi Code 2.2.0 for one headless prompt in an existing sandbox directory. Each turn gets private temporary Kimi settings and cleans its owned process group. Upstream prompt mode automatically permits tools, so the wrapper requires explicit allow_tools=True before launching it. Results are buffered stream-JSON text; this template does not provide resumable sessions.

## Stack

Alibaba FC base v0.0.49, pinned Node.js 24.16.0 (architecture-specific SHA256 verified), npm `@moonshot-ai/kimi-code@2.2.0` (MIT), and the exact public server SDK source in Dockerfile. This uses the current Node CLI, not the unrelated/older Python distribution.

## Problem solved

Give callers a reproducible Moonshot CLI inside one Express sandbox, with compatible-model configuration, typed commands, no interactive account login and explicit bounded tool execution.

## Quick start (CLI)

Install the source-aware CLI and paired `agent-sandbox-client`/server as described in [setup](../docs/using-templates.md). Configure the selected model environment before the named server starts; [prewarmed process configuration](../docs/runtime-environment.md) explains why create-time env does not reconfigure an existing process.

```bash
abx template deploy ./kimi-code -y
abx create <template-id> --detach
abx run <sandbox-id> kimi_version
abx run <sandbox-id> kimi --json-args '{"prompt":"Summarize the files in the current directory.","command_timeout":120,"allow_tools":true}'
abx kill <sandbox-id>
abx template delete <template-id> -y
```

Replace IDs with results from the preceding commands. These examples use the current Express CLI. Named-command invocation uses `abx run`.

## Quick start (Python SDK)

Install `agent-sandbox-client` from the [paired pinned source](../docs/python-client-installation.md). Set the documented Kimi model variables on the configured server process.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600)
    try:
        print(await sb.run("kimi", prompt="Summarize the files in the current directory.",
                           command_timeout=120, allow_tools=True, timeout=150))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

`timeout=150` is the client request budget; `command_timeout=120` bounds the process group. An HTTP timeout alone does not cancel a turn. Select `server_at` for an explicitly configured server port/token.

## Quick start (HTTP POST)

Use the server URL returned for port 9000. Server and provider-gateway authentication are separate; include the selected provider's documented gateway headers when required.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/kimi"   --header 'Content-Type: application/json'   --header "Authorization: Bearer $ABX_SERVER_TOKEN"   --data '{"prompt":"Summarize the files in the current directory.","command_timeout":120,"allow_tools":true}'
# {"result":"<buffered upstream stream-JSON text>"}
```

Omit Authorization only when the server has no token. The body is the direct argument object. Missing/mistyped arguments return 400, invalid auth 401, unknown commands 404 and execution/input errors 500 with `error` and `type`.

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
| ABX_SERVER_TOKEN | no | server authentication, empty by default |

Model variables are verified in the actual npm 2.2.0 runtime and its official [provider documentation](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md). Each invocation sets KIMI_CODE_HOME to an owned temporary directory, leaving caller settings intact, and excludes unrelated cloud/registry credential variables. Secret values and JSON-escaped variants are redacted from returned stdout/stderr. The wrapper does not promise a read-only prompt mode.

## Resources

2 vCPU, 2048 MiB, platform rootfs, port 9000. No KVM, Docker daemon, display or GPU is required. Node >=22.19 is required upstream and provided by the pinned build. No model key is baked into the image.

## Verified

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

Image-backed real-model coding acceptance also passed17 checks with qwen3.8-flash; see the [model receipt](evidence/model-express-2026-10-19T153814Z.json). Earlier failed attempts remain separate.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing run recorded for this template.

</details>

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
