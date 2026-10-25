# Qoder

## What it does

Run the real Qoder coding assistant headlessly against files in a sandbox. The existing `qoder_run` Python script command remains available.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

Qoder CLI `@qoder-ai/qodercli@1.1.72`; platform Python 3.13 / Node.js 20; Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://docs.qoder.com/cli/run-in-scripts)

## Problem solved

Expose a typed, bounded coding task through one named command; inject model credentials at sandbox creation.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./qoder --yes
abx run <sandbox-id> qoder_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('qoder_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/qoder_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "1.1.72"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

`qoder` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| cwd | string | "" | Existing directory; relative paths resolve under WORKSPACE. |
| command_timeout | integer | 600 | Execution deadline, 1–1800 seconds. |

| Additional command | Parameters | Result |
|---|---|---|
| qoder_version | none | Installed CLI version. |
| qoder_setup_check | none | Read-only installed/version/PAT-presence diagnostic. |
| qoder_run | script: string = main.py | Local Python stdout; does not call Qoder. |

## Configuration

`WORKSPACE=/home/user/app`. `QODER_PERSONAL_ACCESS_TOKEN` is required for model execution; browser/OAuth login is never started. `accept_edits` auto-approves file edits; upstream rejects shell confirmations. Sessions are not persisted and automatic updates are disabled.

Secret declarations in template.yaml are empty; do not copy credentials into images or logs.

## Resources

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

```bash
python3 scripts/check_template.py qoder
python3 -m pytest -q qoder/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` controls the model acceptance command budget (default 600 seconds, range 1–1800). L0 does not call a model. `E2E_REQUIRE_LLM=1` forces real coding acceptance. L3 uses target setup diagnostics, seeds failing source/tests, verifies changed source/new artifacts/unchanged tests through target file APIs, then independently executes unittest and held-out calculations. A missing key is not acceptance.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py qoder` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/qoder.md).

## Issues

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## License

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### 2026-10-20 full step checkpoint: template1.1.1

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T155408Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 9 PASS/0 FAIL/1 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
