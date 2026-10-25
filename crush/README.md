# Crush

[中文](README.zh-CN.md).

## What it does

Runs the official native Crush0.98.1 terminal agent using an explicitly configured OpenAI-compatible provider. Default turns expose no tools; allow_tools=true exposes exactly bash/edit/multiedit/view/write/ls/glob/grep. Subagent, MCP, network-fetch, background-job and LSP tools are disabled.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

Alibaba FC generation2 CPU/non-root base, published server package. Official GNU Linux x86_64/aarch64 archives are fixed by byte length and SHA256 in [assets.json](assets.json), source [8b1824282eccc78cc62c188c245cf375230a18ce](https://github.com/charmbracelet/crush/tree/8b1824282eccc78cc62c188c245cf375230a18ce). An arm64 pin is not arm64 execution evidence.

## Problem solved

Run genuine terminal coding in an owned sandbox with explicit model settings and private per-turn configuration/data. This is the compatible-provider CLI profile; interactive UI, saved caller configuration and every upstream provider are outside its scope.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./crush --yes
abx run <sandbox-id> crush_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('crush_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/crush_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.98.1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| ABX_SERVER_TOKEN | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| CRUSH_BINARY | diagnostics | image PATH | binary override; actual version still checked |

Private HOME/XDG/CRUSH config/data and correct native disable-default-providers/auto-update flags prevent loading caller global state. Existing .crushrc/crushrc/.crush.json/crush.json between cwd and the nearest Git worktree root are refused before a native run, because upstream automatically loads them. Caller configuration is preserved. With no Git root, upstream checks cwd only. Only PATH/optional CA settings plus private runtime settings enter children; cloud/GitHub/server keys are excluded. The selected key/base URL enter the private0600 config, are never prompt argv, and exact values are redacted from returned diagnostics. Project output can still contain project secrets.

## Resources

2vCPU/2048MB, command9000 and optional explicit9010. ~26.8MB compressed x64 asset,240-second download/30-second socket bounds; executable400MiB max, separate8GiB rootfs build gate. Prompt256KiB, each output256KiB, wall limit1..1800seconds plus bounded teardown. No native max-turn flag is claimed; per-response8192 tokens and the wall deadline bound execution. Private conversation/config/data are removed after each call; project edits remain caller-owned.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Install with python crush/install_runtime.py --prefix <new-private-prefix>. Run python -m pytest -q crush/test_commands.py crush/test_controller.py with the actual pinned executable on PATH. Fixtures use authored HTTP/tool responses and literal process programs, not real models on the operator host.

Prepare [platform steps](../docs/platform-steps.md) using python scripts/prepare_steps.py crush --output /tmp/crush-steps; preparation alone is not execution. Actual basic step acceptance: python scripts/run_steps_e2e.py crush --timeout 1200. Required real-model controller flags are E2E_REQUIRE_LLM=1 and E2E_REQUIRE_CLI=1; no response-only marker establishes L3.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [spec](../docs/template-spec.md), [design](../docs/design/crush.md) and both language contracts. Preserve immutable upstream/source and actual verification records.

## Issues

[Template Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65); [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template wrapper code is [Apache-2.0](../LICENSE). Crush0.98.1 is **FSL-1.1-MIT**, not currently MIT or an OSI-approved open-source release. Preserve and review the exact [upstream license](upstream-LICENSE.md), future-license date and restrictions; do not infer unrestricted commercial redistribution. The unmodified official binary and all bundled notices are installed intact; model weights are not included.
