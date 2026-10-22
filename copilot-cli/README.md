# Copilot CLI

[中文](README.zh-CN.md).

## What it does

Runs the genuine pinned GitHub Copilot CLI with an explicit OpenAI-compatible BYOK endpoint. Each prompt uses private temporary state. File editing requires `allow_write=true`; shell execution, delegation and web tools are absent from the fixed model tool list.

## Stack

Alibaba FC generation2 base, Linux x86_64, non-root `user`, `@github/copilot@1.0.100` and the required `@github/copilot-linux-x64@1.0.100` native package. [package-lock.json](package-lock.json) pins integrity for the loader/native packages; npm scripts and other optional architectures are omitted. The server source pin is e2cb27e24fde0a67112f82b8d44af463445a5d1a. Native software uses the separate [upstream license](UPSTREAM-LICENSE.md).

## Problem solved

Expose authenticated named commands, file transfer and sandbox lifecycle around a real terminal coding agent. This BYOK profile does not use a GitHub login or vendor PAT. It requires streaming/tool-call capable Chat Completions from the explicitly configured model endpoint; other upstream provider profiles remain outside this template.

## Quick start (CLI)

```bash
abx template deploy ./copilot-cli -y
abx create --template <template-id> --timeout 900 -y
abx run <sandbox-id> copilot_version
abx run <sandbox-id> copilot_setup_check
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Deploy/create return the IDs substituted above. Version/setup are model-free. See [client/provider setup](../docs/using-templates.md#client-entry-compatibility). The equivalent native platform-step build uses the same source and owned cleanup:

```bash
python scripts/express_e2e.py ./copilot-cli --build steps --sandbox-create sdk
```

A step pass does not establish a Dockerfile build. The SDK example configures a separate command server because environment on sandbox creation does not reconfigure a prewarmed server.

## Quick start (Python SDK)

Install `agent-sandbox-client` using [pinned source instructions](../docs/python-client-installation.md). Set the three model variables in the operator environment. The template ID is the deploy result.

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
            env={name: os.environ[name] for name in (
                "COPILOT_PROVIDER_BASE_URL", "COPILOT_PROVIDER_API_KEY", "COPILOT_MODEL")})
        result = await server.commands.run(
            "copilot", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_write=True, command_timeout=300, timeout=360)
        if result["exit_code"] != 0:
            raise RuntimeError("Native Copilot failed; inspect private diagnostics")
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

The example starts its own authenticated9010 server, reads the target artifact and destroys its owned sandbox. It is source checked; only the Verified receipts establish execution.

## Quick start (HTTP POST)

Set ABX_SERVER_URL to the SDK-forwarded9010 URL and ABX_SERVER_TOKEN to that server's random token.

```bash
curl --fail-with-body --max-time 360 -X POST "$ABX_SERVER_URL/commands/copilot" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain the existing source","allow_write":false,"command_timeout":300}'
```

HTTP200 returns `{"result":{"stdout":"<native JSONL>","stderr":"","exit_code":0,"native_version":"1.0.100"}}`. Native nonzero status stays in `exit_code`. Authentication401, unknown command404, schema errors400; invalid configuration/path/bounds, overflow or timeout500 with error/type. Buffered output is bounded to256KiB per stream. Client disconnection does not guarantee cancellation.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| copilot_version | none | `{native_version:"1.0.100"}`, actual binary check; no model key |
| copilot_setup_check | none | mode, base_url_set/api_key_set/model_set booleans, github_auth_required=false; no network |
| copilot | prompt:str required,1..32768UTF-8 bytes/no NUL; cwd:str="", existing directory inside WORKSPACE after symlink resolution; allow_write:bool=false; command_timeout:int=300,1..600seconds | stdout:str, stderr:str, exit_code:int, native_version:str |

Read-only tools are exactly view/glob/grep. Explicit editing adds edit/create/apply_patch. `--allow-all-tools` approves only this closed available-tools list; paths/URLs are not globally approved. The native default path policy remains; this is not an OS filesystem jail. Native invocation disables updates, telemetry, builtin MCP, custom instructions, experimental/BASH_ENV features, questions and remote export. No resume, plugins, caller HOME, repo trust opt-in or arbitrary CLI flags are accepted. Arguments use argv, including one literal prompt argument. JSONL is native output, not a promised stable wrapper event schema. Native `session.error` and nonzero exit must be handled by consumers.

The shared server Boolean scalar also accepts true/false/yes/no/1/0 string forms for CLI compatibility; invalid Boolean tests use a value outside that whitelist.

## Configuration

| Name | Required/default | Meaning |
| --- | --- | --- |
| COPILOT_PROVIDER_BASE_URL | model calls/empty | HTTPS, or loopback HTTP for local development; no userinfo/query/fragment; max2048characters |
| COPILOT_PROVIDER_API_KEY | model calls/empty | explicit endpoint credential, max8192characters/no CR/LF/NUL |
| COPILOT_MODEL | model calls/empty | explicit model identifier, max200ASCII characters |
| WORKSPACE | /home/user/app | allowed cwd root |
| ABX_SERVER_TOKEN | operator set | authenticated command server token |

The three model settings are captured at server startup. BYOK type=openai, wire API=completions and transport=http are fixed; token limits65536prompt/4096output. No key-command, extra headers, bearer override, GitHub token or unrelated host credential is forwarded. Native secret-env filtering and wrapper redaction mask the exact key. Only PATH/optional CA paths plus private HOME/XDG/temp/state enter the process. Private profile/cache/log state is removed after identity-pinned process group and marked detached descendants stop; project edits remain. The owned cloud sandbox is the final boundary against malicious code. See [runtime environment](../docs/runtime-environment.md) and [official BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models).

## Resources

2vCPU/2048MB, server9000, optional operator-owned9010. CPU-only Linux x86_64; no GPU/KVM/Docker daemon. Each native invocation may extract a private native cache; it is removed on completion. Deadline1..600seconds plus bounded cleanup; output256KiB per stream. No GitHub service account or predownloaded model weights.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.0; regular image, actual CLI/SDK, complete HTTP 8 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-22T105025Z.json) |
| opensandbox | 1.0.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 8 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T110834Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version1.0.0 passed actual Alibaba Express native steps, official READY, real Python SDK Sandbox.create and CLI/SDK named smoke. The actual native1.0.100 BYOK profile completed **17 strict checks,0 FAIL/0 SKIP** with the explicit compatible qwen3.8-flash model: existing source changed, fresh report/exact nonce artifact created, original tests unchanged, and independent post-return original/held-out evaluations passed on the cloud target. Own project, native private state/secondary listener and outer sandbox/template absence were independently confirmed.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.0.0 | alicloud-express | [SDK-created native steps](evidence/express-2026-10-20T165141Z.json), [strict model17 and cleanup](evidence/native-model-steps-2026-10-20T165141Z.json) |

Actual native L1 image builds39459153252/39459156236 passed separately; no Docker-image cloud registration is inferred from steps. The first overall failed cloud attempt remains [history](evidence/native-model-steps-2026-10-20T164602Z.json):16PASS/1incorrect controller assertion, with genuine model/artifact tests and owned cleanup passing. The corrected complete rerun is the qualification. No generated source executed on operator. Other architectures/providers and interactive/ACP/GitHub-service/resume workflows remain unverified. The catalog stays experimental. See [final engineering verification](../.agents/evidence/verify/2026-10-20-copilot-cli-native-final.md).

</details>

## Secondary development

Use [design](../docs/design/copilot-cli.md), exact native help and pinned lockfile. Revalidate changed CLI versions, flags, licenses and model behavior. Local unit tests execute fixed authored substitutes, never model-generated source. L3 in e2e_test.py requires an explicitly owned remote sandbox; source changes/new artifacts/original tests/held-out checks run there.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), project/document standards and record rules. Keep both languages and pin provenance together.

## Issues

[Issue64](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/64). Missing accounts/model support stay explicit; never substitute an unrelated credential.

SDK/server bugs: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI bugs: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper source: Apache-2.0, [repository license](../LICENSE). The unmodified native GitHub Copilot CLI is under its own [license](UPSTREAM-LICENSE.md), retained in the image and installed package. Its redistribution conditions require an application/service providing material functionality beyond the CLI and prohibit standalone/primary-product redistribution. The authenticated remote API/file-transfer/sandbox service is independently licensed; this template does not relicense the CLI or grant GitHub service access.

Unified non-model full HTTP acceptance also passed8/0/0 in87.661seconds with actual SDK-created steps, public CLI0.4.1 and independently confirmed sandbox/template cleanup: [current controller result](evidence/verification-steps-2026-10-20T171425Z.json), [canonical CLI/SDK](evidence/express-2026-10-20.json). The17-check native model acceptance above remains separate.
