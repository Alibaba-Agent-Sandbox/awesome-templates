# DeepAgents

[中文](README.zh-CN.md).

## What it does

Runs actual DeepAgents0.7.25 with a local file/shell backend and explicit OpenAI-compatible chat model. Default requests expose zero tools. Explicit allow_tools=true enables exactly ls/read_file/write_file/edit_file/glob/grep/execute/delete. General-purpose and explicit subagents are disabled; task/delegation is absent.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba FC base, generation2/non-root, pinned servere2cb27e. [requirements.lock](requirements.lock) fixes every resolved dependency and SHA256, including [DeepAgents0.7.25](https://pypi.org/project/deepagents/0.7.25/) and langchain-openai1.7.2. Generated from [requirements.in](requirements.in) using uv0.11.28 for Python3.13. Image pip verifies hashes and runs pip check. No remote E2B/OpenSandbox backend or model weights.

## Problem solved

Run the genuine LangChain Deep Agent inside an owned cloud sandbox without asking it to create another sandbox. An explicit Python driver uses the supported API; no unverified console script is assumed. Each call gets a fresh process/model/profile and private HOME/data, preserving caller state.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./deepagents --yes
abx run <sandbox-id> deepagents_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('deepagents_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/deepagents_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.7.25"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| ABX_SERVER_TOKEN | yes | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

The selected model settings remain in private stdin only, never inherited as environment by generated shells. Child runtime receives PATH/optional CA plus private HOME/XDG and disabled LangSmith tracing. LocalShellBackend gets only PATH/HOME/locale and the random non-secret process ownership marker, no inherited model/cloud/GitHub/server credentials. No skills/memory/profile files are loaded. The backend's virtual filesystem maps tool paths inside cwd; shell execution still has the sandbox user's full authority and is not restricted by that mapping.

## Resources

2vCPU/2048MB, server9000, optional SDK-started9010; CPU Linux Python3.13. Hash-locked dependency venv /opt/deepagents, separate8GiB image-rootfs gate. Task256KiB, each output256KiB; wall1..1800seconds plus bounded identity-pinned process/group cleanup. Private configuration/conversation data removed after every call; project edits remain until caller cleanup. The owned sandbox is the final boundary for malicious same-UID code or interrupted server cleanup.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

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
