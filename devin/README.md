# devin

[中文](README.zh-CN.md).

## What it does

Run the original Cognition Devin CLI3000.11.92 through typed bounded named commands in an owned disposable sandbox. The native CLI owns inference and tools; no replacement planner or compatible-model fallback is supplied. Automatic tools require `allow_unsafe_tools=True`.

## Stack

Alibaba generation2 Linuxx86_64 base, Python3.13 server, original fixed [official archive](https://static.devin.ai/cli/3000.11.92/devin-3000.11.92-x86_64-unknown-linux.tar.gz), original234files/200878983bytes, compressed67245544bytes. SHA256 `2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0` was published by the official platform manifest observed2026-10-21; see [inventory](upstream.json). ServerSDK source is pinned in [server-sdk.commit](server-sdk.commit). Build verifies original archive/per-file hashes without executing it; runtime verifies original root-owned files. Original binaries/docs/manpages retain their own terms.

## Problem solved

Use the real headless program with deterministic installation, explicit permission, private per-call state, bounded output/deadline and owned process cleanup. The historical interactive-login obstacle is handled using the vendor-documented credentials file copied between the user's own machines. That integration is available but authenticated execution is unverified without an account.

## Quick start (CLI)

The `abx run` surface explicitly uses `abx --native run` below. Publish the exact source first and replace `<run>`/`<published-commit>` with a unique run and its public40-character commit.

Use the actual native0.4.1 command surface and your configured Express account. Replace owned IDs with results from your own deploy/create; no IDs are stored in this repository.

```bash
python scripts/prepare_steps.py devin --output /tmp/devin-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/devin-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "devin-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/devin-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> devin_version
abx --native run <owned-sandbox-id> devin_native_check
abx --native run <owned-sandbox-id> devin_setup_check
# A process configured with an original credentials file before startup:
abx --native run <owned-sandbox-id> devin --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Create the project first. The account line is syntax checked, not an authenticated pass. Create-time environment does not reconfigure prewarmed commands; use explicit process startup below. CLI `--server-port` selects another command-server port; authentication must match that process. Follow [runtime environment](../docs/runtime-environment.md).

The canonical no-account test invokes the original `--print` through HTTP and SDK and requires explicit native authentication refusal, unchanged fixture bytes and cleanup:

```bash
ABX='abx --native' python scripts/run_steps_e2e.py devin \
  --sandbox-create sdk --http --asset-transport oss
```

OSS uses the [pinned optional prerequisites](../scripts/requirements-steps-cache.txt) and owned private temporary original-archive cache, with hashes/private ACL/independent deletion. Source steps need no local Docker; Docker-image acceptance is separate. No account/model/operator key is injected by this fixture.

## Quick start (Python SDK)

Install the [paired `agent-sandbox-client`](../docs/python-client-installation.md). Native diagnostic/no-account named calls need no account. For real coding, first authenticate with the original CLI on your own authorized machine (`devin auth login`). The vendor permits copying that original sensitive `credentials.toml` between your own machines; see [official authentication](https://docs.devin.ai/cli/enterprise/devin-auth). Set DEVIN_CREDENTIALS_FILE locally to that file's path. This is an authored wrapper setting, not a vendor API-key environment variable. Keep it out of Git and model prompts.

The following real-account example is syntax checked, NOT_RUN without an account. Upload the original file bytes to a private path outside WORKSPACE, set mode0600, then start an independent9010server/Bearer. `<owned-template-id>` belongs to this run.

```python
import asyncio, os, secrets, uuid
from pathlib import Path
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    server = None
    try:
        print(await sb.run("devin_version"))
        folder = "/home/user/devin-private-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -m 700 " + folder)
        credential = folder + "/credentials.toml"
        await sb.files.write(credential, Path(os.environ["DEVIN_CREDENTIALS_FILE"]).read_bytes())
        await sb.commands.run("chmod 600 " + credential)
        project = "/home/user/app/devin-example-" + uuid.uuid4().hex
        await sb.commands.run("mkdir -m 700 " + project)
        await sb.files.write(project + "/calc.py", "def add(a,b): return a-b\n")
        token = secrets.token_urlsafe(32)
        server = await sb.start_server(port=9010, commands="/home/user/app/commands.py",
            token=token, env={"DEVIN_CREDENTIALS_FILE": credential, "ABX_PTY_PORT": "9011"})
        print(await server.commands.run("devin_setup_check"))
        result = await server.commands.run("devin", prompt="Repair existing calc.py and write report.txt",
            cwd=project, command_timeout=300, allow_unsafe_tools=True, timeout=420)
        print(result["stdout"])
    finally:
        try:
            if server is not None:
                await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                await sb.close()

