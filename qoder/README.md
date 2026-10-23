# Qoder

## What it does

Run the real Qoder coding assistant headlessly against files in a sandbox. The existing `qoder_run` Python script command remains available.

## Stack

Qoder CLI `@qoder-ai/qodercli@1.1.72`; platform Python 3.13 / Node.js 20; Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://docs.qoder.com/cli/run-in-scripts)

## Problem solved

Expose a typed, bounded coding task through one named command; inject model credentials at sandbox creation.

## Quick start (CLI)

The examples use the current Express CLI: `abx create <template-id> --detach` prints the sandbox ID; `abx kill <sandbox-id>` cleans it up. Named commands use `abx run`. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qoder
abx create <template-id> --detach --env QODER_PERSONAL_ACCESS_TOKEN="$QODER_PERSONAL_ACCESS_TOKEN"
abx run <sandbox-id> qoder --arg prompt="Inspect this project and fix the failing calculation"
```

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client`. See [installation](../docs/python-client-installation.md) for availability and pinned source installation.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"QODER_PERSONAL_ACCESS_TOKEN": os.environ["QODER_PERSONAL_ACCESS_TOKEN"]})
    try:
        print(await sb.run("qoder", prompt="Inspect and fix the calculation",
                           timeout=660))
    finally:
        await sb.kill()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/qoder" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600}'
```

Success is `{"result":"buffered output"}`. Send arguments directly, with no `args` wrapper. The provider defines gateway access credentials; `ABX_SERVER_TOKEN` separately protects this server. Omit Authorization when unset. The SDK supports `sb.server_at(9000, token=...)`.

HTTP 400: missing/invalid/range arguments; 401: authentication; 404: unknown command; 500: missing credentials, execution failure or timeout. Results are buffered. `command_timeout` bounds execution; SDK `timeout` only controls HTTP waiting and does not guarantee cancellation. Use process APIs for background work.

## Command reference

`qoder` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| cwd | string | "" | Existing directory; relative paths resolve under WORKSPACE. |
| command_timeout | integer | 600 | Execution deadline, 1–1800 seconds. |

| Additional command | Parameters | Result |
|---|---|---|
| qoder_version | none | Installed CLI version. |
| qoder_setup_check | none | Read-only installed/version/PAT-presence diagnostic. |
| qoder_run | script: string = main.py | Local Python stdout; does not call Qoder. |

## Configuration

`WORKSPACE=/home/user/app`. `QODER_PERSONAL_ACCESS_TOKEN` is required for model execution; browser/OAuth login is never started. `accept_edits` auto-approves file edits; upstream rejects shell confirmations. Sessions are not persisted and automatic updates are disabled.

Secret declarations in template.yaml are empty; do not copy credentials into images or logs.

## Resources

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## Verified

No project-recognized receipt certifies the current workflow manifest. Historical acceptance records retain only their original input and call-path scope; see [workflow verification](../docs/workflows.md).

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing run recorded for this template.

</details>

## Secondary development

```bash
python3 scripts/check_template.py qoder
python3 -m pytest -q qoder/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` controls the model acceptance command budget (default 600 seconds, range 1–1800). L0 does not call a model. `E2E_REQUIRE_LLM=1` forces real coding acceptance. L3 uses target setup diagnostics, seeds failing source/tests, verifies changed source/new artifacts/unchanged tests through target file APIs, then independently executes unittest and held-out calculations. A missing key is not acceptance.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py qoder` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/qoder.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### 2026-10-20 full step checkpoint: template1.1.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155408Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
