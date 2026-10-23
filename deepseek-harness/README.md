# DeepSeek coding harness

## What it does

Run a repository-owned coding agent using the official DeepSeek Chat Completions function-call protocol. Each turn executes read_file, write_file, list_files or run_shell and returns tool results to the model until a final answer.

## Stack

Python 3.13; `httpx==0.28.1`; Agent Sandbox server. No third-party agent CLI.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://api-docs.deepseek.com/guides/tool_calls/)

## Problem solved

Expose a typed, bounded coding task through one named command; inject model credentials at sandbox creation.

## Quick start (CLI)

The examples use the current Express CLI: `abx create <template-id> --detach` prints the sandbox ID; `abx kill <sandbox-id>` cleans it up. Named commands use `abx run`. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

```bash
abx template install alibaba-agent-sandbox/awesome-templates//deepseek-harness
abx create <template-id> --detach --env DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"
abx run <sandbox-id> deepseek --arg prompt="Inspect this project and fix the failing calculation"
```

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client`. See [installation](../docs/python-client-installation.md) for availability and pinned source installation.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"DEEPSEEK_API_KEY": os.environ["DEEPSEEK_API_KEY"]})
    try:
        print(await sb.run("deepseek", prompt="Inspect and fix the calculation",
                           timeout=660))
    finally:
        await sb.kill()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/deepseek" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600}'
```

Success is `{"result":"buffered output"}`. Send arguments directly, with no `args` wrapper. The provider defines gateway access credentials; `ABX_SERVER_TOKEN` separately protects this server. Omit Authorization when unset. The SDK supports `sb.server_at(9000, token=...)`.

HTTP 400: missing/invalid/range arguments; 401: authentication; 404: unknown command; 500: missing credentials, execution failure or timeout. Results are buffered. `command_timeout` bounds execution; SDK `timeout` only controls HTTP waiting and does not guarantee cancellation. Use process APIs for background work.

## Command reference

`deepseek` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| model | string | "" | Argument, then DEEPSEEK_MODEL, then deepseek-flash. |
| cwd | string | "" | Existing directory; relative to WORKSPACE. |
| max_turns | integer | 20 | Maximum API rounds, 1–100. |
| command_timeout | integer | 600 | Worker execution deadline, 1–1800 seconds. |

| Additional command | Parameters | Result |
|---|---|---|
| deepseek_setup_check | none | Read-only key-presence/model/tool diagnostic. |
| deepseek_tools | none | Comma-separated registered tool names; no API call. |
| run | script: string = main.py | Local Python stdout (compatibility). |

## Configuration

`DEEPSEEK_BASE_URL=https://api.deepseek.com`; `DEEPSEEK_MODEL=deepseek-flash`; `WORKSPACE=/home/user/app`. `DEEPSEEK_API_KEY` falls back to `OPENAI_API_KEY`. To use a compatible service, supply its base URL and model explicitly. Native DeepSeek and compatible-service acceptance are separate claims. Tool shell processes do not inherit environment credentials. File tools reject traversal/symlink escapes from cwd, read/write at most 128 KiB, and shell results retain the last 64 KiB per stream. Shell execution has sandbox-user authority and is not confined by file-tool path rules.

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

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

No provider has a passing run recorded for this template.

</details>

## Secondary development

```bash
python3 scripts/check_template.py deepseek-harness
python3 -m pytest -q deepseek-harness/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` controls the model acceptance command budget (default 600 seconds, range 1–1800). L0 does not call a model. `E2E_REQUIRE_LLM=1` forces real coding acceptance. L3 uses target setup diagnostics, seeds failing source/tests, verifies changed source/new artifacts/unchanged tests through target file APIs, then independently executes unittest and held-out calculations. A missing key is not acceptance.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py deepseek-harness` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/deepseek-harness.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### 2026-10-20 full step checkpoint: template1.1.1

[Real current-version steps](evidence/express-2026-10-20T154957Z.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T154957Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
