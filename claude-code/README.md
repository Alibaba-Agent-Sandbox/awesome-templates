# claude-code

## What it does

Run unchanged official Claude Code2.0.76 headless planning and Read/Edit/Write/Bash tools. Existing `claude` retains its Anthropic-oriented API; new `claude_byok` explicitly uses an authored Messages-to-OpenAI-Chat text/tool adapter. Compatible-model use is experimental and [not supported by Anthropic](https://code.claude.com/docs/en/llm-gateway); no Claude-model/subscription/vendor endorsement claim.

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13/Node20; original npm package2.0.76 from its SHA512 integrity lock; exact original cli.js SHA256 in [upstream.json](upstream.json). `npm ci --omit=optional --ignore-scripts` excludes optional image codecs and package hooks. Original CLI, embedded tool code and bundled notices remain unchanged. Server source34e7e011c5569f77b7f605e65313be7498f6cf02, authored stdlib adapter/process ownership. [Dockerfile](Dockerfile), [license notice](UPSTREAM-NOTICE.md), [design](../docs/design/claude-code.md).

## Problem solved

Expose original native tool execution through SDK/HTTP, with a new explicitly selected compatible text/tool profile when the approved gateway only provides Chat. The adapter translates protocol messages, preserves original tool names/arguments/results and leaves tool execution to the original CLI. It does not implement another planner or forward credentials to a default vendor.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
abx --provider alicloud-express template launch ./claude-code --workflow application --yes
abx run <sandbox-id> claude_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('claude_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/claude_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "2.0.76 (Claude Code)"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| claude_version | none | Original CLI `2.0.76 (Claude Code)`; no model |
| claude_native_check | none | Original cli.js hash and help flags: original_native/isolated_settings/no_session_persistence/strict_mcp booleans |
| claude_setup_check | none | Mode and model_key_set/model_base_set/model_set presence, vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true; no values/network |
| claude_byok | prompt: required string1..32768UTF8bytes/nonempty/noNUL; cwd: default empty string, max4096bytes, existing resolved directory within WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected; allow_unsafe_tools: booleanFalse default, must explicitly be True for this disposable-sandbox bypass profile | stdout/exit_code0/native_completed/native_version/cli_sha256/model/permission_profile/protocol/model_calls/native_tool_results/relay_calls. Original tools edit project; no raw transcript |
| claude | prompt: required nonempty string; model: string default sonnet; cwd: string default empty/contained existing directory; allowed_tools: string default Read,Edit,Write; resume: string default empty; command_timeout: integer300/range1..900seconds | Legacy original JSON encoded as a string, sanitized for environment secrets. Uses existing Anthropic credential/settings behavior; bounded isolated BYOK guarantees do not certify this legacy mode |

New BYOK requires explicit allow_unsafe_tools=True; False/missing fails before a model call. It selects the outer owned disposable sandbox as the execution boundary and the original CLI permission bypass option for only its four visible tools. Legacy claude remains dontAsk. Original-native success/zero failed responses/artifact and cleanup gates remain mandatory; no cause of earlier disconnected native requests is presumed.

New fixed profile: `-p --model <selected> --output-format json --dangerously-skip-permissions --tools Read,Edit,Write,Bash --allowedTools Read,Edit,Write,Bash --settings <owned> --setting-sources '' --no-session-persistence --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --no-chrome --max-turns16`. Hooks disabled, thinking tokens0; no Task tool, subagents, MCP, plugin or project/local settings loading. Project instructions remain untrusted input; use only an owned disposable target.

Text and original tool schemas/results are translated; unsupported image/thinking/content/tool types, truncated replies, wrong model/token/path and redirects fail closed. Upstream Chat is buffered then emitted as native Messages SSE.32requests/2MiBrequest/4MiBresponse maximum,16native turns,256KiB each native stdout/stderr. Actual native successful result and positive completed transport counts are required. Coding qualification additionally requires positive native tool results and independently downloaded files/tests. Own process/private state and issued RPCs drain before return; cleanup may add up to210seconds, client timeout at least command_timeout+240. Concurrent BYOK calls fail busy.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| CLAUDE_MODEL_API_KEY | empty; required for BYOK | Explicit approved compatible upstream key; parent adapter only |
| CLAUDE_MODEL_BASE_URL | empty; required for BYOK | HTTPS Chat base/no userinfo/query/fragment/max2048chars; literal-loopback HTTP for fixed fixtures |
| CLAUDE_MODEL | empty; required for BYOK | Selected model1..200identifier characters |
| ANTHROPIC_API_KEY | empty; legacy mode only | Existing Anthropic-compatible legacy configuration; not silently reused by BYOK |
| WORKSPACE | /home/user/app | Existing project root |
| ABX_SERVER_TOKEN | Required; empty manifest declaration | Export the independent application token before launch |

New settings captured at module import. Key max8192/no control characters; no default provider/model/key fallback. Native/tool environment gets only an ephemeral local adapter token and minimal private HOME/config/cache; real upstream key remains in the parent and is sent only to exact configured Chat origin. Original command results and error messages omit credentials/private endpoints/transcripts. Same-user OS access remains; environment filtering/cwd containment is not another tenant boundary. Legacy resume/settings behavior is retained and outside BYOK isolation claims.

## Resources

Declared2vCPU2048MB, Linuxx64, port9000,8GiB image rootfs budget; no KVM/Docker/GPU/display requirement. Official npm archive26.4MB/original package70.9MB, Node20 already in base. Approved model egress required; optional image codecs omitted. Peak memory not measured. Full Claude service, OAuth/subscription, interactive/resumed sessions, images/thinking/MCP/plugins/delegation remain unverified.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q claude-code/test_byok.py claude-code/test_adapter.py
python scripts/check_template.py claude-code --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py claude-code --sandbox-create sdk --http
```

Keep original package and notices, lockfile/integrity/hash, explicit approved origin, no real child key, unsupported-feature refusal and owned descendants/listener/private cleanup. Fixed non-executable protocol replies may run locally. Original native/generated-code verification runs only on a fresh owned cloud target; preserve original tests and independently assert artifacts and post-return held-outs.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include bilingual docs, owner note/evidence and current-head review/checks.

## Issues

[Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15), [template defects](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses its support channels. Never attach credentials or private transcripts.

## License

Authored template/adapter: [Apache-2.0](../LICENSE). Original Anthropic package remains all rights reserved under its [original terms/notices](UPSTREAM-NOTICE.md); no relicensing or vendor endorsement.

Template1.3.1 records cancelled_auxiliary_responses separately only for peer disconnect after a complete upstream reply to the pinned original asynchronous Bash file-path request (no tools, one user command/output, SHA256-bound fixed system text). The original CLI explicitly ignores its aborted request. Main/unknown requests, upstream timeouts/errors and all other failures still reject completion; completed_required_responses must be positive. A cancelled optional request is not counted as delivered or as a passing model call. Independent coding/artifact/post-return tests remain mandatory. Current source requires fresh acceptance.
