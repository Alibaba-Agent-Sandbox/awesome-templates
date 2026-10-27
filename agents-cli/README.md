# agents-cli

Pinned Codex and Qwen Code behind a restricted local Agents HTTP API.

## What it does

Installs `@openai/codex@0.162.1` and `@qwen-code/qwen-code@0.23.0`. The server
exposes a version diagnostic, explicit native Codex profile preparation and six session/runtime routes. Callers create a
session, submit messages and poll its items. `X-Agent-Sandbox-Local: 1` labels the
local Agents implementation; it does not mean an OpenAI hosted Agents service.

Both direct startup and the configured `agent-sandbox-server serve` command load
[server-policy.json](./server-policy.json). Shell, files, generic process APIs,
model listing and all other Agents routes are disabled. The agent subprocess
still has its configured workspace permissions; closing HTTP file/shell routes
does not remove the upstream CLI's tools.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

Codex CLI `0.162.1`, Qwen Code `0.23.0`, Node.js `24.16.0`, and the restricted local Agents API policy.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Use an installed tool in an isolated sandbox, submit work through CLI, Python or HTTP, then export the files. Configure model and cloud-sandbox credentials separately.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

Select either `qwen-code` (Chat Completions) or `codex` (Responses). Set `OPENAI_API_KEY`, `OPENAI_BASE_URL` and `OPENAI_MODEL` for your explicitly authorized model service. API-key use does not start OAuth or inherit a host account. Before a Codex session, call `agents_configure_codex`; it explicitly creates a native Responses profile from the startup endpoint, references `OPENAI_API_KEY` by name and disables WebSockets. It never writes the key or overwrites a different existing profile. A Qwen session uses the startup Chat endpoint directly. The same endpoint must support both protocols if you use both adapters in one instance; otherwise launch separate instances with their matching configuration.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENAI_API_KEY='<your-model-or-vendor-key>'
export OPENAI_BASE_URL='<your-model-api-base-including-v1-if-required>'
export OPENAI_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//agents-cli --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

Use the session API below for an actual coding task. The version diagnostic and profile preparation alone do not run the model.

```bash
abx run "$SANDBOX_ID" agents_version
# For Codex sessions, explicitly prepare the native Responses profile:
abx run "$SANDBOX_ID" agents_configure_codex
# Select the adapter for the complete Python example:
export AGENTS_ADAPTER=qwen-code
# Or: export AGENTS_ADAPTER=codex
```

The task creates `generated_hello.py` and `GENERATED_REPORT.md` in `/home/user/workspace`. The example explicitly enables the required editing/tools; use an owned disposable sandbox. The SDK and HTTP examples are alternative ways to submit the same task; choose one.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

Connect to the application started by launch and resolve its gateway with the SDK. This Python example submits the same coding task and polls output within a bounded wait. The restricted application policy has no generic file/shell HTTP routes; inspect the files afterward through provider `abx exec`/`download`.

