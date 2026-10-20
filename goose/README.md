# Goose

[中文](README.zh-CN.md).

## What it does

Runs the official Goose1.54.0 terminal agent with an OpenAI-compatible backend.
Every turn uses private configuration and file stdin. The default is tool-free
chat; explicit `allow_tools=true` enables the bundled developer tools.

## Stack

Alibaba FC base v0.0.49, generation2, non-root `user`, pinned server SDK e2cb27e.
Official CPU GNU Linux x86_64/aarch64 release assets have exact byte lengths and
SHA256 in [assets.json](assets.json), tied to source commit
[cd643d2126fffab4c6a6186905211ba868d6a657](https://github.com/block/goose/tree/cd643d2126fffab4c6a6186905211ba868d6a657).
No GPU, Docker daemon, desktop or floating installer is required. Linux x86_64 is
the current local test profile; an arm64 asset pin is not arm64 provider evidence.

## Problem solved

Use the real Goose agent to perform terminal/file work in an owned sandbox,
without importing a caller's saved providers, extensions, hints or session history.
This profile selects the supported OpenAI-compatible provider, not every upstream
provider or the Goose desktop application.

## Quick start (CLI)

Native CLI syntax; check [entry compatibility](../docs/using-templates.md#client-entry-compatibility).

```bash
abx template deploy ./goose -y
abx create --template <template-id> --timeout 900 -y
abx run <sandbox-id> goose_version
abx run <sandbox-id> goose_setup_check
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Version/setup need no key. Model calls need settings in the running command server;
use the explicit SDK startup below. Create-time environment does not reconfigure
a prewarmed server. Provider setup and ID ownership are in [using templates](../docs/using-templates.md).

## Quick start (Python SDK)

Install the `agent-sandbox-client` distribution using the [pinned client instructions](../docs/python-client-installation.md). Configure the
three GOOSE variables in your operator environment; credentials stay out of argv.
The example owns the sandbox and exports a file before destroying it.

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
            env={"GOOSE_API_KEY": os.environ["GOOSE_API_KEY"],
                 "GOOSE_BASE_URL": os.environ["GOOSE_BASE_URL"],
                 "GOOSE_MODEL": os.environ["GOOSE_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "goose", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("Goose failed; inspect the private returned diagnostics")
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

The SDK helper starts a new9010 server with a separate random bearer token. It
keeps model settings out of the already-running9000 server. Only the caller-owned
sandbox is destroyed. This example is API/source checked; actual provider/model
claims require the receipts below.

## Quick start (HTTP POST)

Use the SDK-forwarded9010 URL of that configured server as `ABX_SERVER_URL`, and
its random process-start token as `ABX_SERVER_TOKEN`.

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/goose" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

Example response: `{"result":{"stdout":"42","stderr":"","exit_code":0}}`.
HTTP200 wraps `{stdout,stderr,exit_code}` in `result`; preserve nonzero upstream
status. Missing/undeclared/mistyped arguments are400, auth failure401, unknown
command404; invalid paths/settings/pins/limits or timeout are500 with error/type.
The response is buffered. Client HTTP timeout is distinct from command timeout;
disconnection does not guarantee native cancellation.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| goose_version | none | actual pinned version string1.54.0 |
| goose_setup_check | none | installed/version and api_key_set/base_url_set/model_set flags; never configures/logs in |
| goose | required prompt:str, nonempty UTF-8/no NUL/256KiB max; cwd:str="", existing directory inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800 | {stdout:str,stderr:str,exit_code:int} |

The actual CLI uses `run --instructions - --no-session --no-profile --max-turns 20`
plus quiet text output, explicit provider/model and only the selected developer
builtin in tool mode. Default chat advertises no tools. Input is a private file
on stdin, never shell interpolation or prompt argv. Each output stream is capped
at256KiB. Timeout/overflow kills the unreaped owned group before leader reap.
Every turn removes its private Goose config/data; project changes remain until
caller cleanup or sandbox deletion. Returned diagnostics redact configured key
and base URL, but project stdout may still contain private project content.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| GOOSE_API_KEY | model calls | empty | OpenAI-compatible credential, translated only into native child OPENAI_API_KEY |
| GOOSE_BASE_URL | model calls | empty | explicit HTTP(S) endpoint; no userinfo/query/fragment; mapped to upstream OPENAI_BASE_URL |
| GOOSE_MODEL | model calls | empty | actual upstream model ID |
| WORKSPACE | no | /home/user/app | caller-owned working directory |
| ABX_SERVER_TOKEN | no | empty | command-server process bearer token |
| GOOSE_BINARY | operator diagnostics only | Goose on image PATH | independently installed binary override, still checks exact version |

A private GOOSE_PATH_ROOT/HOME and XDG dirs, disabled keyring/telemetry/session
naming, `CONTEXT_FILE_NAMES=[]` and `--no-profile` preserve caller state. Native
children receive only PATH/optional CA settings plus private runtime/model
settings; cloud, GitHub and command-server credentials are not forwarded.

When starting a secondary server, preserve the image PATH; an explicit replacement must include `/opt/goose`. The diagnostic reports the binary visible to that server process.

## Resources

2vCPU/2048MB; command API9000, optional explicitly started9010. Shared memory has
no browser dependency. Installer uses an exact ~81MB compressed CPU asset, a
240-second download budget with30-second socket timeout, a400MiB executable bound
and a separate `du -sx`8GiB image-rootfs check. Local prefix installation does not
scan the operator filesystem. Each turn is at most20 model turns and its declared
wall deadline; cleanup follows. Detached setsid children or server SIGKILL remain
outside group cleanup; destroying the sandbox is the final boundary.

## Verified

| Version | Provider | Mode and result | Evidence |
| --- | --- | --- | --- |
| 1.0.0 | alicloud-express | SDK-created, verified CI image; CLI/SDK smoke and strict compatible-model17 PASS/0 FAIL/0 SKIP | [image](evidence/express-2026-10-20.json), [model](evidence/model-image-2026-10-20T073500Z.json) |

The actual Goose agent edited source, created a new report, preserved and ran the original tests and passed independently generated held-out inputs using qwen3.8-flash. Owned sandbox/template/registry cleanup and registry digest readback passed independently. The separate model-off HTTP run has9 PASS and1 explicit model SKIP; that skip is not promoted to a model pass. This is the OpenAI-compatible provider profile, not every upstream provider. The actual step build failed in the native installer budget; [failed step diagnosis](evidence/steps-diagnosis-2026-10-20.json) remains a failure. Other providers and arm64 execution are unverified.

## Secondary development

Use `python goose/install_runtime.py --prefix <new-private-prefix>` for local
installation. Actual local CLI/protocol/process tests:
`python -m pytest -q goose/test_commands.py`. Synthetic local HTTP fixtures prove
native protocol and tool-selection behavior, not real models or provider support.
The source HTTP controller checks real model source edits, new report, unchanged
original tests and isolated held-out values when E2E_REQUIRE_LLM=1; no static
marker alone passes. E2E_REQUIRE_CLI=1 requires the actual binary.

Prepare [platform steps](../docs/platform-steps.md) with
`python scripts/prepare_steps.py goose --output /tmp/goose-steps`; this only
prepares source. Actual basic step acceptance is
`python scripts/run_steps_e2e.py goose --timeout 1200`. Keep build-mode receipts,
real model checks and independent owned-resource cleanup separate.

## Contributing

[CONTRIBUTING](../CONTRIBUTING.md), [spec](../docs/template-spec.md) and
[design](../docs/design/goose.md). Keep both languages/pins/argv/evidence aligned.

## Issues

[Issue49](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/49).
Templates: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
Server/client: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).
CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template code is [Apache-2.0](../LICENSE). Official Goose is Apache-2.0; its
[unchanged license](upstream-LICENSE) is installed with the unmodified official
binary. Upstream dependencies keep their own notices. No upstream desktop,
Vulkan/CUDA asset, proprietary account or model weights are redistributed.

### Additional current-version platform-step acceptance

[Actual steps](evidence/express-2026-10-20T135350Z.json) and [external HTTP attempt](evidence/verification-steps-2026-10-20T135350Z.json): official READY, Python SDK creation, CLI/SDK smoke and 9 HTTP PASS / 0 FAIL / 1 SKIP. Model calls remain NOT_RUN in this receipt. Independent sandbox/template and private same-account asset-cache object/bucket cleanup passed before publication. Earlier image/model receipts retain their own scope.
