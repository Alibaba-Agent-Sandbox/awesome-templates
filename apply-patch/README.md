# apply-patch

## What it does

Runs the actual official Codex *** Begin Patch dialect: add, update, move and delete. Patch bytes enter native stdin through a private temporary file, without a shell or patch text in argv.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49, generation2, non-root user. `npm ci --ignore-scripts` installs official @openai/codex0.162.1/native architecture packages using [lockfile integrity](package-lock.json). The validated native binary is dispatched by apply_patch argv0. The corresponding official release tag points to [092d3acd](https://github.com/openai/codex/tree/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d). This uses official prebuilt packages; it does not claim a local rebuild from that source commit.

## Problem solved

Supplies the real Codex file tool without a model account, Rust compiler, Docker or KVM. Linux x86_64/aarch64 only.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./apply-patch --yes
abx run <sandbox-id> apply_patch_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('apply_patch_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/apply_patch_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "codex-cli 0.162.1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| apply_patch | patch_text: str required, nonempty UTF-8 up to256KiB; cwd: str optional empty=WORKSPACE, existing subdirectory | {stdout: str, stderr: str, exit_code: int} from actual native parser |
| apply_patch_version | none | actual native `codex-cli 0.162.1` |
| apply_patch_smoke | none | APPLY_PATCH_OK only after real add/update/move/delete/literal bytes and owned cleanup |

Upstream failures retain nonzero exit_code; HTTP200 means the invocation completed, not that patching succeeded. Missing/undeclared arguments return400 and unknown command404. The SDK coerces scalar JSON values to declared strings; malformed patches still fail in the native parser. File and move paths must be relative to cwd; absolute paths, .., backslashes and existing symlinks are rejected before executing any part. An upstream failure may leave partial in-workspace edits; patching is not transactional.

## Configuration

No model key. WORKSPACE defaults to /home/user/app. Export ABX_SERVER_TOKEN before application launch; see [runtime environment](../docs/runtime-environment.md). Native patch subprocesses receive only PATH and LANG, without model/cloud credentials.

## Resources

2vCPU,2048MB,port9000. Each patch has a30-second deadline and256KiB per-output-stream limit. Owned process groups are stopped before reaping the original leader. Temporary patch files close automatically; caller modifications persist. Path preflight is not an OS isolation boundary against concurrent same-user rename/symlink races.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

Prepare [platform steps](../docs/platform-steps.md): `python scripts/prepare_steps.py apply-patch --output /tmp/patch-steps`; real acceptance: `python scripts/run_steps_e2e.py apply-patch`. For local runs use `npm ci --prefix apply-patch --ignore-scripts`, run install_alias.py into a separate bin directory, and put it on PATH before tests. Update lockfile, native version, release source and notices together; retain historical evidence.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [spec](../docs/template-spec.md) and [design](../docs/design/apply-patch.md).

## Issues

[Template Issue60](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/60); CLI defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template and Codex: Apache-2.0. Retain pinned-source [upstream-LICENSE](upstream-LICENSE) and official native npm metadata/notices.

### 2026-10-20 full step checkpoint: template1.0.0

[Real current-version steps](evidence/express-2026-10-20.json) and [complete external HTTP controller](evidence/verification-steps-2026-10-20T154625Z.json): official READY, actual Python SDK creation, all CLI/SDK smoke and 5 PASS/0 FAIL/0 SKIP; independent owned sandbox/template cleanup passed. Model acceptance remains NOT_RUN in this receipt; it does not relabel earlier image/model scope. Reproduction and exact server/controller provenance: [step guide](../docs/platform-steps.md).
