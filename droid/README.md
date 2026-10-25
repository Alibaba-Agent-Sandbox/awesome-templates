# Factory Droid

## What it does

Template1.2.0 adds `droid_byok`: the genuine fixed CLI uses an explicit compatible provider without a Factory account. The existing `droid` Factory-account command remains available. Both use private per-call state and bounded owned process cleanup. Current1.2 native SDK/Express/BYOK acceptance passed as recorded below; older receipts retain historical scope.

Run Factory Droid 0.241.1 headlessly on an existing project. Named commands expose a bounded coding call, the installed version, and a setup inspection without calling a model.

## Stack

Official npm `@factory/cli@0.241.1` plus `@factory/cli-linux-x64@0.241.1`, full npm integrity [lock](package-lock.json), unmodified native SHA256 `1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1`, Alibaba FC base, Python3.13 and immutable servere2cb27e. Install hooks are disabled; execute the fixed native binary directly. SHA256 is checked at build and every native command. [Provenance](upstream.json), [upstream notice](UPSTREAM-NOTICE.md), [Dockerfile](Dockerfile). Native metadata is proprietary `UNLICENSED`; its repository field does not establish a public source commit. Non-root `user`, generation2, port9000.

## Problem solved

An automation can upload a project, ask Droid to edit it, inspect files, and run independent tests through Agent Sandbox. Legacy Factory mode refuses missing account credentials before launching login; BYOK requires its separate compatible settings. `WORKSPACE` controls the project root; success and error text redact configured secret values.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./droid --yes
abx run <sandbox-id> droid_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('droid_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/droid_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "0.241.1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result / upstream call |
| --- | --- | --- |
| `droid_byok` | Required `prompt: str`,1–32768 UTF-8 bytes, nonempty/no NUL; `cwd: str=""`, at most4096 bytes, existing resolved workspace directory; `command_timeout: int=300`,1–600seconds, bool refused | Object: native `stdout`, `stderr`, `exit_code`, `native_version`. Fixed `droid exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`; task via anonymous stdin. Modifies the selected project; private state removed on every path. |
| `droid_byok_setup_check` | None | Model/base/key presence booleans, `mode: openai-compatible-byok`, `factory_account_required: false`; no model request or secret values. |
| `droid_version` | None | Version string from `droid --version`; no model key needed. |
| `droid_setup_check` | None | Object with `installed` (bool), `package`, `version`, `expected_version` (strings), `api_key_set`, `workspace_exists`, `auto_update_enabled` (bool). No model call; no key values returned. |
| `droid` | `prompt`: required nonempty string; `auto`: string, default `low`, one of `""`, `low`, `medium`, `high`; `cwd`: string, default `""`, existing directory within `WORKSPACE`; `command_timeout`: integer, default 300, range 1–600 seconds | Buffered stdout string from `droid exec [--auto LEVEL] -- PROMPT`. Nonzero exit or timeout raises a sanitized execution error. |

Relative `cwd` resolves from `WORKSPACE`. Absolute paths must remain inside that root after symlink resolution. `auto=""` omits the flag and uses upstream read-only mode; `low` allows project edits, `medium` also allows development commands, and `high` allows riskier operations. The template never passes `--skip-permissions-unsafe`. **Compatibility:** 1.1.0 uses `/home/user/app` instead of `/app` and defaults the coding command to explicit `--auto low`; use `auto=""` for the previous read-only behavior.

Version1.2.0 adds BYOK without changing legacy arguments. Native paths are fixed and SHA256-checked; output is limited256KiB per stream. Both modes exclude operator cloud/GitHub credentials, use private HOME and identity-pinned group/nonce/pidfd cleanup on success, failure, overflow and timeout. BYOK always uses low autonomy and does not enable unsafe permission bypass. The native process starts in a private temporary Git root; anonymous task context identifies the selected project by absolute path. This prevents project `.factory` settings from affecting model routing; target project native configuration is not loaded automatically. Pass private runtime settings with the pinned `--settings` flag. Only original native file tools Read/Edit/Create/Grep/Glob/LS are enabled; no Execute, subagent or MCP tools. Project files remain caller-owned; cwd selection is not an OS security boundary.

## Configuration

This subprocess lifecycle requires Linux. The command closes its owned process group on success and error as well as at the deadline. It drains both output pipes while keeping the leader unreaped until group cleanup, so redirected background descendants cannot outlive a completed command.

| Name | Default | Purpose |
| --- | --- | --- |
| `DROID_MODEL_API_KEY` | Empty; required for BYOK | At most8192 characters, no CR/LF/NUL; private native environment only. |
| `DROID_MODEL_BASE_URL` | Empty; required for BYOK | Explicit HTTPS compatible base, at most2048 characters, no userinfo/query/fragment; literal local HTTP only for fixtures. |
| `DROID_MODEL` | Empty; required for BYOK | Explicit1–200-character model identifier. |
| `FACTORY_API_KEY` | Empty | Factory account API key, injected at creation. Required only for `droid`. |
| `ABX_SERVER_TOKEN` | empty | Export an independent application token before the application workflow launch; separate from model and gateway credentials |
| `WORKSPACE` | `/home/user/app` | Existing project root; an invalid explicit root fails. |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | Forced off in subprocesses to preserve the pin. |

Factory credentials are obtained from [Factory API key settings](https://app.factory.ai/settings/api-keys). A DashScope or OpenAI key is not a replacement for `FACTORY_API_KEY`. `droid_byok` instead uses a private native `customModels` entry, provider `generic-chat-completion-api`, explicit model/base and `apiKey: "${ABX_DROID_MODEL_KEY}"`. The real key is not written into settings or argv. Native selection uses the configured custom model; no Factory key, interactive login or alternate binary is injected. Key/base values are redacted from native output; private state is deleted. [Official BYOK docs](https://docs.factory.com/model-independence/byok); exact0.241.1 behavior was checked with a synthetic-only fixed response, not a real-model acceptance. Upstream behavior is documented in [Droid Exec](https://docs.factory.com/droid-exec/overview); the exact pinned CLI help is the authority for flags. Redaction covers raw and JSON-escaped configured secret values in stdout and error messages. Agent-written project files still require normal secret hygiene. The cwd constraint selects the project and is not an operating-system security boundary.

## Resources

Default: 2 vCPU, 2048 MB RAM, port 9000. BYOK calls require your configured model service; legacy Factory calls require external Factory access. The platform starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py` and probes `agent-sandbox-server healthcheck --port 9000`.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

Keep the Alibaba base, exact CLI/server pins and non-root user. Extend [commands.py](commands.py) through `@command`; pass argv directly and keep secret redaction, key guards and deadline cleanup. Build with BuildKit; deployment may inject a server wheel. Run:

```bash
python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py droid/test_byok.py droid/test_model_controller.py
python3 scripts/check_template.py droid
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py droid
```

Source-only local execution explicitly skips the missing native version; it cannot qualify the provider. L1 builds the actual Dockerfile and checks the real native SHA/version. Required L2 uses actual SDK creation, canonical steps, full HTTP and independent owned cleanup. L3 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1` runs [e2e_test.py](e2e_test.py) on a fresh owned cloud server configured for BYOK: real native successful JSON with positive turns, exact fresh final nonce, existing source edit, new artifacts, byte-identical original tests, complete independent original and held-out post-return checks with fresh ACKs, and owned project absence. Generated code never runs on the operator. Legacy Factory controller is retained separately as [factory_e2e.py](factory_e2e.py), requiring a genuine Factory key; no such current model pass is claimed.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py droid` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Read [CONTRIBUTING.md](../CONTRIBUTING.md), the [template spec](../docs/template-spec.md), and the [design](../docs/design/droid.md). Keep this README and [Chinese README](README.zh-CN.md) synchronized; include regression tests, engineering records and actual evidence with a scoped PR. Keep the catalog experimental until required acceptance passes.

## Issues

Continue [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19). Report template defects in [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server defects in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), or CLI defects in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include versions, provider, generation and sanitized reproduction; never include keys or raw private logs.

## License

Template source: [Apache-2.0](../LICENSE). Factory Droid is distributed separately under its upstream terms; installing the CLI does not relicense it.

### 2026-10-20 full step checkpoint: template1.1.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155022Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/0 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).

The changed runtime retains the proprietary [upstream notice](UPSTREAM-NOTICE.md).
