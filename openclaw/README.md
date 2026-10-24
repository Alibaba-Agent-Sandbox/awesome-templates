# openclaw

[简体中文](README.zh-CN.md)

## What it does

Runs an authenticated OpenClaw WebSocket gateway as an owned background process. Named commands start, inspect, check and stop it without installing a system service. Gateway readiness proves the runtime works; it does not prove a coding agent or model response.

## Stack

- Alibaba FC base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (deployment resolves the placeholders).
- Node.js `24.16.0`, npm package `openclaw@2026.10.4`. The upstream package requires Node >=24.16.0; the base image Node 20 is insufficient.
- `agent-sandbox-server` pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`, unless deployment injects a wheel.
- Non-root `user`, work directory `/home/user/app`, generation 2, HTTP server port 9000 and optional gateway port 18789.

## Problem solved

A gateway is a long-lived server. Running `openclaw start` synchronously is neither the correct gateway command nor a usable named command lifecycle. This template runs `openclaw gateway run`, waits for an authenticated WebSocket health RPC, then returns while retaining its process handle. It never trusts a PID file or uses upstream `--force` to reclaim a port.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./openclaw --workflow application --yes
abx run <sandbox-id> gateway_status --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('gateway_status'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/gateway_status`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"running": false, "owned": false, "url": null}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters (all optional) | Return and upstream behavior |
|---|---|---|
| `gateway_start` | `port: int=18789` (1024..65535 except 9000); `bind: str="loopback"` (`loopback` or `lan`); `command_timeout: int=60` (1..120 seconds) | `{running:true,healthy:true,url,bind}` after `openclaw gateway run --allow-unconfigured --bind <bind> --auth token --port <port>` and authenticated health. Repeating matching arguments checks health; changing a running gateway's port/bind requires stop first. |
| `gateway_status` | none | `{running,owned,url}` for this server's handle only; never implies health. |
| `gateway_health` | `command_timeout: int=20` (1..120 seconds) | `{healthy:true,url}` only after `openclaw gateway health --json --timeout <milliseconds>` with the isolated config/token environment; otherwise raises. |
| `gateway_stop` | `command_timeout: int=10` (1..120 seconds) | `{running:false,owned:false}`; sends TERM to the owned process group, then KILL on timeout with at most five additional seconds for reaping. Idempotent. |
| `gateway` | `action: str="start"` (`start`, `status`, `health`, `stop`); `port: int=18789`; `bind: str="loopback"`; `command_timeout: int=60` | Compatibility alias to the corresponding command. Port/bind apply only to start; command_timeout applies to start/health/stop. It no longer forwards arbitrary main commands to the CLI. |

Health probes allow a bounded cleanup margin after their execution deadline for group termination, reaping and pipe-reader shutdown; failed startup also cleans its owned gateway. The server owns a single gateway. No systemd/service installation is required. Abrupt server death loses the in-memory handle: this implementation deliberately will not adopt or kill an unknown process after restart. Destroying the sandbox cleans up its processes. State is temporary and removed by stop; configure persistent upstream agents separately rather than assuming this smoke runtime preserves sessions.

### Version2.1 explicit proxies and SDK acceptance

The default loopback gateway needs no proxy configuration. To access the gateway
through a provider-forwarded port, explicitly choose `bind="lan"` and configure
`OPENCLAW_TRUSTED_PROXIES` before the named-command server starts. It accepts at
most16 comma-separated explicit IPs/CIDRs and2048UTF-8 bytes; invalid/empty,
unrestricted and multicast networks fail. Addresses are canonicalized/deduplicated.
Use independently verified provider proxy addresses, never values supplied in
X-Forwarded-For. Empty keeps upstream defaults. No global proxy trust is added;
gateway token authentication remains mandatory.

Actual2.0.1 authenticated native RPC and forwarded `/healthz` passed, while
forwarded `/readyz` returned403. The pinned upstream rejects unattributed proxy
headers. Version2.1 writes only explicit operator settings to the owned temporary
configuration; it preserves upstream source/auth checks and caller configuration.
Liveness requires HTTP200 with `ok=true`; readiness requires HTTP200 with
`ready=true`. Startup503 may be polled within a fixed bound.

From the repository root, the CLI recipe invokes the companion SDK controller.
It borrows a fresh owned sandbox, observes its own nonce-protected probe's kernel
peer on9012, explicitly supplies that exact `/32` or `/128` test address to its
own9010server, starts/authenticates/stops the real gateway and independently
checks forwarded18789liveness/readiness. It never derives trust from forwarded
header values, returns tokens/raw proxy addresses or destroys the caller sandbox.
Own processes/listeners/state are cleaned up; the caller still owns final sandbox
destruction. No model credential or model/channel claim is involved. The Python
example explicitly starts9010 so create-time environment is not mistaken for a
prewarmed9000process configuration.

