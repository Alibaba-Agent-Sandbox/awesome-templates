# stagehand

## What it does

Runs the genuine Node.js `@browserbasehq/stagehand@4.3.0` SDK and its bundled browser extension against a private local Chromium. A bounded call performs one upstream `act` instruction, optionally extracts a `{text: string}` result with native `extract`, and writes a fresh PNG. It is a local browser slice; Browserbase hosted sessions, login persistence, full autonomous planning and arbitrary extraction schemas are outside this template's contract.

## Stack

Alibaba generation2 base v0.0.49, SHA256-pinned Node24.16.0, npm integrity-locked Stagehand4.3.0/Zod4.4.3 with the disclosed exact-source connect-parameter patch, Playwright1.58.0 Chromium1208/145.0.7632.6, Python3.13 and server source e2cb27e24fde0a67112f82b8d44af463445a5d1a. Runtime is non-root user; app `/home/user/app`, port9000. [Dockerfile](Dockerfile), [lockfile](package-lock.json), [design](../docs/design/stagehand.md).

## Problem solved

Expose real Stagehand semantic browser actions through the Agent Sandbox named-command API without requiring a Browserbase account. Native4.3.0 does not accept a custom base URL in ModelConfig. The documented upstream ClientLLM callback maps structured text/image requests to an explicitly configured OpenAI-compatible Chat Completions endpoint; DOM interpretation, selector choice, browser actions and extraction still use the actual SDK/extension. No substitute browser agent or fake CLI is installed.

## Quick start (CLI)

Named operations use `abx run`; CLI0.4.1 selects this surface explicitly as `abx --native run` below.

Install the [verified native CLI entry](../docs/platform-steps.md), configure Express credentials, publish the exact source commit when preparation needs public COPY inputs, and replace each unique-run/template/sandbox placeholder with your own value. Wait for official READY before creating. The following uses the native CLI syntax; it is a reproduction recipe, not a passing cloud receipt.

```bash
python scripts/prepare_steps.py stagehand --output /tmp/stagehand-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/stagehand-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> stagehand_self_test
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

`stagehand_self_test` returns `STAGEHAND_NATIVE_OK` after real offline browser/extension navigation/title/PNG and owned cleanup. Prefer the canonical SDK-created acceptance runner for automatic receipts and exact ownership recovery:

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py stagehand --sandbox-create sdk --http
```

## Quick start (Python SDK)

Install `agent-sandbox-client` from the [paired pinned source](../docs/python-client-installation.md); import `agent_sandbox`. The example uses only its own sandbox and the model-free native self-test.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("stagehand_self_test", timeout=90))
    finally:
        await sb.kill()

