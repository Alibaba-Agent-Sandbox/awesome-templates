# Factory Droid

## What it does

Run Factory Droid 0.241.1 headlessly on an existing project. Named commands expose a bounded coding call, the installed version, and a setup inspection without calling a model.

## Stack

Install the pinned CLI from `https://registry.npmjs.org` with optional platform packages included. The base image npm mirror returned 404 for the required native package; its absence triggers an upstream fallback that can leave a self-referencing binary link.

Alibaba FC base image (normally `v0.0.49`), its Python 3.13 and Node.js 20, npm `@factory/cli@0.241.1`, and the pinned in-sandbox `agent-sandbox-server` source in [Dockerfile](Dockerfile). The template uses generation 2 and runs as `user` on port 9000.

## Problem solved

An automation can upload a project, ask Droid to edit it, inspect files, and run independent tests through Agent Sandbox. Missing Factory credentials fail before launching interactive login. `WORKSPACE` controls the project root; success and error text redact configured secret values.

## Quick start (CLI)

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

Use `agent-sandbox-client`, imported as `agent_sandbox`. For an unpublished release, use the [paired source installation](../docs/python-client-installation.md).

```python
import asyncio
import os
from agent_sandbox import Sandbox

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
| `droid_version` | None | Version string from `droid --version`; no model key needed. |
| `droid_setup_check` | None | Object with `installed` (bool), `package`, `version`, `expected_version` (strings), `api_key_set`, `workspace_exists`, `auto_update_enabled` (bool). No model call; no key values returned. |
| `droid` | `prompt`: required nonempty string; `auto`: string, default `low`, one of `""`, `low`, `medium`, `high`; `cwd`: string, default `""`, existing directory within `WORKSPACE`; `command_timeout`: integer, default 300, range 1–600 seconds | Buffered stdout string from `droid exec [--auto LEVEL] -- PROMPT`. Nonzero exit or timeout raises a sanitized execution error. |

Relative `cwd` resolves from `WORKSPACE`. Absolute paths must remain inside that root after symlink resolution. `auto=""` omits the flag and uses upstream read-only mode; `low` allows project edits, `medium` also allows development commands, and `high` allows riskier operations. The template never passes `--skip-permissions-unsafe`. **Compatibility:** 1.1.0 uses `/home/user/app` instead of `/app` and defaults the coding command to explicit `--auto low`; use `auto=""` for the previous read-only behavior.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Default | Purpose |
| --- | --- | --- |
| `FACTORY_API_KEY` | Empty | Factory account API key, injected at creation. Required only for `droid`. |
| `ABX_SERVER_TOKEN` | Empty | Optional HTTP server authentication. |
| `WORKSPACE` | `/home/user/app` | Existing project root; an invalid explicit root fails. |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | Forced off in subprocesses to preserve the pin. |

Factory credentials are obtained from [Factory API key settings](https://app.factory.ai/settings/api-keys). A DashScope or OpenAI key is not a replacement for `FACTORY_API_KEY`. A custom model configuration is outside this template's API. Upstream behavior is documented in [Droid Exec](https://docs.factory.com/droid-exec/overview); the exact pinned CLI help is the authority for flags. Redaction covers raw and JSON-escaped configured secret values in stdout and error messages. Agent-written project files still require normal secret hygiene. The cwd constraint selects the project and is not an operating-system security boundary.

## Resources

Default: 2 vCPU, 2048 MB RAM, port 9000. Model calls require external Factory network access. The platform starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py` and probes `agent-sandbox-server healthcheck --port 9000`.

## Verified

Source-runtime follow-up on 2026-10-18: the native Python SDK completed the pinned Droid background install, SDK keyless/version checks, external HTTP suite and owned cleanup (nine checks PASS). See [exact-scope evidence](../.agents/evidence/verify/2026-10-18-droid-native-runtime.md). This is not image-backed/canonical L2 or model acceptance; `tested_on` remains unchanged.

No canonical image-deployment provider pass is recorded for this template.

## Secondary development

Keep the Alibaba base, exact CLI/server pins and non-root user. Extend [commands.py](commands.py) through `@command`; pass argv directly and keep secret redaction, key guards and deadline cleanup. Build with BuildKit; deployment may inject a server wheel. Run:

```bash
python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py
python3 scripts/check_template.py droid
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py droid
```

The local suite requires the real pinned `droid` on the server PATH; it never substitutes a fake version. L1 additionally requires a Docker build. L2 requires a real Express deployment and externally asserted smoke commands. L3 requires `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1`, a Factory key on the server, and the coding acceptance in [e2e_test.py](e2e_test.py): seeded failing code, source modification, preserved tests, new downloaded artifacts, independent test reruns and held-out assertions. The verifier uses remote file/process APIs and removes its own project. Missing keys fail required L3; a response marker alone cannot pass.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md), and the [design](../docs/design/droid.md). Keep this README and [Chinese README](README.zh-CN.md) synchronized; include regression tests, engineering records and actual evidence with a scoped PR. Keep the catalog experimental until required acceptance passes.

## Issues

Continue [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19). Report template defects in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), or CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions, provider, generation and sanitized reproduction; never include keys or raw private logs.

## License

Template source: [Apache-2.0](../LICENSE). Factory Droid is distributed separately under its upstream terms; installing the CLI does not relicense it.
