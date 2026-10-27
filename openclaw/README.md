# openclaw

[简体中文](README.zh-CN.md)

## What it does

Runs an authenticated native OpenClaw gateway with an owned background lifecycle and optional text conversations. Configure your own compatible model endpoint, API key and model ID; summarize expenses and continue a conversation using its returned session ID.

## Stack

The default recipe uses the Alibaba FC generation-2 base, non-root `user`, and the published `agent-sandbox-server==0.4.0a6` package.

OpenClaw `2026.10.4`, Node.js `24.16.0`, application port 9000 and optional gateway port 18789.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## Problem solved

Summarize a small expense list through the native gateway, ask follow-up questions with conversation context, and manage the gateway without a system service.

## Quick start (CLI)

Install the CLI/Python client and configure your platform (Sandbox API key, connection address and build image registry) using the [usage guide](../docs/using-templates.md#installation), then set the separate model/application credentials below. Launching the public recipe does not require a repository checkout.

Use an independent `OPENCLAW_GATEWAY_TOKEN` for gateway authentication. For model conversations, set all three `OPENCLAW_MODEL_*` variables below; legacy `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` alone do not configure this workflow. The upstream must support OpenAI Chat Completions. No vendor OAuth login is needed for this explicit API-key workflow. Gateway lifecycle alone remains available without model settings. Keep `bind="loopback"`; the named chat command reaches the gateway internally through application port 9000.

Replace every `<...>` placeholder with your own value; use an exact model ID available to your account. Set secrets in your own terminal or secret manager, never in the image, YAML or public logs. Configure these variables **before** launch; later host changes do not reconfigure the running application.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENCLAW_GATEWAY_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export OPENCLAW_MODEL_API_KEY='<your-model-api-key>'
export OPENCLAW_MODEL_BASE_URL='<your-chat-completions-api-base-including-v1-if-required>'
export OPENCLAW_MODEL='<your-exact-model-id>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//openclaw --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` is the sandbox lifetime in seconds; `command_timeout`/`timeout_s` limits one task, while `ABX_HTTP_TIMEOUT`/SDK `timeout` controls client waiting. These are separate limits.

Launch starts this instance's application; do not create a second sandbox or second server. For OpenSandbox, follow its [setup](../docs/using-templates.md#cli-sdk-and-http) and set `ABX_PROVIDER=opensandbox`; the Python examples below read that same choice.

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_start --json-args '{"bind":"loopback","command_timeout":60}'
abx run "$SANDBOX_ID" gateway_health
abx run "$SANDBOX_ID" gateway_status
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_chat --json-args '{"prompt":"Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total."}'
# Copy session_id from the result to continue this conversation.
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" gateway_chat --json-args '{"prompt":"Remove the train from the previous expenses. Return the same JSON fields.","session_id":"<returned-session-id>"}'
abx run "$SANDBOX_ID" gateway_stop
```

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('gateway_start', bind='loopback', command_timeout=60))
            print(await client.commands.run("gateway_health"))
            first = await client.commands.run("gateway_chat", prompt="Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total.")
            print(first)
            print(await client.commands.run("gateway_chat", prompt="Remove the train from the previous expenses. Return the same JSON fields.", session_id=first["session_id"]))
        finally:
            try:
                await client.commands.run("gateway_stop")
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use the [direct HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserving gateway headers, URL path/query and the independent application token. Send `POST /commands/gateway_start` with `Content-Type: application/json` and this direct argument object, without an `args` wrapper:

```json
{
  "bind": "loopback",
  "command_timeout": 60
}
```

The response is `{"result": ...}`; see the command reference for its actual content type. Model text varies. Set the HTTP wait to at least 420 seconds; the command execution deadline is separate, and disconnecting does not guarantee remote cancellation. Authentication failures return 401, invalid argument types 400, and execution errors an error response. If a result includes `exit_code`, also check that it is zero.

### Export files and cleanup

After an HTTP start, call authenticated `POST /commands/gateway_health` with `{}`, then `POST /commands/gateway_stop` with `{}`. Finally delete the sandbox:

```bash
abx kill "$SANDBOX_ID"
```

`close()`/`aclose()` only close client connections; they do not delete the sandbox. Prepared templates/images in the launch journal can remain for reuse; remove only your own exact resources when no longer needed.

### Model selection and extending the conversation

To switch model, endpoint or API key, change the three `OPENCLAW_MODEL_*` exports and launch a new instance. Existing instances retain their startup environment. `gateway_stop` removes its temporary gateway state and conversation history; reusing a session ID after restart starts fresh. A new/omitted session ID creates a separate conversation. Keep one session ID per application conversation thread.

The example should yield count 3 / total 51.30, then count 2 / total 36.30. Parse the returned `text` as JSON and check its fields in your application; model output can vary. Extend this by passing invoice CSV text and a schema, keeping independent arithmetic checks. This text-only template disables tools, channels, browser/control UI and nested Docker; it does not provision Slack or another messaging integration.

Direct HTTP business calls use `POST /commands/gateway_chat` with `{"prompt":"Summarize taxi 12.50, lunch 23.80 and train 15.00. Return only JSON with integer count and two-decimal string total."}`. Reuse `result.session_id` in a second call with `{"prompt":"Remove the train from the previous expenses. Return the same JSON fields.","session_id":"<returned-session-id>"}`. Stop the gateway after use. The native upstream endpoint is [OpenClaw Chat Completions](https://docs.openclaw.ai/gateway/openai-http-api); this command uses it internally, so no public gateway forwarding is needed.

## Command reference

| Command | Parameters (`prompt` required for chat; others optional) | Return and upstream behavior |
|---|---|---|
| `gateway_start` | `port: int=18789` (1024..65535 except 9000); `bind: str="loopback"` (`loopback` or `lan`); `command_timeout: int=60` (1..120 seconds) | `{running:true,healthy:true,url,bind}` after `openclaw gateway run --allow-unconfigured --bind <bind> --auth token --port <port>` and authenticated health. Repeating matching arguments checks health; changing a running gateway's port/bind requires stop first. |
| `gateway_chat` | `prompt: str` (1..65536 UTF-8 bytes, nonblank); `session_id: str=""` (empty or 1..80 ASCII letters/digits/underscore/hyphen); `command_timeout: int=180` (1..300 seconds) | `{session_id,text}` from the native gateway `/v1/chat/completions`, agent `openclaw/default`, stable per-conversation `user`. Starts the owned gateway if needed. |
| `gateway_status` | none | `{running,owned,url}` for this server's handle only; never implies health. |
| `gateway_health` | `command_timeout: int=20` (1..120 seconds) | `{healthy:true,url}` only after `openclaw gateway health --json --timeout <milliseconds>` with the isolated config/token environment; otherwise raises. |
| `gateway_stop` | `command_timeout: int=10` (1..120 seconds) | `{running:false,owned:false}`; sends TERM to the owned process group, then KILL on timeout with at most five additional seconds for reaping. Idempotent. |

The application owns one gateway; `gateway_stop` stops that owned process. Loopback serves internal clients only. Forwarding needs lan binding and an explicit trusted-proxy configuration supplied before launch; never derive trust from X-Forwarded-For.

## Configuration

On Linux, each short-lived gateway health RPC drains its output and keeps its leader unreaped until owned-group cleanup, including success, error and timeout. This never stops the separate long-running gateway group. A process that deliberately escapes with setsid is outside that group.

| Variable | Default | Meaning |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | empty | Required for gateway start; inject via sandbox environment, never a command parameter. It is passed in the child environment and referenced by name in isolated config, never returned or included in argv. |
| `OPENCLAW_TRUSTED_PROXIES` | empty | Explicit verified proxy IP/CIDR list for forwarded access; max16/2048bytes, no unrestricted/multicast networks. |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the template launch; separate from model and gateway credentials `/health` does not require the application token. |
| `OPENCLAW_MODEL_API_KEY` | empty | Explicit compatible-model key, referenced by environment name in native config; never guessed from legacy vendor credentials. |
| `OPENCLAW_MODEL_BASE_URL` | empty | Explicit HTTP(S) API base, including `/v1` when required; no embedded credentials/query/fragment. |
| `OPENCLAW_MODEL` | empty | Exact model ID available on that endpoint; all three model settings must be supplied together. Native catalog declares 128000 context / 4096 output tokens; choose a model supporting these limits. |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | empty | Retained legacy environment names; not used as fallback for the explicit conversation workflow. |

The gateway uses a private temporary state/config directory, disables model tools and browser/control UI and skips channels. A client timeout/disconnection does not guarantee an accepted native turn is cancelled; stop the owned gateway or destroy the sandbox to end remaining work. Calls serialize on the gateway lifecycle lock; a waiting stop may wait for the current bounded request. Local user OpenClaw configuration is not modified. Gateway logs are discarded to avoid exposing upstream credential-bearing output through the command API. Diagnose upstream configuration in a separate controlled session; do not publish raw logs.

## Resources

2 vCPU, 4096 MB RAM, application port 9000, non-root `user`. Working directory: `/home/user/app`. Disk capacity and lifetime depend on the selected platform. Internal gateway health checks do not require a model service.

## Contributing

To develop the template, read [CONTRIBUTING](../CONTRIBUTING.md) and the [design](../docs/design/openclaw.md).

## Issues

Track this work in [awesome-templates#20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20). File runtime/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), using `[templates]` in the title. Upstream reference: [Gateway CLI](https://docs.openclaw.ai/cli/gateway); version and options are also checked against the installed `2026.10.4` binary.

## License

[Apache-2.0](../LICENSE). OpenClaw retains its upstream license and attribution.
