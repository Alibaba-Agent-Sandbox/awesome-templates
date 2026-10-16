# DeepSeek coding harness

## What it does

Run a repository-owned coding agent using the official DeepSeek Chat Completions function-call protocol. Each turn executes read_file, write_file, list_files or run_shell and returns tool results to the model until a final answer.

## Stack

Python 3.13; `httpx==0.28.1`; Agent Sandbox server. No third-party agent CLI.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://api-docs.deepseek.com/guides/tool_calls/)

## Problem solved

Expose a typed, bounded coding task through one named command; inject model credentials at sandbox creation.

## Quick start (CLI)

```bash
abx template install alibaba-agent-sandbox/awesome-templates//deepseek-harness
abx create --template <template-id> --env DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"
abx run <sandbox-id> deepseek --arg prompt="Inspect this project and fix the failing calculation"
```

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client`. See [installation](../docs/python-client-installation.md) for availability and pinned source installation.

```python
import asyncio
import os
from agent_sandbox import Sandbox

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

No provider has a passing run recorded for this template.

## Secondary development

```bash
python3 scripts/check_template.py deepseek-harness
python3 -m pytest -q deepseek-harness/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` controls the model acceptance command budget (default 600 seconds, range 1–1800). L0 does not call a model. `E2E_REQUIRE_LLM=1` forces real coding acceptance. L3 uses target setup diagnostics, seeds failing source/tests, verifies changed source/new artifacts/unchanged tests through target file APIs, then independently executes unittest and held-out calculations. A missing key is not acceptance.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/deepseek-harness.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).
