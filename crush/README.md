# Crush

[中文](README.zh-CN.md).

## What it does

Runs the official native Crush0.98.1 terminal agent using an explicitly configured OpenAI-compatible provider. Default turns expose no tools; allow_tools=true exposes exactly bash/edit/multiedit/view/write/ls/glob/grep. Subagent, MCP, network-fetch, background-job and LSP tools are disabled.

## Stack

Alibaba FC generation2 CPU/non-root base, pinned SDK e2cb27e. Official GNU Linux x86_64/aarch64 archives are fixed by byte length and SHA256 in [assets.json](assets.json), source [8b1824282eccc78cc62c188c245cf375230a18ce](https://github.com/charmbracelet/crush/tree/8b1824282eccc78cc62c188c245cf375230a18ce). An arm64 pin is not arm64 execution evidence.

## Problem solved

Run genuine terminal coding in an owned sandbox with explicit model settings and private per-turn configuration/data. This is the compatible-provider CLI profile; interactive UI, saved caller configuration and every upstream provider are outside its scope.

## Quick start (CLI)

```bash
abx template deploy ./crush -y
abx create <template-id> --detach --timeout 900
abx run <sandbox-id> crush_version
abx run <sandbox-id> crush_setup_check
abx kill <sandbox-id>
abx template delete <template-id> -y
```

Deploy returns the template ID and create returns the owned sandbox ID used above. Version/setup need no model key. See [entry compatibility and provider setup](../docs/using-templates.md#client-entry-compatibility). Model settings must be present in the running server; create-time environment does not reconfigure a prewarmed server.

## Quick start (Python SDK)

Install agent-sandbox-client using the [pinned source instructions](../docs/python-client-installation.md). Set the three CRUSH variables in the operator environment, then run:

```python
import asyncio
import os
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900)
    server = None
    try:
        server = await sb.start_server(
            port=9010, commands="/home/user/app/commands.py", timeout=60,
            token=secrets.token_urlsafe(32),
            env={"CRUSH_API_KEY": os.environ["CRUSH_API_KEY"],
                 "CRUSH_BASE_URL": os.environ["CRUSH_BASE_URL"],
                 "CRUSH_MODEL": os.environ["CRUSH_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "crush", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("Crush failed; inspect the private returned diagnostics")
        print(await sb.files.read("/home/user/app/HELLO.txt"))
    finally:
        try:
            if server is not None:
                await server.aclose()
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())

```

The example starts its own random-token9010 command server, exports the generated file and destroys only its owned sandbox. This source-checked example does not itself establish provider/model acceptance. Preserve image PATH when starting a secondary server; a replacement must include /opt/crush.

## Quick start (HTTP POST)

Use the SDK-forwarded9010 URL as ABX_SERVER_URL and that server's random token as ABX_SERVER_TOKEN.

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/crush" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

HTTP200 result is {"result":{"stdout":"42","stderr":"","exit_code":0}}; retain nonzero native status. Undeclared/missing/mistyped arguments400, auth401, unknown command404, invalid path/config/limits/pin or timeout500 with error/type. Both response streams are buffered; client timeout/disconnection does not guarantee process cancellation.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| crush_version | none | actual pinned0.98.1 string |
| crush_setup_check | none | installed/version/api_key_set/base_url_set/model_set; read-only flags |
| crush | prompt:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

Actual argv: crush run --quiet --model owned/ID --small-model owned/ID --cwd DIRECTORY --data-dir PRIVATE. Prompt enters private file stdin. Native foreground mode uses CRUSH_CLIENT_SERVER=false. All29 builtin tools are disabled by default; explicit tool mode enables only the eight above. Each stream256KiB; deadline/overflow/nonzero/success all close the owned process group and identity-pinned marked workers. Same-UID hostile code, overwritten ownership markers and server SIGKILL require final sandbox destruction.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| CRUSH_API_KEY | model calls | empty | explicit compatible-provider credential |
| CRUSH_BASE_URL | model calls | empty | HTTP(S) endpoint; no userinfo/query/fragment |
| CRUSH_MODEL | model calls | empty | bounded native model identifier |
| WORKSPACE | no | /home/user/app | existing caller workspace |
| ABX_SERVER_TOKEN | no | empty | server process bearer token |
| CRUSH_BINARY | diagnostics | image PATH | binary override; actual version still checked |

Private HOME/XDG/CRUSH config/data and correct native disable-default-providers/auto-update flags prevent loading caller global state. Existing .crushrc/crushrc/.crush.json/crush.json between cwd and the nearest Git worktree root are refused before a native run, because upstream automatically loads them. Caller configuration is preserved. With no Git root, upstream checks cwd only. Only PATH/optional CA settings plus private runtime settings enter children; cloud/GitHub/server keys are excluded. The selected key/base URL enter the private0600 config, are never prompt argv, and exact values are redacted from returned diagnostics. Project output can still contain project secrets.

## Resources

2vCPU/2048MB, command9000 and optional explicit9010. ~26.8MB compressed x64 asset,240-second download/30-second socket bounds; executable400MiB max, separate8GiB rootfs build gate. Prompt256KiB, each output256KiB, wall limit1..1800seconds plus bounded teardown. No native max-turn flag is claimed; per-response8192 tokens and the wall deadline bound execution. Private conversation/config/data are removed after each call; project edits remain caller-owned.

## Verified

Version1.0.0 passed actual Alibaba Express registration of the verified CI image, official READY, native Python SDK Sandbox.create, CLI/SDK smoke and **17 strict real-model checks,0 FAIL/0 SKIP** using the explicit compatible qwen3.8-flash model. Source edits, new report/exact artifact, unchanged original tests and independent post-return held-out calculations passed. Sandbox/template/registry cleanup and post-runtime digest readback passed independently.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.0.0 | alicloud-express | [SDK-created image](evidence/express-2026-10-20.json), [strict model17](evidence/model-image-2026-10-20T111012Z.json), [model-off HTTP](evidence/image-http-2026-10-20T111012Z.json) |

The separate model-off HTTP controller has9 PASS and1 explicit model SKIP; it is not model proof. The [actual native step attempt](evidence/full-http-steps-2026-10-20T110221Z.json) did not independently reach READY and failed before any HTTP assertion; owned cleanup was independently confirmed. A subsequent [official readiness diagnosis](evidence/steps-diagnosis-2026-10-20.json) identifies RUN step4 failing the exact-asset byte/deadline guard; it does not distinguish oversized bytes from deadline expiry. The verified image route is available; do not claim step success. Other providers, arm64 execution and other upstream model/provider profiles remain unverified.

## Secondary development

Install with python crush/install_runtime.py --prefix <new-private-prefix>. Run python -m pytest -q crush/test_commands.py crush/test_controller.py with the actual pinned executable on PATH. Fixtures use authored HTTP/tool responses and literal process programs, not real models on the operator host.

Prepare [platform steps](../docs/platform-steps.md) using python scripts/prepare_steps.py crush --output /tmp/crush-steps; preparation alone is not execution. Actual basic step acceptance: python scripts/run_steps_e2e.py crush --timeout 1200. Required real-model controller flags are E2E_REQUIRE_LLM=1 and E2E_REQUIRE_CLI=1; no response-only marker establishes L3.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [spec](../docs/template-spec.md), [design](../docs/design/crush.md) and both language contracts. Preserve immutable upstream/source and actual verification records.

## Issues

[Template Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65); [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template wrapper code is [Apache-2.0](../LICENSE). Crush0.98.1 is **FSL-1.1-MIT**, not currently MIT or an OSI-approved open-source release. Preserve and review the exact [upstream license](upstream-LICENSE.md), future-license date and restrictions; do not infer unrestricted commercial redistribution. The unmodified official binary and all bundled notices are installed intact; model weights are not included.
