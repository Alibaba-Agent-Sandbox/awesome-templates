# Qwen Code

[中文](README.zh-CN.md)

## What it does

Runs the pinned Qwen Code CLI as a non-interactive coding agent, with named HTTP commands for coding, installation diagnostics and Python execution.

## Stack

Alibaba FC generation-2 base, Python from the platform, Node.js 24.16.0 (fixed release and SHA256 for x86_64/aarch64), `@qwen-code/qwen-code@0.23.0`, and the pinned in-sandbox server in [Dockerfile](Dockerfile). No extra DashScope or OpenAI Python library is needed by the CLI.

## Problem solved

Provides a reproducible headless CLI rather than requiring browser OAuth or configuring each sandbox by hand. The wrapper explicitly selects OpenAI-compatible authentication and rejects a missing key before starting the agent.

## Quick start (CLI)

Install the published CLI and Python client and configure Express using the [usage guide](../docs/using-templates.md#installation). Run from this repository's root with Docker and the provider's image registry configured. Generate an independent application token in your current shell:

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
abx template launch ./qwen-code --workflow application --sandbox-timeout 900 --yes
```

The launch prepares the template, creates the sandbox and starts its application. Copy the returned sandbox ID into `SANDBOX_ID`, then keep the same application token for all three clients:

```bash
export SANDBOX_ID='<sandbox-id>'
abx sandbox command list "$SANDBOX_ID"
abx run "$SANDBOX_ID" qwen_version
abx run "$SANDBOX_ID" qwen_setup_check
```

`qwen_version` returns `0.23.0`. The setup result reports installation and configuration presence without exposing credentials. Neither command needs a model key; these checks do not execute a coding task. For OpenSandbox, follow its setup in the [calling guide](../docs/using-templates.md#cli-sdk-and-http), set `ABX_PROVIDER=opensandbox` before launch and use `provider="opensandbox"` in Python below.

### Run a coding task

Before launching a **new** instance, configure `OPENAI_API_KEY` securely in the launching shell (or `DASHSCOPE_API_KEY` as fallback). The empty key declarations in `template.yaml` inherit those values at launch. The default endpoint/model are DashScope and `qwen3-coder-plus`; edit nonempty `env` defaults in `template.yaml` before launching if your endpoint or workspace differs. Exporting a value later does not reconfigure the running application. The `model` command argument can override the selected model for an individual call.

With a keyed instance's ID and token selected, upload your existing calculator and test files, then ask Qwen to fix it:

```bash
abx upload "$SANDBOX_ID" ./calculator.py /home/user/app/calculator.py
abx upload "$SANDBOX_ID" ./test_calculator.py /home/user/app/test_calculator.py
```

Run the coding call described in the Python SDK section below, then execute independent tests and download the report. CLI 0.4.16 named calls wait up to 30 seconds; use the Python/HTTP client with explicit `timeout=330` for a longer coding task. `command_timeout` bounds server execution and does not extend the CLI wait.

```bash
abx exec "$SANDBOX_ID" -- python3 -m unittest discover -s /home/user/app -p test_calculator.py
abx download "$SANDBOX_ID" /home/user/app/REPORT.md ./REPORT.md
```

Replace the local filenames with your own project files before uploading. `yolo=true` approves all agent tool actions; use it only for a project you intend the agent to modify. It defaults to `false`. The result is buffered Qwen JSON text. Inspect the report and independent test result; a version/setup check does not establish model compatibility or a successful code change.

After finishing the CLI, Python and HTTP examples, delete your owned instance with `abx kill "$SANDBOX_ID"`. The launch journal identifies any prepared template/image retained for reuse; remove those exact owned resources separately when no longer needed.

## Quick start (Python SDK)

Install `agent-sandbox-client` as shown in the [usage guide](../docs/using-templates.md#installation). Connect to the instance launched above; creating another instance does not inherit its running application.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["SANDBOX_ID"], provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=330)
        try:
            print(await client.commands.run("qwen_version"))
            print(await client.commands.run("qwen_setup_check"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

For a keyed instance with your files uploaded, call `await client.commands.run("qwen", prompt="Fix calculator.py and write REPORT.md; preserve and run its tests", max_turns=20, yolo=True, command_timeout=300)` inside the same `try` block. `timeout=330` sets the HTTP wait; `command_timeout=300` bounds the agent process group. Client timeout alone does not cancel work. Closing a borrowed connection does not delete the sandbox.

## Quick start (HTTP POST)

Resolve the endpoint and gateway headers from the same instance. This example preserves gateway authentication, URL path prefixes and query parameters. The application token remains independent:

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["SANDBOX_ID"], provider="alicloud-express")
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        if any(key.lower() == "authorization" for key in headers):
            raise ValueError("Keep gateway Authorization; do not replace it with an application token")
        token = os.environ["ABX_SERVER_TOKEN"]
        headers["Authorization"] = "Bearer " + token
        if not any(key.lower() == "x-access-token" for key in headers):
            headers["X-Access-Token"] = token
        base = httpx.URL(endpoint)
        async with httpx.AsyncClient(timeout=330) as http:
            for name in ("qwen_version", "qwen_setup_check"):
                url = base.copy_with(path=base.path.rstrip("/") + "/commands/" + name)
                response = await http.post(url, headers=headers, json={})
                response.raise_for_status()
                print(response.json())
    finally:
        await sb.close()

asyncio.run(main())
```

`POST /commands/qwen_version` sends `{}` with `Content-Type: application/json` and returns `{"result":"0.23.0"}`. Setup returns an object inside `result`. For a configured coding task, use `POST /commands/qwen` with the direct object below, without an `args` wrapper; its response is `{"result":"<buffered Qwen JSON output>"}`. Missing/mistyped arguments return 400, authentication failure 401, unknown commands 404, and command validation, missing keys/CLI, upstream failures or execution deadlines 500. Errors carry `{"error":"...","type":"RuntimeError"}` or `ValueError`; known secret values are redacted.

```json
{"prompt":"Fix calculator.py, preserve test_calculator.py, write REPORT.md and run tests","max_turns":20,"yolo":true,"command_timeout":300}
```

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
| `OPENAI_API_KEY` | Primary model key for coding tasks; version/setup checks do not require it |
| `DASHSCOPE_API_KEY` | Fallback model key when `OPENAI_API_KEY` is empty; mapped only in the child process |
| `OPENAI_BASE_URL` | Default `https://dashscope.aliyuncs.com/compatible-mode/v1`; edit the manifest default before launch for another compatible endpoint |
| `OPENAI_MODEL` | Default `qwen3-coder-plus`; explicit command `model` wins |
| `WORKSPACE` | Default `/home/user/app` |
| `ABX_SERVER_TOKEN` | Required before application workflow launch; independent of model and gateway credentials |

Diagnostics inspect `~/.qwen/settings.json` and `<workspace>/.qwen/settings.json` without altering contents or permissions. Normal upstream coding may maintain its own runtime cache. Upstream [model-provider configuration](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md) and [headless usage](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md) describe compatibility; each endpoint/model still requires a real acceptance run. Do not enable API logging with secrets in public artifacts.

## Resources

2 vCPU, 4096 MB RAM, port 9000; outbound access to the selected model service. Generation 2 runs as non-root `user`. No Docker-in-Docker or elevated capabilities are required by Qwen.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. This historical smoke does not establish a real-model task or the current launch path.

## Secondary development

Extend `commands.py` with typed `@command` functions; keep `start()` under the main guard. Preserve the `qwen` and `run` names and document new arguments in both languages. Pin CLI/server versions. Inspect [design](../docs/design/qwen-code.md) before changing runtime behavior.

For current source-launch checks, use the [public launch testing guide](../docs/public-launch-testing.md). Historical steps below retain their original inputs and calling paths.

## Contributing

Read [contributor instructions](../CONTRIBUTING.md) and [specification](../docs/template-spec.md). Run `python3 scripts/check_template.py qwen-code`, `python3 -m pytest -q qwen-code/test_commands.py`, and `python3 scripts/run_local_e2e.py`. Local checks skip a missing CLI unless `E2E_REQUIRE_CLI=1`; a skip never proves runtime acceptance. For coding acceptance run the server with compatible key/base URL/model, then `E2E_REQUIRE_CLI=1 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python3 qwen-code/e2e_test.py`. The test changes existing source, retrieves a new report and exact artifact via files APIs, then runs independent tests and held-out calculations through the target shell API. It removes only its unique test project. Preserve engineering records; do not commit secrets or failed provider-pass JSON.

## Issues

Track template work in [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26). File SDK/server bugs in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and CLI bugs in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and actual failed gates.

## License

Apache-2.0 for this template. Qwen Code retains its [upstream license](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE).

### 2026-10-20 full step checkpoint: template2.1.1

[Real current-version steps](evidence/express-2026-10-20T155502Z.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155502Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
