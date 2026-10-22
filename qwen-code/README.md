# Qwen Code

[中文](README.zh-CN.md)

## What it does

Runs the pinned Qwen Code CLI as a non-interactive coding agent, with named HTTP commands for coding, installation diagnostics and Python execution. The template is experimental; the acceptance levels below describe what was actually checked.

## Stack

Alibaba FC generation-2 base, Python from the platform, Node.js 22 when the base does not provide Node >=22, `@qwen-code/qwen-code@0.23.0`, and the pinned in-sandbox server in [Dockerfile](Dockerfile). No extra DashScope or OpenAI Python library is needed by the CLI.

## Problem solved

Provides a reproducible headless CLI rather than requiring browser OAuth or configuring each sandbox by hand. The wrapper explicitly selects OpenAI-compatible authentication and rejects a missing key before starting the agent.

## Quick start (CLI)

The examples use the current Express CLI: `abx create <template-id> --detach` prints the sandbox ID; `abx kill <sandbox-id>` cleans it up. Named commands use `abx run`. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

Build/register with Express credentials and an available Docker daemon:

```bash
abx template install ./qwen-code --registry-type local
abx create <template-id> --detach --env OPENAI_API_KEY="$OPENAI_API_KEY"
abx run <sandbox-id> qwen_version
abx run <sandbox-id> qwen_setup_check
abx run <sandbox-id> qwen --json-args '{"prompt":"Fix the existing calculator.py and write REPORT.md explaining the fix; run its tests","max_turns":20,"yolo":true,"command_timeout":300}'
```

Upload the project before invoking the agent. `yolo=true` approves all agent tool actions; use it only for a sandbox and project you intend the agent to modify. The default is `false`. Results are buffered JSON text emitted by Qwen, not live events.

## Quick start (Python SDK)

Use `agent-sandbox-client` with the paired server; see [source installation](../docs/python-client-installation.md) if the matching version is unpublished. The Python import remains `agent_sandbox`.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600,
        envs={"OPENAI_API_KEY": os.environ["OPENAI_API_KEY"]})
    try:
        print(await sb.run("qwen_version"))
        await sb.files.write("/home/user/app/calculator.py", "def add(a,b):\n    return a-b\n")
        print(await sb.run("qwen", prompt="Fix calculator.py and write REPORT.md explaining the fix; run its tests",
            max_turns=20, yolo=True, command_timeout=300, timeout=330))
        print((await sb.commands.run("cd /home/user/app && python3 -c 'from calculator import add; assert add(2,3)==5'")).exit_code)
    finally:
        await sb.kill()

asyncio.run(main())
```

`timeout=330` controls the client's HTTP wait; `command_timeout=300` limits the owned agent process group. A client timeout does not guarantee cancellation. Use process APIs for background jobs and cancellation. If `ABX_SERVER_TOKEN` is configured, use `sb.server_at(9000, token=os.environ["ABX_SERVER_TOKEN"]).commands.run(...)` for named commands.

## Quick start (HTTP POST)

Use the port-9000 URL returned by `sb.network.get_url(9000)`. On Express, include its gateway `X-Access-Token` in addition to any separately configured server `Authorization: Bearer` token. Omit a header only if that layer does not require authentication.

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/qwen" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $SANDBOX_GATEWAY_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  -d '{"prompt":"Fix calculator.py and write REPORT.md explaining the fix; run its tests","max_turns":20,"yolo":true,"command_timeout":300}'
```

The request is the direct argument object, without an `args` wrapper. Response: `{"result":"<buffered Qwen JSON output>"}`. `POST /commands/qwen_version` with `{}` returns `{"result":"0.23.0"}`. Missing or mistyped arguments return 400; missing authentication returns 401; an unknown command returns 404; command validation, missing keys/CLI, upstream nonzero exits and execution deadlines return 500 with `{"error":"...","type":"RuntimeError"}` or `ValueError`. Error and success text redact secret environment values.

## Command reference

| Command | Parameters | Result / upstream |
| --- | --- | --- |
| `qwen` | `prompt: str` required, nonempty; `max_turns: int=100` (1–1000); `model: str=""` uses `OPENAI_MODEL`; `cwd: str=""` uses workspace; `command_timeout: int=600` (1–1800 seconds); `yolo: bool=false` | String from `qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`; adds `--model MODEL`, `--yolo` when supplied |
| `qwen_version` | None | Real `qwen --version` string, no key needed |
| `qwen_setup_check` | None | Object with installed/version, pin, key/model/base-url presence and settings-file existence/JSON validity; never returns settings values or writes files |
| `run` | `script: str="main.py"` | Python stdout; compatibility command with 120-second deadline |

