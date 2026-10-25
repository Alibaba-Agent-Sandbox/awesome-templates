# devin

[中文](README.zh-CN.md).

## What it does

Run the original Cognition Devin CLI3000.11.92 through typed bounded named commands in an owned disposable sandbox. The native CLI owns inference and tools; no replacement planner or compatible-model fallback is supplied. Automatic tools require `allow_unsafe_tools=True`.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Alibaba generation2 Linuxx86_64 base, Python3.13 server, original fixed [official archive](https://static.devin.ai/cli/3000.11.92/devin-3000.11.92-x86_64-unknown-linux.tar.gz), original234files/200878983bytes, compressed67245544bytes. SHA256 `2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0` was published by the official platform manifest observed2026-10-21; see [inventory](upstream.json). The server package is pinned in the Dockerfile. Build verifies original archive/per-file hashes without executing it; runtime verifies original root-owned files. Original binaries/docs/manpages retain their own terms.

## Problem solved

Use the real headless program with deterministic installation, explicit permission, private per-call state, bounded output/deadline and owned process cleanup. The historical interactive-login obstacle is handled using the vendor-documented credentials file copied between the user's own machines. That integration is available but authenticated execution is unverified without an account.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./devin --yes
abx run <sandbox-id> devin_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('devin_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/devin_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "devin 3000.11.92 (7f4e64980e22)"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Arguments | Result/side effects |
| --- | --- | --- |
| devin_version | none | Original file identity + actual `--version` string |
| devin_native_check | none | Original `--help`; original_native/headless_print/private_config/explicit_permission/workspace_trust_control booleans |
| devin_setup_check | none | mode/installed/pinned_version/credentials_file_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback; presence only |
| devin | prompt:string required; cwd:string empty; command_timeout:int300; allow_unsafe_tools:boolFalse; model:string empty | Buffered original final stdout; explicit opt-in permits native file/tool actions |

prompt:1..32768UTF8bytes, nonblank/noNUL. cwd:existing resolved directory inside WORKSPACE, at most4096UTF8bytes/noNUL; empty chooses root. command_timeout:integer1..600seconds, booleans rejected. allow_unsafe_tools must be exactTrue. model:empty uses vendor default; otherwise up to200ASCII `[A-Za-z0-9_.:/-]` characters starting alphanumeric. No model availability is inferred. Native `.devin` directories/symlinks in cwd or ancestors are refused unchanged so project config cannot replace the fixed private profile.

Fixed original argv: `--config <private-json> --permission-mode dangerous --respect-workspace-trust false [--model <model>] --print <literal-prompt>`, with project cwd. Config disables updates/subagents/imports from other agents; private HOME/config/data/cache/TMP isolates user state. Original dangerous mode uses the owned outer sandbox; no nested sandbox/auth-bypass/cloud mode is enabled.

Success requires original exit0 and nonempty stdout, returning stdout, empty stderr, exit_code0, native_completed:true, native_version, archive_sha256, permission_profile:explicit-owned-sandbox-bypass and requested_model. This original version's print mode is plain text, so native_completed records process completion only; an actual code/artifact/model result needs the independent remote controller. Nonzero/empty/timeout/overflow is an error; no partial success. No arbitrary extra argv or subprocess shell interpolation.

## Configuration

| Setting | Default/requirement | Meaning |
| --- | --- | --- |
| DEVIN_CREDENTIALS_FILE | empty; optional for diagnostics/error-path, required for account tasks | Authored wrapper input path captured at module import; absolute, outside WORKSPACE, regular nonsymlink owned by root/current UID, no group/other permissions,1..65536bytes valid UTF8TOML |
| WORKSPACE | /home/user/app | Captured existing project root |
| ABX_SERVER_TOKEN | required; empty declaration | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

A missing original account file reaches original print and preserves its explicit login refusal; no interactive login, made-up DEVIN_API_KEY, root model key or fallback planner is used. The subprocess receives minimal private state environment without operator/model/cloud credentials or the source credential path. Known credential TOML string values, server Bearer/private HOME/source path are redacted in returned stdout. Native errors omit raw output. One operation per server process; overlap returns busy.

Each stdout/stderr stream is bounded256KiB; command1..600seconds plus up to90seconds owned descendant cleanup. Set client timeout at least command_timeout+120seconds. Same OS user/tool permissions are not a multi-tenant filesystem security boundary. Use owned disposable sandboxes with explicitly trusted task content; the native program can execute tools under that account.

## Resources

Linuxx86_64 only, nonroot user,2vCPU/4096MB/port9000; build enforces rootfs<=8GiB. Original package200.9MB, compressed67.3MB. No KVM/Docker/GPU/desktop requirement is claimed. Account execution needs authorized vendor egress/account/CLI role. PeakRSS/authenticated throughput, other architectures/providers, interactive/resume/cloud/ACP/MCP/plugins/delegation remain unverified.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python -m pytest -q devin/test_commands.py devin/test_controller.py devin/test_install.py
python scripts/check_template.py devin --strict
python scripts/check_docs.py
```

Keep original bytes/notices, exact manifest digest, explicit permissions, input credential isolation and cleanup. Publish all changed COPY/helper source before immutable step preparation; generic300MiB and15000wire limits remain. Full external controller requires actual original no-account HTTP+SDK refusal. With a genuine account, explicitly opt into the owned-remote coding controller: existing source edit, unchanged original3tests, report/exact nonce,3original+4held-outs/fresh post-return ACK. Generated code never executes on the operator.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standard](../docs/documentation-standards.md) and [specification](../docs/template-spec.md). Keep standalone source, typed contract, bilingual docs/design/catalog and indexed actual evidence consistent. Required latest-head CI/review and normal pinned merge apply.

## Issues

[Issue72](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Vendor login/model behavior belongs to Cognition. Never attach credentials/private transcripts.

## License

Authored template Apache-2.0. Original Cognition software/docs/manpages retain separate terms; see [notice](UPSTREAM-NOTICE.md). No original binary/source is committed or relicensed; no vendor endorsement/independent redistribution grant is asserted.
