# Cursor Agent

[中文](README.zh-CN.md).

## What it does

Run the original Cursor Agent CLI in an owned disposable sandbox through typed named commands. Cursor owns inference and tool execution. A genuine CURSOR_API_KEY is required for agent tasks; no compatible-model or operator-key fallback exists. Automatic native tools require explicit `allow_unsafe_tools=True`.

## Stack

Original official CLI2026.10.19-6bbf2c4 for Linux x86_64, including its original bundled Node/launcher/native modules. The unchanged183,733,394-byte archive has controller-measured SHA256 `cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f`; this is not an upstream-published checksum. The460regular-file inventory totals585,886,062bytes. Python3.13 and the Alibaba generation2 base; server source34e7e011c5569f77b7f605e65313be7498f6cf02. See [original metadata](upstream.json), [notice](UPSTREAM-NOTICE.md) and [design](../docs/design/cursor-agent.md).

## Problem solved

Provide a reproducible headless Cursor installation, a scalar SDK/HTTP interface and bounded execution with owned process/private-state cleanup. This is a local CLI profile; it does not provision Cursor Cloud Agents or an enterprise machine scheduler. Authenticated coding/model behavior remains unverified until a genuine vendor-key run exists.

## Quick start (CLI)

The `abx run` surface uses `abx --native run` here.

Use the [verified CLI/native entry](../docs/using-templates.md#client-entry-compatibility) and authorized Express settings. Replace `<run>`, `<published-commit>`, `<owned-template-id>` and `<owned-sandbox-id>` with your unique run, exact public40-character source commit and resources created by that run. Publish the exact source before immutable COPY preparation. Rename the generated manifest `name` to `cursor-agent-<run>` before deployment.

```bash
python scripts/prepare_steps.py cursor-agent --output /tmp/cursor-agent-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/cursor-agent-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "cursor-agent-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/cursor-agent-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> agent_version
abx --native run <owned-sandbox-id> agent_native_check
abx --native run <owned-sandbox-id> agent_setup_check
# On a command-server process configured with its own vendor key before startup:
abx --native run <owned-sandbox-id> agent --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Create the project first. The configured-agent line is syntax-checked, not a successful account test. A create-time environment does not configure a prewarmed process; use the explicit process startup below and [runtime guide](../docs/runtime-environment.md). The native CLI supports `--server-port`; SDK/HTTP examples use a separately authenticated9010process. Match authentication to that process.

The canonical keyless test prepares an explicitly invalid synthetic vendor-key fixture and calls the actual original program through HTTP/SDK; it never injects the operator's vendor/model key:

```bash
ABX='abx --native' python scripts/run_steps_e2e.py cursor-agent \
  --sandbox-create sdk --http --asset-transport oss
```

OSS transport requires the [pinned optional cache prerequisites](../scripts/requirements-steps-cache.txt), creates only owned private temporary objects, verifies original hashes/ACL and independently deletes them. Native steps need no local Docker daemon. Docker image acceptance is a separate check.

## Quick start (Python SDK)

Install `agent-sandbox-client` through the [paired source instructions](../docs/python-client-installation.md). Set CURSOR_API_KEY in the operator's secure environment. `<owned-template-id>` is the template you created; this example's unique project and sandbox belong to the example. No vendor key value is placed in argv or JSON command arguments.

```python
import asyncio, os, secrets, uuid
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    server = None
    try:
        print(await sb.run("agent_version"))
        project = "/home/user/app/cursor-example-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -p " + project)
        await sb.files.write(project + "/calc.py", "def add(a,b): return a-b\n")
        token = secrets.token_urlsafe(32)
        server = await sb.start_server(port=9010, commands="/home/user/app/commands.py",
            token=token, env={"CURSOR_API_KEY": os.environ["CURSOR_API_KEY"], "ABX_PTY_PORT": "9011"})
        print(await server.commands.run("agent_setup_check"))
        result = await server.commands.run("agent", prompt="Repair existing calc.py and write report.txt",
            cwd=project, command_timeout=300, allow_unsafe_tools=True, timeout=420)
        print(result["stdout"])
    finally:
        if server is not None:
            await server.aclose()
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

Vendor-authenticated lines are not claimed executed. Set a sandbox lifetime covering the command and cleanup; a command timeout is separate from sandbox TTL. Closing a borrowed server client closes its client transport; killing the owned sandbox ends its remote processes. Independently confirm resource absence when automating deployment.

## Quick start (HTTP POST)

Use the forwarded URL of the configured server process and its independent command-server Bearer from the SDK example. The direct JSON arguments do not include the vendor key.

```bash
curl --fail-with-body -X POST "$CURSOR_COMMAND_SERVER_URL/commands/agent" \
  -H "Authorization: Bearer $COMMAND_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Repair existing calc.py and write report.txt","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
```

HTTP200 has `{"result":{"stdout":"...","stderr":"","exit_code":0,...}}`. Missing/unknown/wrong-type arguments400; command authentication401; unknown command404; semantic/native errors500 with bounded sanitized category/exit code. An expected invalid-key500 is a program error-path test, not model success. `/health`, `/commands`, files and shell use the same process/auth boundary. HTTP client disconnect does not cancel a provider job; the bounded owned operation still cleans up.

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
| ABX_SERVER_TOKEN | empty/optional | Independent command-server Bearer, not a Cursor credential |

Original programs receive a minimal environment with only their explicit vendor key and private HOME/config/data/cache/TMP paths. Updates and project configuration loading are disabled by pinned original flags; OS keychain/persistent native sessions are not used. Per-call native state is removed after success/error/timeout. The server process and native tools share an OS user; these paths are not another tenant boundary. Use a fresh caller-owned disposable sandbox for automatic tools.

At most one agent operation per server process; concurrent calls fail busy. Stdout/stderr are each bounded256KiB, command deadline1..600seconds plus up to90seconds cleanup; client timeout should cover command_timeout+120seconds. Known key/command-token/private-home values are redacted. No private transcript or provider ID belongs in public evidence.

## Resources

Linux x86_64 only;2vCPU/4096MB/port9000, non-root user, WORKSPACE=/home/user/app,8GiB rootfs ceiling checked during build. Original bundle585.9MB; archive183.7MB. No nested Docker, KVM, GPU or desktop requirement is claimed. Vendor egress/account are required for model tasks; peak RSS and authenticated throughput are unmeasured. Other architectures/providers, interactive/resume/MCP/plugins/delegation/cloud-agent features are not certified.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.0; regular image, actual CLI/SDK, complete HTTP 16 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-22T105311Z.json) |
| opensandbox | 1.0.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 16 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T111132Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

| Provider | Runtime verification | Scope |
| --- | --- | --- |
| alicloud-express | [PASS receipt](evidence/express-2026-10-21.json) · [steps/full HTTP](evidence/verification-steps-2026-10-21T110917Z.json) | Original native version/help, actual SDK create, HTTP and SDK invalid-key refusal, independently confirmed owned sandbox/template/private-cache cleanup |

The current1.0.0 published-source native step run completed in170.608seconds, with16HTTP checksPASS,0FAIL,0SKIP and7554wire bytes. A fixed explicitly invalid synthetic credential exercises the original program's authentication error; it is never counted as an authenticated model session. Genuine Cursor account/model/coding acceptance is NOT_RUN because no vendor credential is available. The catalog remains experimental. Local authored tests, hosted Docker-image checks and provider step acceptance are separate. [Research and executed checks](../.agents/evidence/verify/2026-10-21-cursor-native-research.md).

</details>

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
