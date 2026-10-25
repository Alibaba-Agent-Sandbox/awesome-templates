# gemini

## What it does

Run original official Google Gemini CLI0.64.0 planning and text/file/shell tools. Existing gemini/setup/version APIs remain; gemini_byok adds explicit compatible Chat transport through an authored GenerateContent-to-Chat text/tool adapter. Original CLI/tool engine is unchanged; Google Gemini model access, OAuth, hosted subscriptions and full feature compatibility are not claimed. [Official configuration](https://geminicli.com/docs/reference/configuration/).

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

Alibaba generation2basev0.0.49/Linuxx64/Python3.13/Node20; original npm0.64.0/SHA512 integrity lock; all449original package files/98597935bytes independently SHA256-pinned in [upstream.json](upstream.json), archive20841287bytes/SHA256891a794e55c8319b6b78f6f8f13d6b8b2782a4709dfd2fcabf3a1f63ae8365e6. `npm ci --omit=optional --ignore-scripts` omits interactive native PTY/keychain add-ons and scripts. Original bundled notices/code remain unchanged. Published server package, stdlib authored adapter/process controls. [Dockerfile](Dockerfile), [design](../docs/design/gemini.md), [notice](UPSTREAM-NOTICE.md).

## Problem solved

Give an explicitly approved Chat gateway access to original Gemini text/tool planning without sending its key to a default Google endpoint. The adapter translates original function schemas, arguments and correlated results; it does not execute tools or replace the native planner. Native API environment variables select only the owned local adapter, with a fresh token and no real child key.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./gemini --yes
abx run <sandbox-id> gemini_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('gemini_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/gemini_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.64.0"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| gemini_version | none | Original CLI0.64.0; no model |
| gemini_native_check | none | Exact original449file identity plus actual help flags original_native/headless_json/explicit_approval/owned_project_include |
| gemini_byok_setup_check | none | mode/model_key_set/model_base_set/model_set, vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true; no values/network |
| gemini_byok | prompt required nonempty1..32768UTF8bytes/noNUL; cwd default empty string/max4096bytes/existing resolved directory within WORKSPACE; command_timeout integer1..600seconds/default300/no bool; allow_unsafe_tools booleanFalse, must explicitly be True on an owned disposable sandbox | stdout/exit_code0/native_completed/permission_profile:explicit-owned-sandbox-bypass/native_version/archive_sha256/model/protocol/model_calls/native_tool_results/relay_calls; native tools modify caller project; no raw transcript |
| gemini_setup_check | none | Legacy installed/version/pinned_version/key/model presence/workspace/settings path/existence/JSON-validity inspection; no changes/authentication |
| gemini | prompt required nonempty string; model default empty string then GEMINI_MODEL then gemini-3.1-flash-lite; cwd default empty/contained existing directory; command_timeout integer600/range1..1800seconds; yolo booleanFalse | Legacy original buffered JSON string. yoloFalse selects plan, True explicitly permits tool execution. Requires GEMINI_API_KEY, no implicit OpenAI-key/OAuth fallback. New BYOK isolation guarantees do not certify legacy mode |

New fixed profile: --prompt/--model/--output-format json/--approval-mode yolo/--include-directories <contained-project>. Launch cwd is a fresh private directory; prompt includes absolute project path. Hash-pinned root-owned /opt/gemini/profile.json system settings force gemini-api-key auth,16model session turns, hooks/skills/subagents/update/telemetry disabled, no configured MCP/installed extensions. Original core tools are read_file/write_file/replace/run_shell_command/list_directory/glob/grep_search. No delegation tool. Native original file/tool code executes only on an owned disposable sandbox; project instructions remain untrusted input.

Translate only text and original function declarations/results with exact IDs or deterministic same-history name correlation when native IDs are absent. Google schema type case/nullability is mapped explicitly. Unsupported images/thinking/content/tool types, mismatched results, truncated replies, wrong model path/token and redirects are refused. Upstream Chat is buffered and emitted as original GenerateContent SSE; actual usage comes from upstream.32requests/2MiBrequest/4MiBresponse/16native turns,256KiB each stdout/stderr; command deadline plus up to90seconds owned cleanup, client timeout at least command_timeout+120. Concurrent BYOK returns busy. Completion requires original successful nonempty response, completed upstream requests and no failed responses; coding also requires positive native tool results and independent artifacts/tests.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| GEMINI_BYOK_API_KEY | empty; required for BYOK | Explicit compatible upstream key, parent adapter only |
| GEMINI_BYOK_BASE_URL | empty; required for BYOK | HTTPS Chat base/max2048chars/no userinfo/query/fragment; literal-loopback HTTP for fixtures |
| GEMINI_BYOK_MODEL | empty; required for BYOK | Actual selected identifier1..200allowed characters |
| GEMINI_API_KEY | empty; legacy only | Existing Google/native-compatible key; BYOK never silently reuses it |
| GEMINI_MODEL | gemini-3.1-flash-lite; legacy only | Existing legacy default; separate from explicit BYOK selection |
| WORKSPACE | /home/user/app | Existing caller project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

BYOK settings captured at module import; key max8192/no control characters. Native environment has only fresh local adapter token, minimal PATH and private HOME/config/cache; real upstream key is sent only to exact approved Chat origin. Same-user OS access remains; cwd/environment filters are not another tenant boundary. Existing legacy configuration behavior stays separate. No private endpoints/keys/transcripts in results or errors.

## Resources

Declared2vCPU4096MB/Linuxx64/port9000/8GiBrootfs budget; no KVM/nested Docker/GPU/display. Original package98.6MB, Node20 already in base; optional interactive add-ons omitted. Approved model egress required. Peak memory, image cloud deployment, other providers, Google OAuth/subscription, full interactive/resume/PTY/image/thinking/MCP/plugin/delegation product not certified.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q gemini/test_byok.py gemini/test_adapter.py gemini/test_controller.py gemini/test_commands.py gemini/test_e2e_protocol.py
python scripts/check_template.py gemini --strict
python scripts/check_docs.py
python scripts/run_steps_e2e.py gemini
```

Preserve exact original inventory/lock/notices, real-key isolation, strict origin and content refusal, owned process/RPC/private/listener cleanup. Local replies are fixed non-executable fixtures; original native/generated-code acceptance only on fresh explicitly owned cloud. Main e2e dispatches strict current BYOK controller; legacy helpers/regressions remain. Record both dispatch and byok_e2e_test.py hashes. Require changed source, original3test bytes/report/exact nonce/original3+4held-outs/fresh post-returnACK and independent owned absence.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include owner note/evidence, bilingual contracts, latest-head review/checks and normal merge.

## Issues

[Issue30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses upstream channels. Never attach credentials/private transcripts.

## License

Authored template/adapter and original Gemini CLI are Apache-2.0 under their respective original [licenses/notices](UPSTREAM-NOTICE.md); retain bundled third-party terms. [Repository license](../LICENSE). No Google endorsement or hosted model access claim.

The text/tool adapter accepts only the original CLI fixed `skip_thought_signature_validator` placeholder on function calls and removes that metadata during translation. Other thought signatures and thinking content remain unsupported and rejected.

Current2.2.0 requires explicit `allow_unsafe_tools=True` (`true` in JSON) before configuration/native/model execution; missing/false/nonboolean values are refused. This matches setup_check.requires_unsafe_optin. Earlier2.1.4 actual native/API/model/image passes are historical for the changed permission profile; current2.2.0 actual native/API/model acceptance is recorded above.
