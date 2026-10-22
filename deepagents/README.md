# DeepAgents

[中文](README.zh-CN.md).

## What it does

Runs actual DeepAgents0.7.25 with a local file/shell backend and explicit OpenAI-compatible chat model. Default requests expose zero tools. Explicit allow_tools=true enables exactly ls/read_file/write_file/edit_file/glob/grep/execute/delete. General-purpose and explicit subagents are disabled; task/delegation is absent.

## Stack

Alibaba FC base, generation2/non-root, pinned servere2cb27e. [requirements.lock](requirements.lock) fixes every resolved dependency and SHA256, including [DeepAgents0.7.25](https://pypi.org/project/deepagents/0.7.25/) and langchain-openai1.7.2. Generated from [requirements.in](requirements.in) using uv0.11.28 for Python3.13. Image pip verifies hashes and runs pip check. No remote E2B/OpenSandbox backend or model weights.

## Problem solved

Run the genuine LangChain Deep Agent inside an owned cloud sandbox without asking it to create another sandbox. An explicit Python driver uses the supported API; no unverified console script is assumed. Each call gets a fresh process/model/profile and private HOME/data, preserving caller state.

## Quick start (CLI)

```bash
abx template deploy ./deepagents -y
abx create <template-id> --detach --timeout 900
abx run <sandbox-id> deepagents_version
abx run <sandbox-id> deepagents_setup_check
abx kill <sandbox-id>
abx template delete <template-id> -y
```

Deploy returns the template ID and create returns the owned sandbox ID used above. Version/setup need no model key. See [entry compatibility and provider setup](../docs/using-templates.md#client-entry-compatibility). Model settings must be present in the running server; create-time environment does not reconfigure a prewarmed server.



## Quick start (Python SDK)

Install agent-sandbox-client using the [pinned source instructions](../docs/python-client-installation.md). Set the three DEEPAGENTS variables in the operator environment, then run:

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
            env={"DEEPAGENTS_API_KEY": os.environ["DEEPAGENTS_API_KEY"],
                 "DEEPAGENTS_BASE_URL": os.environ["DEEPAGENTS_BASE_URL"],
                 "DEEPAGENTS_MODEL": os.environ["DEEPAGENTS_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "deepagents", task="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("DeepAgents failed; inspect the private returned diagnostics")
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

The example starts its own random-token9010 command server, exports the generated file and destroys only its owned sandbox. This source-checked example does not itself establish provider/model acceptance.

## Quick start (HTTP POST)

Use the SDK-forwarded9010 URL as ABX_SERVER_URL and that server's random token as ABX_SERVER_TOKEN.

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/deepagents" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"task":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

HTTP200 result is {"result":{"stdout":"42","stderr":"","exit_code":0}}; retain nonzero native status. Undeclared/missing/mistyped arguments400, auth401, unknown command404, invalid path/config/limits/pin or timeout500 with error/type. Both response streams are buffered; client timeout/disconnection does not guarantee process cancellation.



## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| deepagents_version | none | actual installed0.7.25 |
| deepagents_setup_check | none | installed/version/api_key_set/base_url_set/model_set flags; read-only |
| deepagents | task:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

The native [driver](worker.py) calls create_deep_agent with an explicitly constructed ChatOpenAI(use_responses_api=False), LocalShellBackend(inherit_env=False), no custom/subagents and GeneralPurposeSubagentProfile(enabled=False). Default profile excludes all eight native tools; each call registers its profile in a fresh process because upstream registration merges exclusions additively. A tool-mode request cannot re-enable delegation. Task/settings enter private file stdin, not shell/argv.

The graph recursion limit is40 (graph steps, not a promise of40 model turns); each native model request timeout60seconds with zero retries and8192 output tokens. Per-shell timeout min(command_timeout,120), native shell output100000bytes after capture (not a peak-memory bound); outer process deadline/each output256KiB. Native nonzero status is retained. Deadline/overflow raises500; normal structured result remainsHTTP200 even when exit_code is nonzero. Returned diagnostics mask the exact configured key/base URL; project output can remain private.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| DEEPAGENTS_API_KEY | model calls | empty | explicit compatible-provider credential |
| DEEPAGENTS_BASE_URL | model calls | empty | HTTP(S), no userinfo/query/fragment |
| DEEPAGENTS_MODEL | model calls | empty | explicit model identifier |
| DEEPAGENTS_PYTHON | no | /opt/deepagents/bin/python | exact native dependency environment, version checked |
| WORKSPACE | no | /home/user/app | existing owned project directory |
| ABX_SERVER_TOKEN | no | empty | command-server process bearer token |

The selected model settings remain in private stdin only, never inherited as environment by generated shells. Child runtime receives PATH/optional CA plus private HOME/XDG and disabled LangSmith tracing. LocalShellBackend gets only PATH/HOME/locale and the random non-secret process ownership marker, no inherited model/cloud/GitHub/server credentials. No skills/memory/profile files are loaded. The backend's virtual filesystem maps tool paths inside cwd; shell execution still has the sandbox user's full authority and is not restricted by that mapping.

## Resources

2vCPU/2048MB, server9000, optional SDK-started9010; CPU Linux Python3.13. Hash-locked dependency venv /opt/deepagents, separate8GiB image-rootfs gate. Task256KiB, each output256KiB; wall1..1800seconds plus bounded identity-pinned process/group cleanup. Private configuration/conversation data removed after every call; project edits remain until caller cleanup. The owned sandbox is the final boundary for malicious same-UID code or interrupted server cleanup.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.0; regular image, actual CLI/SDK, complete HTTP 9 PASS / 0 FAIL / 1 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-22T110056Z.json) |
| opensandbox | 1.0.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 9 PASS / 0 FAIL / 1 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T111055Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version1.0.0 passed actual Alibaba Express verified CI-image registration, official READY, native Python Sandbox.create, CLI/SDK smoke and **17 strict real-model checks,0 FAIL/0 SKIP** with the explicit compatible qwen3.8-flash model. The real native agent changed source, produced a report and exact artifact, preserved all original tests and passed independent post-return original/held-out evaluations. Owned sandbox/template/registry cleanup and post-runtime image digest were independently verified.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.0.0 | alicloud-express | [SDK-created image](evidence/express-2026-10-20.json), [strict model17](evidence/model-image-2026-10-20T113609Z.json), [model-off HTTP](evidence/image-http-2026-10-20T113609Z.json) |

The separate model-off HTTP controller has9 PASS/1 explicit model SKIP and is not L3. The [actual native step attempt](evidence/verification-steps-2026-10-20T112245Z.json) did not independently reach READY within1200seconds; last official state remained building. No sandbox was created. Owned template deletion and [independent template/sandbox absence recheck](evidence/steps-cleanup-2026-10-20.json) passed. This is a failed step attempt, not step qualification or proof of a universal provider RUN cap. Other providers and every upstream model/backend profile remain unverified.

</details>

## Secondary development

Restore dependencies with python -m venv <new-prefix> then <new-prefix>/bin/python -m pip install --require-hashes -r deepagents/requirements.lock; run pip check. Set DEEPAGENTS_PYTHON to that venv Python (preserve its path rather than resolving its executable symlink). Run python -m pytest -q deepagents/test_commands.py deepagents/test_controller.py. Fixtures use actual installed DeepAgents with authored HTTP/write-tool responses and literal process code, never real generated host commands.

[Platform steps](../docs/platform-steps.md): python scripts/prepare_steps.py deepagents --output /tmp/deepagents-steps prepares; python scripts/run_steps_e2e.py deepagents --timeout 1200 executes. Set E2E_REQUIRE_LLM=1 and E2E_REQUIRE_CLI=1 for strict real-model checks. Preparation or a static output marker is not provider/model acceptance.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [template spec](../docs/template-spec.md) and [design](../docs/design/deepagents.md). Preserve both languages, exact dependency hashes, upstream notices and immutable verification history.

## Issues

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67); template/catalog: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues); SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template wrapper is [Apache-2.0](../LICENSE). DeepAgents and langchain-openai are MIT; preserve their unchanged [DeepAgents license](upstream-LICENSE) and [integration license](langchain-openai-LICENSE). Hash-locked third-party dependencies retain their own notices installed by pip; do not relabel all dependency code as Apache-2.0.

### Current platform-step acceptance

The later [current-version real step receipt](evidence/express-2026-10-20T141151Z.json) and [full external HTTP result](evidence/verification-steps-2026-10-20T141151Z.json) supersede the earlier failed step attempt for current readiness: official READY, actual Python SDK creation, CLI/SDK smoke and 9 HTTP PASS / 0 FAIL / 1 explicit model SKIP passed in 586.639 seconds. Independent owned sandbox/template and temporary private asset-cache cleanup passed. This step receipt is model-free; earlier image/model receipts keep their own scope.
