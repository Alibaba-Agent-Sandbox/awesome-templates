# Factory Droid

## What it does

Template1.2.0 adds `droid_byok`: the genuine fixed CLI uses an explicit compatible provider without a Factory account. The existing `droid` Factory-account command remains available. Both use private per-call state and bounded owned process cleanup. Current1.2 native SDK/Express/BYOK acceptance passed as recorded below; older receipts retain historical scope.

Run Factory Droid 0.241.1 headlessly on an existing project. Named commands expose a bounded coding call, the installed version, and a setup inspection without calling a model.

## Stack

Official npm `@factory/cli@0.241.1` plus `@factory/cli-linux-x64@0.241.1`, full npm integrity [lock](package-lock.json), unmodified native SHA256 `1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1`, Alibaba FC base, Python3.13 and immutable servere2cb27e. Install hooks are disabled; execute the fixed native binary directly. SHA256 is checked at build and every native command. [Provenance](upstream.json), [upstream notice](UPSTREAM-NOTICE.md), [Dockerfile](Dockerfile). Native metadata is proprietary `UNLICENSED`; its repository field does not establish a public source commit. Non-root `user`, generation2, port9000.

## Problem solved

An automation can upload a project, ask Droid to edit it, inspect files, and run independent tests through Agent Sandbox. Legacy Factory mode refuses missing account credentials before launching login; BYOK requires its separate compatible settings. `WORKSPACE` controls the project root; success and error text redact configured secret values.

## Quick start (CLI)

The primary path is explicit BYOK. Replace placeholders with this run's unique directory and owned IDs. Publish the immutable source before preparation. Start the server with the three `DROID_MODEL_*` settings before the coding call; do not put secrets in CLI arguments. Native CLI0.4.1 syntax below is source-checked; current SDK/Express acceptance is linked below. Require official READY and independently verify owned cleanup.

```bash
python scripts/prepare_steps.py droid --output /tmp/droid-steps-<unique-run> --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/droid-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> droid_version
abx --native run <owned-sandbox-id> droid_byok_setup_check
abx --native run <owned-sandbox-id> droid_byok --arg prompt='Create hello.txt containing Hello from Droid.'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

The following retained example uses the separate Factory-account command.

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

Install the CLI following the [official installation instructions](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox#readme), then build this template on `alicloud-express`:

```bash
abx template install alibaba-agent-sandbox/awesome-templates//droid
abx create --template <template-id>
abx run <sandbox-id> droid_version
abx run <sandbox-id> droid_setup_check
abx run <sandbox-id> droid --arg prompt='Review the existing project' --arg auto=''
```

Use the template ID returned by installation. Inject `FACTORY_API_KEY` through your private environment configuration at sandbox creation; provider credentials and the Factory product key are separate. The final command requires the Factory key. Upload a project with the SDK files API before a coding task. Remove the sandbox with `abx kill <sandbox-id> -y` when done.

## Quick start (Python SDK)

BYOK example with the paired `agent-sandbox-client`: install using the [source guide](../docs/python-client-installation.md). Settings are captured at server import. Inspect setup flags; a prewarmed process requires [explicit environment startup](../docs/runtime-environment.md). No model key is passed in named-command arguments. The example is syntax-checked; recorded cloud acceptance exercised these SDK operations with the explicitly configured9010server.

```python
import asyncio
import os
import secrets

import httpx
from agent_sandbox.api.sandbox import Sandbox