asyncio.run(main())
```

For real actions, configure `STAGEHAND_API_KEY`, `STAGEHAND_BASE_URL` and `STAGEHAND_MODEL` on the command server before it starts. A prewarmed9000 server does not inherit later create-time environment automatically; follow [explicit process configuration](../docs/runtime-environment.md). Then `await sb.run("stagehand", task="Click the Publish button", url="https://your-authorized-site.example/", extract_instruction="Read the displayed receipt", command_timeout=180, timeout=210)` returns the schema below. Replace the URL with an authorized reachable site. Use only a fresh owned sandbox without valuable credentials.

## Quick start (HTTP POST)

`ABX_SERVER_URL` is the sandbox port9000 URL (`sb.network.get_url(9000)`). When server authentication is enabled, inject its own `ABX_SERVER_TOKEN` separately from the model key.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/stagehand_self_test" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 is `{"result":"STAGEHAND_NATIVE_OK"}`. `POST /commands/stagehand` accepts the direct JSON argument object, without an args wrapper. Missing/type-invalid/unknown arguments return400, authentication failure401, unknown command404 and semantic guards/runtime/native/model failure500 with `{error,type}`. Results are buffered; client disconnection does not cancel the bounded native process.

## Command reference

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| stagehand_version | none | Actual installed SDK version `4.3.0`; no browser/model |
| stagehand_setup_check | none | Boolean `api_key_set`, `base_url_set`, `model_set`; mode; `browserbase_account_required:false`; no network/secrets |
| stagehand_self_test | none | `STAGEHAND_NATIVE_OK`; new private offline browser, title/PNG and cleanup;60s deadline |
| stagehand | `task`: required nonempty string; `url`: required HTTP(S) without userinfo/control/whitespace; `extract_instruction`: optional string default empty; `command_timeout`: integer1..600seconds default180 | Actual native action, optional text extraction and new PNG; private local browser per call |

Task and extraction instructions each cap32768UTF-8 bytes; URL caps8192. Return object: `version`, `sdk_sha256`, `title`, `final_url`, `action:{success,message,actionDescription,actions}`, `extracted:null` or `{text}`, `model_calls` (at most8), `screenshot_path` and `png_bytes`. The unique artifact is `/home/user/app/stagehand-artifacts/<random>.png` (or under WORKSPACE); PNG caps8MiB. Read it through `sb.files.read_bytes` and delete only that returned artifact after use. No existing caller file is overwritten. Calls run serially; overlap fails explicitly instead of replacing an active process. Native stdout/stderr each cap256KiB; private upstream errors are omitted; nonzero exit/deadline/cleanup uncertainty fails.

## Configuration

| Variable | Required / default | Meaning |
| --- | --- | --- |
| STAGEHAND_API_KEY | required for model; empty | Approved compatible endpoint credential; never a Browserbase token |
| STAGEHAND_BASE_URL | required for model; empty | HTTPS API base ending in your endpoint's API prefix; literal localhost HTTP allowed for development; no userinfo/query/fragment; appends `/chat/completions` |
| STAGEHAND_MODEL | required for model; empty | Actual model identifier, at most200 allowed identifier characters |
| ABX_SERVER_TOKEN | optional; empty | Independent named-server Bearer credential |
| WORKSPACE | `/home/user/app` | Existing artifact root |

The wrapper uses upstream ClientLLM structured generation, maps text/images and requires complete JSON-schema model replies. Requests cap2MiB, replies1MiB, each inference60seconds; no redirects, retries or provider fallback. Model values are captured at server import. Secrets enter the Node consumer via anonymous stdin memory, never argv, browser environment or credential files. Browser subprocesses inherit only selected runtime/certificate variables and new private HOME/cache/profile. Native Chromium sandbox is explicitly disabled inside the outer disposable sandbox; it is not a tenant/security boundary. Pages can reach networks accessible to that sandbox; authenticate/trust named-command callers accordingly.

## Resources

2vCPU,4096MB RAM, port9000, about10GiB Express rootfs. No Docker/KVM/GPU needed inside the sandbox. The image enforces an8GiB rootfs budget. Local browser/extension startup and compatible model structured output are required. Browserbase cloud/cache/services are not required or verified.

## Verified

Template1.1.0 explicitly fixes pinned SDK4.3.0 local connect forwarding: its factory accepts but drops extensionId, then attempts Extensions.loadUnpacked over a debugging port that this Chromium rejects. The owned launcher now preloads the unmodified bundled npm extension, observes its actual service-worker ID and uses native localBrowser.connect/Stagehand.create/act/extract. The [build patch](patch_sdk.py) requires the pristine SDK SHA256 and forwards only the existing public parameter. The worker requires the exact patched source SHA256 `bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0`. This is a disclosed patched upstream distribution, not an unmodified release or substitute browser agent. Previous1.0.0native cloud/L1 failures remain historical and do not qualify1.1.0; fresh actual acceptance is required.

No current provider or real-model pass is recorded yet. Source/import/fixture checks are not cloud acceptance. Keep `tested_on: []` and catalog experimental until exact current native L1, Express SDK creation/commands/model and independent cleanup receipts pass.

## Secondary development

```bash
npm ci --prefix stagehand --ignore-scripts --registry=https://registry.npmjs.org
node --test stagehand/test_transport.mjs
python -m pytest -q stagehand/test_commands.py
python scripts/check_template.py stagehand --strict
python scripts/check_docs.py
```

Local authored callbacks/process tests verify transport and guards only. The HTTP e2e reports native absence as SKIP unless E2E_REQUIRE_CLI=1; E2E_REQUIRE_LLM cannot silently skip a requested real model. Actual model behavior uses the separate owned SDK controller. Preserve pins, private ownership, deadlines, translations and old pass/fail records on updates. [Platform steps](../docs/platform-steps.md) explains source hashes, transport and cleanup.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [template spec](../docs/template-spec.md). Change only this template's contract; SDK/CLI defects belong to their owners.

## Issues

[Template Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Never include credentials or private logs.

## License

Wrapper: [Apache-2.0](../LICENSE). Stagehand and Zod: MIT; retain [upstream Stagehand license](UPSTREAM-LICENSE.md). Chromium/Node and their dependencies retain upstream notices/licenses in their unmodified distributions. No SaaS software or vendor account rights are implied.
