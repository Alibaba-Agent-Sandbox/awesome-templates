# Cursor Agent

[中文](README.zh-CN.md).

## What it does

Run the original Cursor Agent CLI in an owned disposable sandbox through typed named commands. Cursor owns inference and tool execution. A genuine CURSOR_API_KEY is required for agent tasks; no compatible-model or operator-key fallback exists. Automatic native tools require explicit `allow_unsafe_tools=True`.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Original official CLI2026.10.19-6bbf2c4 for Linux x86_64, including its original bundled Node/launcher/native modules. The unchanged183,733,394-byte archive has controller-measured SHA256 `cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f`; this is not an upstream-published checksum. The460regular-file inventory totals585,886,062bytes. Python3.13 and the Alibaba generation2 base; published server package. See [original metadata](upstream.json), [notice](UPSTREAM-NOTICE.md) and [design](../docs/design/cursor-agent.md).

## Problem solved

Provide a reproducible headless Cursor installation, a scalar SDK/HTTP interface and bounded execution with owned process/private-state cleanup. This is a local CLI profile; it does not provision Cursor Cloud Agents or an enterprise machine scheduler. Authenticated coding/model behavior remains unverified until a genuine vendor-key run exists.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./cursor-agent --yes
abx run <sandbox-id> agent_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('agent_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/agent_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "2026.10.19-6bbf2c4"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| agent_version | none | Fixed native version string; validates all original files before running --version |
| agent_native_check | none | original_native/headless_print/json_output/explicit_force/contained_workspace booleans; original --help; no model |
| agent_setup_check | none | mode/installed/pinned_version/api_key_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback; presence only, no values/network |
| agent | prompt required string; cwd string default empty; command_timeout integer300; allow_unsafe_tools booleanFalse; model string default empty | Buffered original final; may read/write/run tools only after explicit opt-in |

`prompt`:1..32768UTF8bytes, nonempty/no NUL. `cwd`: existing resolved directory inside WORKSPACE, max4096UTF8bytes/no NUL; empty selects WORKSPACE. `command_timeout`:1..600seconds, booleans rejected. `allow_unsafe_tools`: only exactTrue proceeds. `model`: empty retains the vendor-selected default; otherwise max200ASCII identifier characters `[A-Za-z0-9_.:/-]`, beginning alphanumeric; no model availability claim.

Successful `agent` returns stdout:string, stderr:empty string, exit_code:0, native_completed:true, native_version, archive_sha256, permission_profile:explicit-owned-sandbox-bypass and requested_model. Original native JSON must be type=result/subtype=success/is_error=false with nonempty final. Nonzero, malformed/incomplete output, timeout or overflow raises an error; no partial-success string is returned. Actual selected-model behavior and coding artifacts require their separate test.

Fixed original argv: --print --output-format json --disable-auto-update --disable-project-configs --sandbox disabled --trust --force --workspace <contained-project>, optional --model, literal prompt. The external owned sandbox supplies isolation; original nested sandboxing is disabled for this explicit profile. All arguments are passed as argv. No arbitrary flags, authentication bypass, default operator credential fallback or replacement planner is exposed.

## Configuration

| Variable | Default / requirement | Meaning |
| --- | --- | --- |
| CURSOR_API_KEY | empty; required for agent | Genuine vendor credential captured when the server imports commands |
| WORKSPACE | /home/user/app | Contained project root, captured at import |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the template launch; separate from model and gateway credentials |

Original programs receive a minimal environment with only their explicit vendor key and private HOME/config/data/cache/TMP paths. Updates and project configuration loading are disabled by pinned original flags; OS keychain/persistent native sessions are not used. Per-call native state is removed after success/error/timeout. The server process and native tools share an OS user; these paths are not another tenant boundary. Use a fresh caller-owned disposable sandbox for automatic tools.

At most one agent operation per server process; concurrent calls fail busy. Stdout/stderr are each bounded256KiB, command deadline1..600seconds plus up to90seconds cleanup; client timeout should cover command_timeout+120seconds. Known key/command-token/private-home values are redacted. No private transcript or provider ID belongs in public evidence.

## Resources

Linux x86_64 only;2vCPU/4096MB/port9000, non-root user, WORKSPACE=/home/user/app,8GiB rootfs ceiling checked during build. Original bundle585.9MB; archive183.7MB. No nested Docker, KVM, GPU or desktop requirement is claimed. Vendor egress/account are required for model tasks; peak RSS and authenticated throughput are unmeasured. Other architectures/providers, interactive/resume/MCP/plugins/delegation/cloud-agent features are not certified.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q cursor-agent/test_commands.py cursor-agent/test_controller.py cursor-agent/test_install.py
python scripts/check_template.py cursor-agent --strict
python scripts/check_docs.py
```

Preserve original file hashes/notices, explicit permission, private state and owned cleanup. Publish all changed COPY/helper sources before immutable step preparation; retain15000wire bytes and the generic300MiB archive limit. The full external controller requires actual original HTTP and SDK invalid-key refusal; install/version-only receipts cannot qualify. With a genuine vendor key, explicitly opt into the owned-remote coding controller: existing source edit, unchanged original3tests, report/exact nonce,3original+4held-outs/fresh post-return ACK. Generated code never runs on the operator.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [spec](../docs/template-spec.md). Keep the standalone profile, typed contracts, bilingual docs/design/catalog, owner records and current-source evidence together. Use latest-head CI/review and normal pinned merge.

## Issues

[Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Upstream behavior belongs to Cursor. Do not attach credentials/private transcripts.

## License

Authored template Apache-2.0. Original Anysphere software and bundled third-party licenses retain their own terms/notices; see [notice](UPSTREAM-NOTICE.md). No vendor endorsement or redistribution of its binary/source in this Git repository is asserted.