async def example():
    settings = {name: os.environ[name] for name in ('DROID_MODEL_API_KEY', 'DROID_MODEL_BASE_URL', 'DROID_MODEL')}
    token = secrets.token_urlsafe(32)
    settings.update(HOME="/home/user", WORKSPACE='/home/user/app',
                    ABX_SERVER_BASE_DIR='/home/user/app', ABX_SERVER_TOKEN=token,
                    PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin")
    sb = await Sandbox.create(template="<owned-template-id>", timeout=1200)
    stream = drain = server = None
    try:
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py",
            env=settings, timeout=1100)
        started = asyncio.Event()
        async def consume():
            async for chunk in stream:
                if chunk.pid:
                    started.set()
        drain = asyncio.create_task(consume())
        await asyncio.wait_for(started.wait(), 90)
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(60):
                try:
                    response = await client.get(sb.network.get_url(9010) + "/health",
                                                headers=sb.network.get_access_headers())
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("configured server not healthy")
        server = sb.server_at(9010, token=token)
        print(await server.commands.run('droid_version', timeout=90))
        setup = await server.commands.run('droid_byok_setup_check', timeout=60)
        if not all(setup.get(k) is True for k in ("api_key_set", "base_url_set", "model_set")):
            raise RuntimeError("model configuration not present in this server")
        await sb.files.write("/home/user/app/calc.py", "def add(a, b): return a - b\n")
        result = await server.commands.run("droid_byok", prompt="Fix calc.py so add returns the sum.",
                                           command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("native Droid did not complete successfully")
        print(await sb.files.read("/home/user/app/calc.py"))
    finally:
        try:
            if server is not None:
                await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                if drain is not None:
                    drain.cancel()
                    await asyncio.gather(drain, return_exceptions=True)
                if stream is not None:
                    await stream.cancel()

asyncio.run(example())
```

Legacy Factory-account example:

Use `agent-sandbox-client`, imported as `agent_sandbox`. For an unpublished release, use the [paired source installation](../docs/python-client-installation.md).

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=600,
        envs={"FACTORY_API_KEY": os.environ["FACTORY_API_KEY"]},
    )
    try:
        await sb.files.write("/home/user/app/calc.py", "def add(a, b):\n    return a - b\n")
        print(await sb.run("droid_version"))  # "0.241.1"
        print(await sb.run("droid", prompt="Fix calc.py so add returns the sum.",
                           auto="low", command_timeout=300, timeout=360))
        print(await sb.files.read("/home/user/app/calc.py"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`command_timeout` is the server-side execution deadline. `Sandbox.run(timeout=360)` is the client HTTP timeout; a shorter client timeout does not guarantee cancellation. Results are buffered. For background jobs, progress and cancellation, use the SDK process API.

## Quick start (HTTP POST)

BYOK uses a direct JSON argument object and your own server URL/token in environment variables. The envelope is `{"result":{"exit_code":0,"native_version":"0.241.1","stdout":"<native JSON>","stderr":""}}`. Native nonzero exits remain visible in `exit_code`; do not treat HTTP200 alone as agent success. `POST /commands/droid_byok_setup_check` accepts `{}`. Schema errors400, authentication401, unknown commands404 and semantic/configuration/deadline failures500. Buffered output; client disconnection does not cancel execution.

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/droid_byok" -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' -d '{"prompt":"Fix calc.py so add returns the sum.","command_timeout":300}'
```

Legacy Factory-account HTTP:

Obtain the sandbox URL for port 9000 using `sb.network.get_url(9000)`:

```bash
curl -X POST '<sandbox-port-9000-url>/commands/droid' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ABX_SERVER_TOKEN}" \
  -d '{"prompt":"Fix calc.py so add returns the sum.","auto":"low","command_timeout":300}'
```

The request body is the direct argument object. A successful reply is `{"result":"<buffered Droid output>"}`. If `ABX_SERVER_TOKEN` is empty, omit that header. A nonempty server token requires `Authorization: Bearer <token>` or `X-Access-Token: <token>`; with the Python SDK, use `sb.server_at(9000, token=...)`. Provider gateway authentication is separate: add the access header required by your provider in addition to server authentication. `GET /commands` describes signatures. `POST /commands/droid_version` and `/commands/droid_setup_check` accept `{}`.

HTTP 400 indicates missing or mistyped arguments; 401 indicates server authentication failure; 404 indicates an unknown command; 500 indicates invalid value ranges, missing Factory credentials, upstream failure or execution timeout. No streamed response is returned.

## Command reference

| Command | Parameters | Result / upstream call |
| --- | --- | --- |
| `droid_byok` | Required `prompt: str`,1–32768 UTF-8 bytes, nonempty/no NUL; `cwd: str=""`, at most4096 bytes, existing resolved workspace directory; `command_timeout: int=300`,1–600seconds, bool refused | Object: native `stdout`, `stderr`, `exit_code`, `native_version`. Fixed `droid exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`; task via anonymous stdin. Modifies the selected project; private state removed on every path. |
| `droid_byok_setup_check` | None | Model/base/key presence booleans, `mode: openai-compatible-byok`, `factory_account_required: false`; no model request or secret values. |
| `droid_version` | None | Version string from `droid --version`; no model key needed. |
| `droid_setup_check` | None | Object with `installed` (bool), `package`, `version`, `expected_version` (strings), `api_key_set`, `workspace_exists`, `auto_update_enabled` (bool). No model call; no key values returned. |
| `droid` | `prompt`: required nonempty string; `auto`: string, default `low`, one of `""`, `low`, `medium`, `high`; `cwd`: string, default `""`, existing directory within `WORKSPACE`; `command_timeout`: integer, default 300, range 1–600 seconds | Buffered stdout string from `droid exec [--auto LEVEL] -- PROMPT`. Nonzero exit or timeout raises a sanitized execution error. |

Relative `cwd` resolves from `WORKSPACE`. Absolute paths must remain inside that root after symlink resolution. `auto=""` omits the flag and uses upstream read-only mode; `low` allows project edits, `medium` also allows development commands, and `high` allows riskier operations. The template never passes `--skip-permissions-unsafe`. **Compatibility:** 1.1.0 uses `/home/user/app` instead of `/app` and defaults the coding command to explicit `--auto low`; use `auto=""` for the previous read-only behavior.

Version1.2.0 adds BYOK without changing legacy arguments. Native paths are fixed and SHA256-checked; output is limited256KiB per stream. Both modes exclude operator cloud/GitHub credentials, use private HOME and identity-pinned group/nonce/pidfd cleanup on success, failure, overflow and timeout. BYOK always uses low autonomy and does not enable unsafe permission bypass. The native process starts in a private temporary Git root; anonymous task context identifies the selected project by absolute path. This prevents project `.factory` settings from affecting model routing; target project native configuration is not loaded automatically. Pass private runtime settings with the pinned `--settings` flag. Only original native file tools Read/Edit/Create/Grep/Glob/LS are enabled; no Execute, subagent or MCP tools. Project files remain caller-owned; cwd selection is not an OS security boundary.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Default | Purpose |
| --- | --- | --- |
| `DROID_MODEL_API_KEY` | Empty; required for BYOK | At most8192 characters, no CR/LF/NUL; private native environment only. |
| `DROID_MODEL_BASE_URL` | Empty; required for BYOK | Explicit HTTPS compatible base, at most2048 characters, no userinfo/query/fragment; literal local HTTP only for fixtures. |
| `DROID_MODEL` | Empty; required for BYOK | Explicit1–200-character model identifier. |
| `FACTORY_API_KEY` | Empty | Factory account API key, injected at creation. Required only for `droid`. |
| `ABX_SERVER_TOKEN` | Empty | Optional HTTP server authentication. |
| `WORKSPACE` | `/home/user/app` | Existing project root; an invalid explicit root fails. |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | Forced off in subprocesses to preserve the pin. |

Factory credentials are obtained from [Factory API key settings](https://app.factory.ai/settings/api-keys). A DashScope or OpenAI key is not a replacement for `FACTORY_API_KEY`. `droid_byok` instead uses a private native `customModels` entry, provider `generic-chat-completion-api`, explicit model/base and `apiKey: "${ABX_DROID_MODEL_KEY}"`. The real key is not written into settings or argv. Native selection uses the configured custom model; no Factory key, interactive login or alternate binary is injected. Key/base values are redacted from native output; private state is deleted. [Official BYOK docs](https://docs.factory.com/model-independence/byok); exact0.241.1 behavior was checked with a synthetic-only fixed response, not a real-model acceptance. Upstream behavior is documented in [Droid Exec](https://docs.factory.com/droid-exec/overview); the exact pinned CLI help is the authority for flags. Redaction covers raw and JSON-escaped configured secret values in stdout and error messages. Agent-written project files still require normal secret hygiene. The cwd constraint selects the project and is not an operating-system security boundary.

## Resources

Default: 2 vCPU, 2048 MB RAM, port 9000. BYOK calls require your configured model service; legacy Factory calls require external Factory access. The platform starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py` and probes `agent-sandbox-server healthcheck --port 9000`.

## Verified

Template1.2.0, experimental, `tested_on: [alicloud-express]`. Actual same-source
[L1 image39500551739](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39500551739),
[canonical SDK-created native steps](evidence/express-2026-10-20T212811Z.json) and
[full HTTP/model proof](evidence/verification-steps-2026-10-20T212811Z.json) PASS.
HTTP8PASS/0FAIL/0SKIP and genuine approved-model BYOK17PASS/0FAIL/0SKIP. A native
synthetic-key cloud probe first verified exact model/Bearer routing, zero requests
to conflicting project settings, six permitted file tools and fixture absence
before any real model key. Real coding fixed the seeded existing source, preserved
all original tests byte-for-byte, created fresh report/nonce artifacts, and passed
complete original plus held-out post-return checks with unpredictable ACKs.
Owned project/private state/listener and outer sandbox/template absence passed.
Duration134.596s. No current real Factory-account model or other-provider pass
is claimed. SDK snippets are syntax-checked and recorded cloud acceptance used
the same explicitly configured9010SDK operations. Historical receipts stay unchanged.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

Source-runtime follow-up on 2026-10-18: the native Python SDK completed the pinned Droid background install, SDK keyless/version checks, external HTTP suite and owned cleanup (nine checks PASS). See [exact-scope evidence](../.agents/evidence/verify/2026-10-18-droid-native-runtime.md). This is not image-backed/canonical L2 or model acceptance; `tested_on` remains unchanged.

No canonical image-deployment provider pass is recorded for this template.

</details>

## Secondary development

Keep the Alibaba base, exact CLI/server pins and non-root user. Extend [commands.py](commands.py) through `@command`; pass argv directly and keep secret redaction, key guards and deadline cleanup. Build with BuildKit; deployment may inject a server wheel. Run:

```bash
python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py droid/test_byok.py droid/test_model_controller.py
python3 scripts/check_template.py droid
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py droid
```

Source-only local execution explicitly skips the missing native version; it cannot qualify the provider. L1 builds the actual Dockerfile and checks the real native SHA/version. Required L2 uses actual SDK creation, canonical steps, full HTTP and independent owned cleanup. L3 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1` runs [e2e_test.py](e2e_test.py) on a fresh owned cloud server configured for BYOK: real native successful JSON with positive turns, exact fresh final nonce, existing source edit, new artifacts, byte-identical original tests, complete independent original and held-out post-return checks with fresh ACKs, and owned project absence. Generated code never runs on the operator. Legacy Factory controller is retained separately as [factory_e2e.py](factory_e2e.py), requiring a genuine Factory key; no such current model pass is claimed.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py droid` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md), and the [design](../docs/design/droid.md). Keep this README and [Chinese README](README.zh-CN.md) synchronized; include regression tests, engineering records and actual evidence with a scoped PR. Keep the catalog experimental until required acceptance passes.

## Issues

Continue [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19). Report template defects in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), or CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions, provider, generation and sanitized reproduction; never include keys or raw private logs.

## License

Template source: [Apache-2.0](../LICENSE). Factory Droid is distributed separately under its upstream terms; installing the CLI does not relicense it.

### 2026-10-20 full step checkpoint: template1.1.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155022Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/0 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).

The changed runtime retains the proprietary [upstream notice](UPSTREAM-NOTICE.md).
