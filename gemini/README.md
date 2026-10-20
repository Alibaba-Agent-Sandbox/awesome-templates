# gemini

Experimental Gemini CLI template. [中文](README.zh-CN.md).

## What it does

Runs pinned Gemini CLI headlessly through the named `gemini` command. `gemini_version` and `gemini_setup_check` inspect installation and configuration. Model execution needs a genuine Gemini API key; an OpenAI-compatible key does not substitute for it.

## Stack

Alibaba runtime base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (deploy resolves region/tag), Node.js >=20, `@google/gemini-cli@0.64.0`, and `agent-sandbox-server` pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505` unless deploy injects a wheel. Runs as `user` in `/home/user/app`; generation 2 uses the start/readiness commands in [template.yaml](template.yaml), without Docker CMD/ENTRYPOINT.

## Problem solved

Provides buffered, typed command calls with a missing-key guard, read-only setup diagnostics, an explicit tool-permission choice and a process-group execution deadline. The default approval mode is upstream `plan` (read-only); `yolo=true` explicitly approves editing and shell tools. The sandbox runtime is the isolation boundary; the cwd check only constrains the starting directory.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Runtime configuration: the create-time key examples below require the named-command server to start with those values. For a prewarmed server, inspect its setup flags when provided and follow [explicit process configuration](../docs/runtime-environment.md); creating a sandbox does not reconfigure an already running server.

Deploy from the repository checkout with your existing provider configuration:

```bash
abx template deploy ./gemini -y
abx create --template <template-id> -y --env GEMINI_API_KEY="$GEMINI_API_KEY"
abx run <sandbox-id> gemini_version
abx run <sandbox-id> gemini_setup_check
abx run <sandbox-id> gemini --json-args '{"prompt":"Describe the project files","command_timeout":120,"yolo":false}'
```

For an authorized coding task, explicitly pass `"yolo":true` and choose an existing project `cwd` inside `WORKSPACE`. Use a new alias when replacing a generation-1 template; do not update it in place with generation-2 startup options. Clean up task-owned resources with `abx kill <sandbox-id> -y` and `abx template delete <template-id> -y`.

## Quick start (Python SDK)

Install `agent-sandbox-client`; check release availability or use the [paired source installation](../docs/python-client-installation.md). Import `agent_sandbox`.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300,
                              envs={"GEMINI_API_KEY": os.environ["GEMINI_API_KEY"]})
    try:
        print(await sb.run("gemini", prompt="Describe the project files",
                           command_timeout=120, yolo=False, timeout=150))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` invokes a named command. `sb.commands.run` executes a shell process. `command_timeout` limits the server's CLI process group; `timeout` controls the client's HTTP request and does not guarantee cancellation. Use the process API for background tasks and cancellation.

## Quick start (HTTP POST)

`ABX_SERVER_URL` is the sandbox port-9000 URL from `sb.network.get_url(9000)`, or `http://127.0.0.1:9000` locally:

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gemini" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Describe the project files","command_timeout":120,"yolo":false}'
```

Send parameters directly, without an `args` wrapper. HTTP 200 returns `{"result":"<buffered Gemini JSON output>"}`. Omit Authorization when server `ABX_SERVER_TOKEN` is empty. Provider gateway authentication is separate: also send the gateway access header required by your provider. No server secret is automatically a provider token.

Missing or mistyped arguments return HTTP 400; failed server authentication 401; unknown commands 404; invalid ranges/paths, empty prompts, missing keys, missing CLI, deadline expiry and upstream failures return 500 with `{"error":"...","type":"..."}`. Argument values are converted by the server before invoking Python; use JSON numbers and booleans. Successful and failed CLI output is redacted using secret-valued environment variables.

## Command reference

| Command | Parameters | Returns |
|---|---|---|
| `gemini` | `prompt`: required nonempty string; `model`: string, default `""` → `GEMINI_MODEL` → `gemini-3.1-flash-lite`; `cwd`: string, default `""` → `WORKSPACE`; `command_timeout`: integer 1–1800 seconds, default 600; `yolo`: boolean, default false | string containing buffered upstream JSON |
| `gemini_version` | none | installed CLI version string, expected `0.64.0` |
| `gemini_setup_check` | none | object: installation/version/pin, API-key presence boolean, model-presence/workspace and settings-file metadata; no credential/settings values |

`cwd` must exist inside resolved `WORKSPACE`; relative paths resolve there, and symlink/traversal escapes are rejected. The executable receives an argv array: `gemini -p <prompt> --model <model> --output-format json --approval-mode plan` (or `yolo` only when opted in). stdin is closed. No unsupported turn-limit flag is invented. Diagnostics do not rewrite `~/.gemini/settings.json` or project `.gemini/settings.json`; settings parsing reports JSON-object validity, not schema validity.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | empty | Required for model calls; missing/whitespace fails before CLI launch and prevents interactive OAuth login |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Default model; must be available to the supplied key |
| `WORKSPACE` | `/home/user/app` | Existing execution root |
| `ABX_SERVER_TOKEN` | empty | Optional server bearer authentication; inject at create time |
| `ABX_SERVER_PORT` | `9000` | Local standalone server port |

Existing upstream auth/settings remain user-owned. The wrapper does not reconfigure an OAuth/Vertex-selected profile; inspect your profile if it conflicts with API-key authentication. Never put real secrets in a template, image, report or committed environment file.

## Resources

2 vCPU, 4096 MB RAM, port 9000; Express rootfs is about 10G. No nested Docker, KVM or extra capabilities are required.

## Verified

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.0.1; steps build, official READY, CLI/SDK basic smoke, independent cleanup; current-version model acceptance NOT_RUN | [2026-10-19](evidence/express-2026-10-19T183608Z.json) |

The changed workspace profile is verified in real generated steps. Prior receipts retain historical scope; basic smoke does not establish model acceptance.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider acceptance is recorded. Local diagnostics and mocked regressions do not prove image, cloud or model acceptance. `tested_on` remains empty and catalog status remains experimental. See [verification record](../.agents/evidence/verify/2026-10-16-gemini-runtime.md).

</details>

## Secondary development

Read [design](../docs/design/gemini.md). Keep exact npm/server pins, Alibaba base, non-root user and generation-2 startup. Run `python3 scripts/check_template.py gemini`, `python3 -m pytest gemini/test_commands.py gemini/test_e2e_protocol.py -q`, and `python3 scripts/run_local_e2e.py` with the server/client dependencies installed. `E2E_RUN_LLM=0` skips model execution and sends no coding requests.

L1 requires a real image build; L2 requires deployment plus external CLI/SDK calls. For L3, start the target with `GEMINI_API_KEY`, set controller `E2E_BASE_URL` and target `E2E_BASE_DIR` inside `WORKSPACE`, then run `E2E_REQUIRE_LLM=1 E2E_RUN_LLM=1 python3 gemini/e2e_test.py`. Only the target needs the model key. The test seeds failing source/tests through the target files API, requests a fix plus new artifacts with explicit yolo, preserves the tests, independently executes original and held-out tests remotely, and removes its unique project. A response marker alone fails.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py gemini` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and repository engineering records. Reuse [Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30). Record failed, skipped and blocked tiers separately; a missing key is a blocked required L3, not a pass.

## Issues

Template problems: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client problems: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI problems: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), using `[templates]` for SDK/CLI reports.

## License

Apache-2.0. See [LICENSE](../LICENSE).

### 2026-10-20 full step checkpoint: template2.0.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155048Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