## Configuration

On Linux, each short-lived gateway health RPC drains its output and keeps its leader unreaped until owned-group cleanup, including success, error and timeout. This never stops the separate long-running gateway group. A process that deliberately escapes with setsid is outside that group.

| Variable | Default | Meaning |
|---|---|---|
| `OPENCLAW_GATEWAY_TOKEN` | empty | Required for gateway start; inject via sandbox environment, never a command parameter. It is passed in the child environment and referenced by name in isolated config, never returned or included in argv. |
| `OPENCLAW_TRUSTED_PROXIES` | empty | Explicit verified proxy IP/CIDR list for forwarded access; max16/2048bytes, no unrestricted/multicast networks. |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials `/health` does not require the application token. |
| `ABX_SERVER_PORT` | 9000 | Local `python commands.py` HTTP port; cloud start command explicitly uses 9000. |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | empty | Optional upstream model credentials; gateway health does not need them. No model call is implemented or validated by these commands. |

The gateway uses a private temporary state/config directory, disables browser/control UI and skips channels. Local user OpenClaw configuration is not modified. Gateway logs are discarded to avoid exposing upstream credential-bearing output through the command API. Diagnose upstream configuration in a separate controlled session; do not publish raw logs.

## Resources

2 vCPU, 4096 MB RAM; approximately 10G Express rootfs. No Docker or extra capabilities are required for the gateway itself. Nested Docker-based agent sandboxing is outside this template's verified slice.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical2.0.1verification


| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.0.1; steps build, official READY, CLI/SDK basic smoke, independent cleanup; current-version model acceptance NOT_RUN | [2026-10-19](evidence/express-2026-10-19T183726Z.json) |

The changed workspace profile is verified in real generated steps. Prior receipts retain historical scope; basic smoke does not establish model acceptance.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

Read [design](../docs/design/openclaw.md). Keep upstream versions pinned, command argv as lists, token values in environment, and owned process handles rather than PID files. Add functional regressions for lifecycle changes and keep both READMEs current. Adding agent/model commands requires a separate contract and real-model acceptance.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py openclaw` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md) and [template spec](../docs/template-spec.md). Run `python3 scripts/check_template.py openclaw` and `python3 -m pytest openclaw/test_commands.py`. For local HTTP smoke, start `python3 openclaw/commands.py` and run `python3 openclaw/e2e_test.py` with matching `E2E_BASE_URL`, server auth and gateway token. A synthetic random gateway token suffices for a real local gateway test; a model key is unnecessary. Keep `tested_on: []` until provider evidence passes. Required image/cloud acceptance must remain explicit if unavailable.

## Issues

Track this work in [awesome-templates#20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20). File runtime/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), using `[templates]` in the title. Upstream reference: [Gateway CLI](https://docs.openclaw.ai/cli/gateway); version and options are also checked against the installed `2026.10.4` binary.

## License

[Apache-2.0](../LICENSE). OpenClaw retains its upstream license and attribution.

### 2026-10-20 authenticated full step checkpoint

[Real2.0.1 steps](evidence/express-2026-10-20T161954Z.json) and [original complete HTTP controller](evidence/verification-steps-2026-10-20T161954Z.json) passed official READY, Python SDK creation, all CLI/SDK smoke and 11 HTTP PASS/0 FAIL/1 model SKIP in703.799s. A per-run generated gateway token is supplied only after installers in the private recipe; actual authenticated readiness/health, persistent status, owned stop and stopped-health failure were exercised. Independent sandbox/template and exact private Node-cache object/bucket cleanup passed. No operator/model credential was used; public evidence omits token values. The earlier6/0/2 receipt retains its narrower scope and does not certify gateway lifecycle. [Strict audit and reproduction](../docs/platform-steps.md).

### Current2.1.0 full-HTTP step repeat

After integrating the new explicit proxy configuration and4GiB profile, the [current2.1.0 step receipt](evidence/express-2026-10-20T165241Z.json) and [unchanged full HTTP controller](evidence/verification-steps-2026-10-20T165241Z.json) passed11/0/1(model SKIP) in525.594s. Official READY, actual CLI/Python SDK, authenticated gateway lifecycle and independently observed sandbox/template/private-cache absence passed. The current whole-manifest-bound strict audit accepts this source; the old2.0.1 full receipt remains historical. Separate current native SDK/forwarded health and image proof above is preserved.