`cwd` can be absolute or relative to `WORKSPACE` and must exist. Named commands use argv lists without shell interpolation. Coding can change files and run shell commands through the upstream agent.

This Linux runtime drains both output pipes and keeps its session leader unreaped until owned process-group cleanup. Success, nonzero exit and deadline paths all stop that group before returning.

## Configuration

| Variable | Meaning |
| --- | --- |
| `OPENAI_API_KEY` | Primary model key, required in the command-server process |
| `DASHSCOPE_API_KEY` | Fallback model key when `OPENAI_API_KEY` is empty; mapped only in the child process |
| `OPENAI_BASE_URL` | Default `https://dashscope.aliyuncs.com/compatible-mode/v1`; override for a compatible endpoint |
| `OPENAI_MODEL` | Default `qwen3-coder-plus`; explicit command `model` wins |
| `WORKSPACE` | Default `/home/user/app` |
| `ABX_SERVER_TOKEN` | Optional independent HTTP server authentication token; never the model key |

Diagnostics inspect `~/.qwen/settings.json` and `<workspace>/.qwen/settings.json` without altering contents or permissions. Normal upstream coding may maintain its own runtime cache. Upstream [model-provider configuration](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md) and [headless usage](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md) describe compatibility; each endpoint/model still requires a real acceptance run. Do not enable API logging with secrets in public artifacts.

## Resources

2 vCPU, 4096 MB RAM, port 9000; outbound access to the selected model service. Generation 2 runs as non-root `user`. No Docker-in-Docker or elevated capabilities are required by Qwen.

## Verified

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.1.1; steps build, official READY, CLI/SDK basic smoke, independent cleanup; model phase not run in this step receipt | [2026-10-19](evidence/express-2026-10-19T184254Z.json) |
| alicloud-express | 2.1.1; actual CI image, official READY, Python Sandbox.create, CLI/SDK and17 strict real-model assertions;0 FAIL/0 SKIP; independent sandbox/template/registry cleanup | [image](evidence/express-2026-10-20.json), [model](evidence/model-image-2026-10-20T073522Z.json) |

The changed workspace profile is verified in real generated steps. Prior receipts retain historical scope; basic smoke does not establish model acceptance.


Model: qwen3.8-flash over the explicitly configured OpenAI-compatible endpoint.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

No provider has a passing run recorded for this template.

Local CLI installation/version and HTTP regression results are recorded in the [verification record](../.agents/evidence/verify/2026-10-16-qwen-code-v2.md). L1 image build and L2 Express are blocked by the unavailable Docker daemon. A local model run cannot establish cloud/image acceptance.

</details>

## Secondary development

Extend `commands.py` with typed `@command` functions; keep `start()` under the main guard. Preserve the `qwen` and `run` names and document new arguments in both languages. Pin CLI/server versions. Inspect [design](../docs/design/qwen-code.md) before changing runtime behavior.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py qwen-code` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Read [contributor instructions](../CONTRIBUTING.md) and [specification](../docs/template-spec.md). Run `python3 scripts/check_template.py qwen-code`, `python3 -m pytest -q qwen-code/test_commands.py`, and `python3 scripts/run_local_e2e.py`. Local checks skip a missing CLI unless `E2E_REQUIRE_CLI=1`; a skip never proves runtime acceptance. For coding acceptance run the server with compatible key/base URL/model, then `E2E_REQUIRE_CLI=1 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python3 qwen-code/e2e_test.py`. The test changes existing source, retrieves a new report and exact artifact via files APIs, then runs independent tests and held-out calculations through the target shell API. It removes only its unique test project. Preserve engineering records; do not commit secrets or failed provider-pass JSON.

## Issues

Track template work in [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26). File SDK/server bugs in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and CLI bugs in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and actual failed gates.

## License

Apache-2.0 for this template. Qwen Code retains its [upstream license](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE).

### 2026-10-20 full step checkpoint: template2.1.1

[Real current-version steps](evidence/express-2026-10-20T155502Z.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155502Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