asyncio.run(main())
```

Original credentials can persist until revoked; never treat a short sandbox TTL as revocation of the original token. Each invocation copies bytes unchanged to a new private `$XDG_DATA_HOME/devin/credentials.toml` and deletes that copy afterward. The input file remains caller-owned; sandbox deletion removes this example's upload. Independently read back absence after deleting owned resources. No `stop_server` method is assumed.

## Quick start (HTTP POST)

Use the forwarded URL of the configured command server and its independent Bearer; no vendor token or credential file contents belong in JSON arguments.

```bash
curl --fail-with-body -X POST "$DEVIN_COMMAND_SERVER_URL/commands/devin" \
  -H "Authorization: Bearer $COMMAND_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Repair existing calc.py and write report.txt","cwd":"project","command_timeout":300,"allow_unsafe_tools":true}'
```

Success HTTP200 contains `{"result":{"stdout":"...","stderr":"","exit_code":0,...}}`. Missing/unknown/type-invalid arguments400; command-server authentication401; unknown command404; semantic/native execution errors500. Native no-account refusal is an expected500 program error-path check, not model success. Error output exposes only bounded exit/category. `/health`, `/commands`, files and shell share the same server authentication boundary. HTTP disconnect does not cancel the remote operation; its own deadline still applies.

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
| ABX_SERVER_TOKEN | empty/optional | Independent command-server Bearer, not vendor account auth |

A missing original account file reaches original print and preserves its explicit login refusal; no interactive login, made-up DEVIN_API_KEY, root model key or fallback planner is used. The subprocess receives minimal private state environment without operator/model/cloud credentials or the source credential path. Known credential TOML string values, server Bearer/private HOME/source path are redacted in returned stdout. Native errors omit raw output. One operation per server process; overlap returns busy.

Each stdout/stderr stream is bounded256KiB; command1..600seconds plus up to90seconds owned descendant cleanup. Set client timeout at least command_timeout+120seconds. Same OS user/tool permissions are not a multi-tenant filesystem security boundary. Use owned disposable sandboxes with explicitly trusted task content; the native program can execute tools under that account.

## Resources

Linuxx86_64 only, nonroot user,2vCPU/4096MB/port9000; build enforces rootfs<=8GiB. Original package200.9MB, compressed67.3MB. No KVM/Docker/GPU/desktop requirement is claimed. Account execution needs authorized vendor egress/account/CLI role. PeakRSS/authenticated throughput, other architectures/providers, interactive/resume/cloud/ACP/MCP/plugins/delegation remain unverified.

## Verified

| Provider | Runtime verification | Scope |
| --- | --- | --- |
| alicloud-express | [Current1.0.1PASS receipt](evidence/express-2026-10-21T124114Z.json) · [steps/fullHTTP](evidence/verification-steps-2026-10-21T124114Z.json) | Original native version/help, SDKcreate, actual HTTP+SDK no-account refusal, fixture preservation and independent owned sandbox/template/private-cache absence |

The diagnostic-origin correction was requalified at published source8fa9bb821316b56c8f708945deb06b41321edccb:174.416seconds,16HTTPchecksPASS0FAIL0SKIP. Only the original expected no-account error path is passed; genuine vendor account/model/coding remainsNOT_RUN. Template1.0.0 receipts remain historical. [Follow-up verification](../.agents/evidence/verify/2026-10-21-devin-diagnostic-origin.md).

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