```python
import asyncio
import os
import time
from pathlib import Path
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        occupied = {key.lower() for key in headers}
        token = os.environ["ABX_SERVER_TOKEN"]
        if "authorization" not in occupied:
            headers["Authorization"] = "Bearer " + token
        if "x-access-token" not in occupied:
            headers["X-Access-Token"] = token
        if {"authorization", "x-access-token"}.issubset(occupied):
            raise ValueError("Gateway occupies both application authentication headers")
        base = httpx.URL(endpoint)
        def url(path):
            return base.copy_with(path=base.path.rstrip("/") + path)
        async with httpx.AsyncClient(headers=headers, timeout=60) as http:
            adapter = os.environ.get("AGENTS_ADAPTER", "qwen-code")
            if adapter not in ("qwen-code", "codex"):
                raise ValueError("AGENTS_ADAPTER must be qwen-code or codex")
            if adapter == "codex":
                response = await http.post(url("/commands/agents_configure_codex"), json={})
                response.raise_for_status()
            response = await http.post(url("/v1/agents/sessions"), json={
                "adapter": adapter,
                "agent": {"model": os.environ["OPENAI_MODEL"], "permissions": "full_access"},
                "environment": {"type": "self_hosted",
                                "workspace_directory": "/home/user/workspace"},
            })
            response.raise_for_status()
            session = response.json()["id"]
            path = "/v1/agents/sessions/" + session
            response = await http.post(url(path + "/events"), json={
                "events": [{"type": "agent.session.input.message", "input": [
                    {"role": "user", "content": [{"type": "input_text", "text":
                     "Create generated_hello.py that prints exactly Hello from the sandbox, "
                     "and GENERATED_REPORT.md explaining the program. Preserve unrelated files."}]}]}]
            })
            response.raise_for_status()
            deadline = time.monotonic() + 420
            while time.monotonic() < deadline:
                response = await http.get(url(path))
                response.raise_for_status()
                state = response.json()
                if state.get("error") or state.get("status") == "failed":
                    raise RuntimeError("Agent session failed; inspect private diagnostics")
                response = await http.get(url(path + "/items"))
                response.raise_for_status()
                items = response.json()["data"]
                if state.get("status") == "idle" and items:
                    print(items)
                    Path("generated_hello.py").write_bytes(await sb.files.read_bytes("/home/user/workspace/generated_hello.py"))
                    Path("GENERATED_REPORT.md").write_bytes(await sb.files.read_bytes("/home/user/workspace/GENERATED_REPORT.md"))
                    break
                await asyncio.sleep(1)
            else:
                raise TimeoutError("Destroy your owned sandbox to stop the task")
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

The read-only named diagnostic is `POST /commands/agents_version`, with body `{}` and response `{"result":"codex 0.162.1; qwen-code 0.23.0"}`. Actual coding uses the Agents session API below, rather than an invented named coding command.

Set `Content-Type: application/json`.

Resolve the port-9000 endpoint using the [direct HTTP flow](../docs/using-templates.md#cli-sdk-and-http), preserving gateway headers and URL path/query, and add the independent application token. Submit the same task with these session requests:

For Codex, first send `POST /commands/agents_configure_codex` with `{}`; expect `{"result":{"configured":true,"wire_api":"responses","credential_written":false}}`.

1. `POST /v1/agents/sessions`:

```json
{
  "adapter": "qwen-code",
  "agent": {
    "model": "<same-model-as-OPENAI_MODEL>",
    "permissions": "full_access"
  },
  "environment": {
    "type": "self_hosted",
    "workspace_directory": "/home/user/workspace"
  }
}
```

Use `"adapter":"codex"` for native Codex after profile preparation, or keep `qwen-code`. Replace the model placeholder with the exact ID for the selected protocol. Expect `200`; save response `id` as `<session-id>`.

2. `POST /v1/agents/sessions/<session-id>/events`:

```json
{
  "events": [
    {
      "type": "agent.session.input.message",
      "input": [
        {
          "role": "user",
          "content": [
            {
              "type": "input_text",
              "text": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files."
            }
          ]
        }
      ]
    }
  ]
}
```

Expect `202` for queued work, not completion. Poll `GET /v1/agents/sessions/<session-id>` and `GET /v1/agents/sessions/<session-id>/items?limit=100&order=asc` with a bounded 420-second wait; stop on `error`/`failed`. Once output exists and status returns to `idle`, check the actual files below; `idle` alone does not prove successful edits. Cancel/delete routes are disabled; destroy your owned sandbox to stop work or end the session.

### Continuing and switching models

Post a further input-message event to the same session ID to resume the native conversation. Wait for new output items and a return to idle, then independently inspect its files; idle alone does not prove success. Use a new session to start an independent conversation. Select another authorized model on the same endpoint/key in a new session's `agent.model`. To change endpoint or key, change the startup exports and launch a new instance; later host exports do not reconfigure an existing server. A different existing Codex profile is preserved: choose a fresh `CODEX_HOME` before launch instead of overwriting it.

### Export files and cleanup

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/workspace/generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/workspace/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

Expected program output: `Hello from the sandbox`. Inspect actual files before using them; a successful-looking model response does not guarantee files exist. Files do not automatically update the template or your machine; export them before deleting the sandbox.

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

## Command reference

| Command | Parameters | Returns | Execution |
|---|---|---|---|
| `agents_configure_codex` | None; `{}` | `{configured:true,wire_api:"responses",credential_written:false}` | Explicitly creates CODEX_HOME/config.toml (0600); same profile is idempotent, different existing/symlinked config fails without overwrite. Uses startup OPENAI_BASE_URL and environment key reference; no model/login call. |
| `agents_version` | None; `{}` | Buffered string | Actual `codex --version` and `qwen --version`, each with a 20-second deadline; missing/wrong version raises an error without raw CLI output. |

| Enabled route | Purpose |
|---|---|
| `GET /commands`, `POST /commands/agents_version`, `POST /commands/agents_configure_codex` | Discover/run diagnostics and explicit profile preparation |
| `POST /v1/agents/sessions` | Create a session; `adapter` selects `codex` or `qwen-code`; the default runtime is Codex |
| `GET /v1/agents/sessions`, `GET /v1/agents/sessions/{id}` | List/reconnect sessions |
| `POST /v1/agents/sessions/{id}/events` | Queue messages |
| `GET /v1/agents/sessions/{id}/items` | Poll output items |
| `GET /v1/agents/runtimes` | Inspect declared, implemented and installed runtimes |

Named-command results are buffered rather than streamed. `cwd` must be an existing directory satisfying the template's path constraints. Editing/tool permission allows model actions with the sandbox user's authority. Client disconnect is not a cancellation mechanism.

## Configuration

| Name | Required | Purpose |
|---|---|---|
| `ABX_SERVER_TOKEN` | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |
| `OPENAI_API_KEY` | For compatible model turns | Runtime credential, declared empty; usable by Qwen and compatible Codex setups |
| `CODEX_API_KEY` | Optional Codex alternative | Declared empty; actual authentication support depends on the chosen upstream provider |
| `OPENAI_BASE_URL`, `OPENAI_MODEL` | Provider-dependent | Explicit model endpoint/model; Qwen requires Chat Completions, Codex requires Responses after profile preparation |
| `ABX_AGENTS_STATE_DIR` | No | Native local session persistence directory `/home/user/.agent-sandbox/agents`; destroyed with the instance |
| `CODEX_HOME` | No | Codex state directory, `/home/user/.codex` |
| `WORKSPACE` | No | `/home/user/workspace`; session requests should specify the target workspace explicitly |
| `ABX_SERVER_POLICY_FILE` | Set in image | Path to the shipped policy; the canonical start command also passes `--policy` explicitly |

Changing the policy deliberately changes the public HTTP surface. Keep the shipped
allowlist for this template's documented contract.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/workspace`. Disk capacity and lifetime depend on the selected platform. Model tasks require outbound access to the configured model service and incur that service's charges.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/agents-cli.md).

## Issues

Template/policy integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
Runtime/API defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI deployment defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Apache-2.0; see [LICENSE](../LICENSE). Upstream CLIs retain their own licenses.
