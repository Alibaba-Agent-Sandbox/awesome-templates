# Copilot CLI

[中文](README.zh-CN.md).

## What it does

Runs the genuine pinned GitHub Copilot CLI with an explicit OpenAI-compatible BYOK endpoint. Each prompt uses private temporary state. File editing requires `allow_write=true`; shell execution, delegation and web tools are absent from the fixed model tool list.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

Alibaba FC generation2 base, Linux x86_64, non-root `user`, `@github/copilot@1.0.100` and the required `@github/copilot-linux-x64@1.0.100` native package. [package-lock.json](package-lock.json) pins integrity for the loader/native packages; npm scripts and other optional architectures are omitted.  Native software uses the separate [upstream license](UPSTREAM-LICENSE.md).

## Problem solved

Expose authenticated named commands, file transfer and sandbox lifecycle around a real terminal coding agent. This BYOK profile does not use a GitHub login or vendor PAT. It requires streaming/tool-call capable Chat Completions from the explicitly configured model endpoint; other upstream provider profiles remain outside this template.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./copilot-cli --yes
abx run <sandbox-id> copilot_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('copilot_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/copilot_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": {"native_version": "1.0.100"}}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

The three model settings are captured at server startup. BYOK type=openai, wire API=completions and transport=http are fixed; token limits65536prompt/4096output. No key-command, extra headers, bearer override, GitHub token or unrelated host credential is forwarded. Native secret-env filtering and wrapper redaction mask the exact key. Only PATH/optional CA paths plus private HOME/XDG/temp/state enter the process. Private profile/cache/log state is removed after identity-pinned process group and marked detached descendants stop; project edits remain. The owned cloud sandbox is the final boundary against malicious code. See [runtime environment](../docs/runtime-environment.md) and [official BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models).

## Resources

2vCPU/2048MB, server9000, optional operator-owned9010. CPU-only Linux x86_64; no GPU/KVM/Docker daemon. Each native invocation may extract a private native cache; it is removed on completion. Deadline1..600seconds plus bounded cleanup; output256KiB per stream. No GitHub service account or predownloaded model weights.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

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
