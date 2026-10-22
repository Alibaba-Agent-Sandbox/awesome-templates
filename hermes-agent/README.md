# Hermes Agent

## What it does

Run the actual upstream Hermes Agent CLI with its local terminal and file toolsets. This template exposes the coding slice; messaging gateways, browser/desktop integrations and external terminal backends are not provisioned.

## Stack

NousResearch Hermes Agent v0.22.1, commit `297552a9d646119871391d202509822cd86330df`; private Python 3.14.6; `uv==0.12.3`; upstream frozen `uv.lock`; platform Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df)

## Problem solved

Expose the real Hermes headless CLI through a typed named command with a bounded CLI wait; inject model credentials at sandbox creation. Accepted gateway work has a separate lifecycle.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

```bash
abx template install alibaba-agent-sandbox/awesome-templates//hermes-agent
abx create --template <template-id> --env OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
abx run <sandbox-id> hermes --arg prompt="Inspect this project and fix the failing calculation" --arg model="<model-id>"
```

Hermes requires a compatible model argument or HERMES_MODEL at creation.

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client`. See [installation](../docs/python-client-installation.md) for availability and pinned source installation.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"]})
    try:
        print(await sb.run("hermes", prompt="Inspect and fix the calculation", model="<model-id>",
                           timeout=660))
    finally:
        await sb.kill()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/hermes" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600,"model":"<model-id>"}'
```

Success is `{"result":"buffered output"}`. Send arguments directly, with no `args` wrapper. The provider defines gateway access credentials; `ABX_SERVER_TOKEN` separately protects this server. Omit Authorization when unset. The SDK supports `sb.server_at(9000, token=...)`.

HTTP 400: missing/invalid/range arguments; 401: authentication; 404: unknown command; 500: missing credentials, execution failure or timeout. Results are buffered. `command_timeout` bounds the CLI process and its owned process group; SDK `timeout` only controls HTTP waiting. Hermes v0.22.1 executes accepted turns through a separate canonical gateway and managed workers. Those can continue after either timeout. Destroy the sandbox to stop all work; per-turn gateway cancellation is not provided by this template. Use process APIs for background work.

## Command reference

`hermes` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| model | string | "" | Required argument or HERMES_MODEL; no implicit model choice. |
| provider | string | "" | Argument or HERMES_PROVIDER=openrouter; openrouter / openai-api / custom. |
| cwd | string | "" | Existing directory; relative to WORKSPACE. |
| max_turns | integer | 20 | Maximum tool rounds, 1–100. |
| command_timeout | integer | 600 | CLI process deadline, 1–1800 seconds; accepted gateway work can continue. |

| Additional command | Parameters | Result |
|---|---|---|
| hermes_version | none | Installed upstream version and provenance. |
| hermes_setup_check | none | Read-only CLI/version/provider-key diagnostic. |
| run | script: string = main.py | Local Python stdout (compatibility). |

## Configuration

`WORKSPACE=/home/user/app`; `HERMES_HOME=/home/user/.hermes`; `HERMES_PROVIDER=openrouter`. Supply `HERMES_MODEL` or the model argument. OpenRouter requires `OPENROUTER_API_KEY`; openai-api/custom require `OPENAI_API_KEY`. Custom also requires `OPENAI_BASE_URL`. The command uses `-Q --yolo`, terminal/file toolsets and the local terminal backend. It ignores user config and rules, does not run interactive setup, and kills the owned process group on timeout. Hermes may persist session/memory state under HERMES_HOME. Its CLI auto-starts the canonical gateway when needed; that detached authority exits after upstream idle conditions are satisfied. Killing the CLI does not cancel an accepted gateway turn. Messaging adapters are not configured, while the internal canonical gateway is part of this upstream CLI execution path.

Secret declarations in template.yaml are empty; do not copy credentials into images or logs.

Hermes runs through its private Python 3.14 shebang. The image exposes only its `hermes` launcher on the platform PATH; `python3` and `agent-sandbox-server` continue to use the server environment. For local direct `python3 commands.py` development, select the environment with agent-sandbox-server installed; placing the entire Hermes venv first on PATH would select a different interpreter.

## Resources

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.1.1; regular image, actual CLI/SDK, complete HTTP 9 PASS / 0 FAIL / 1 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T110933Z.json) |
| opensandbox | 1.1.1; original Docker backend, every CLI/SDK named smoke, complete HTTP 9 PASS / 0 FAIL / 1 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T111713Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version 1.1.1 passed actual CI-image registration, official READY, CLI/SDK and 17 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion. Independently confirmed sandbox/template/registry cleanup. Status remains experimental; other providers are unverified.

| Provider | Scope | Evidence |
| --- | --- | --- |
| alicloud-express | Exact current version, actual image and independently verified cleanup | [canonical receipt](evidence/express-2026-10-20.json), [HTTP](evidence/image-http-2026-10-20T062649Z.json), [strict model](evidence/model-image-2026-10-20T062649Z.json) |

Additional native SDK creation acceptance2026-10-20: the same1.1.1 runtime was registered from its verified CI image, reached official READY and was actually created by Python Sandbox.create, then passed CLI/SDK smoke and its model-off HTTP controller. [New immutable SDK receipt](evidence/express-2026-10-20T110933Z.json), [HTTP/cleanup](evidence/image-http-2026-10-20T110933Z.json). Owned sandbox/template/registry absence and post-runtime image digest were independently confirmed. This run did not repeat the model; the prior exact-runtime/controller real-model pass above remains a separate unchanged receipt.

</details>

## Historical verification

Historical1.1.0 image acceptance on2026-10-19: CLI-created sandbox, full image/provenance/HTTP plus17 real compatible-model assertions and independently verified owned sandbox/template/registry cleanup. These receipts retain the original version/controller and do not qualify1.1.1. [image](evidence/express-2026-10-19.json) · [HTTP](evidence/image-http-2026-10-19T175057Z.json) · [model](evidence/model-image-2026-10-19T175057Z.json).



The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

No provider has a passing run recorded for this template.

## Secondary development

```bash
python3 scripts/check_template.py hermes-agent
python3 -m pytest -q hermes-agent/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` controls the model acceptance command budget (default 600 seconds, range 1–1800). L0 does not call a model. `E2E_REQUIRE_LLM=1` forces real coding acceptance. L3 uses target setup diagnostics, seeds failing source/tests, verifies changed source/new artifacts/unchanged tests through target file APIs, then independently executes unittest and held-out calculations. A missing key is not acceptance.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py hermes-agent` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/hermes-agent.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### Current platform-step acceptance

[Current-version genuine steps](evidence/express-2026-10-20T151019Z.json) and [full external HTTP result](evidence/verification-steps-2026-10-20T151019Z.json): official READY, actual Python SDK creation, CLI/SDK smoke and 9 PASS / 0 FAIL / 1 model SKIP; 319.815 seconds. Independent owned sandbox/template and private asset-cache cleanup passed. Earlier failed step attempts remain historical failures; this receipt is model-free and does not extend prior image/model scope.
