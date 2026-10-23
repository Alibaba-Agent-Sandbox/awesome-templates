# qm

## What it does

Run unchanged original QM0.1.0 exported Pi harness and original tool context on one owned Express computer, using an authored backend built on the real Agent Sandbox Node.js HTTP SDK. Coding uses an explicitly approved compatible model. Original full multiplayer core/web/Slack/Postgres durability/cron/subscription features are not started or qualified. Original default Docker backend is not used. This is a bounded original-library integration, not a shell program named qm or a replacement agent. [Original source](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255).

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13. SHA256-pinned original Node24.16.0 archive/executable, full original QM source0.1.0/immutable commit and original npm integrity lock. Original Node SDK0.1.0 source90b5187dca84fca78d75d3045896482540641c72 built with its original lock/build script; npm0.1.0 returned404 on2026-10-21, so no npm release is assumed. Server34e7e011c5569f77b7f605e65313be7498f6cf02. [Dockerfile](Dockerfile), [provenance](upstream.json), [QM lock](package-lock.json), [SDK lock](sdk-package-lock.json), [design](../docs/design/qm.md).

## Problem solved

Run genuine exported original QM functionality with actual SDK-backed tools without nested Docker or cloud credentials in model tools. Native package/source/import checks, SDK round trips and actual model file/task acceptance are separate gates. The Node SDK is an in-sandbox HTTP client; outer creation/kill belongs to the caller's Python Sandbox SDK. One caller project per backend; attach/provision does not create another cloud VM.

## Quick start (CLI)

Install the [verified CLI native entry](../docs/platform-steps.md), configure authorized Express access and replace every angle-bracket placeholder. Publish the exact source commit before immutable public COPY preparation. Assign the generated manifest a unique owned name as below; wait for official READY before creation. The same model-free task is used by CLI, Python SDK and HTTP. `abx run` is selected as `abx --native run` in CLI0.4.1.

```bash
python scripts/prepare_steps.py qm --output /tmp/qm-steps-<unique-run> \
  --asset-transport parallel --server-commit 34e7e011c5569f77b7f605e65313be7498f6cf02
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/qm-steps-<unique-run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "qm-<unique-run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/qm-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> qm_sdk_smoke
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```
Canonical owned validation uses `ABX='abx --native' python scripts/run_steps_e2e.py qm --sandbox-create sdk --http --asset-transport oss`; it owns/reconciles temporary resources and private OSS caches. Manual callers must clean their own known IDs. Steps acceptance does not prove Docker image deployment.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` following the [paired source instructions](../docs/python-client-installation.md); import `agent_sandbox`. Examples are syntax checked, not a provider pass. This example owns cleanup and assumes the default empty command-server token. If any server has a Bearer configured, use `sb.server_at(9000,token=...)` (or its actual port), call that client’s commands and close it.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        result = await sb.run("qm_sdk_smoke", timeout=200)
        assert result == "Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK"
    finally:
        await sb.kill()

asyncio.run(main())
```
For actual coding, configure QM_MODEL_API_KEY/QM_MODEL_BASE_URL/QM_MODEL before command-server startup and check qm_setup_check. Then `await sb.run("qm", prompt="Fix existing source and preserve its tests", cwd="project", command_timeout=300, timeout=430)`. Returns the structured object directly with buffered final reply/metadata; no streamed chunks or raw reasoning. Native completion plus independent files/tests are required for a coding claim.

[Prewarmed server configuration](../docs/runtime-environment.md): later create-time environment does not reconfigure an existing9000process. A separately started9010server must explicitly set QM_SANDBOX_BASE_URL=http://127.0.0.1:9010 and the matching SDK Bearer. Use sb.server_at(port,token=...) for named calls, close that client, stop/drain/cancel its owned server stream and finally kill the outer sandbox. Never place key/token values in argv.

## Quick start (HTTP POST)

ABX_SERVER_URL is `sb.network.get_url(9000)`; command-server Bearer, optional provider gateway access headers, SDK Bearer and model credentials are distinct.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/qm_sdk_smoke" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```
HTTP200 returns `{"result":"Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK"}`. Named commands accept direct JSON argument objects, without an args wrapper. Missing/unknown/type-invalid arguments400, auth401, unknown command404, semantic/native exceptions500 with `{error,type}`. Exec results preserve actual command code and timedOut separately; an authored command exiting124 is not automatically a timeout. A request disconnect does not cancel the native bounded operation. Backend close drains already issued SDK requests before closing transport; model-tool deadlines are capped to min(30seconds, the turn deadline), and an aborted run is not reported as successful.

## Command reference

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| qm_version | none | Actual checked `{qm_version:"0.1.0",node_version:"24.16.0",sdk_version:"0.1.0"}`; no model/network |
| qm_native_check | none | `{original_qm_harness:true,original_tool_context:true,actual_sdk_client:true}`; real original imports, no backend/model request |
| qm_setup_check | none | Read-only mode `original-qm-agent-sandbox-sdk-slice`, SDK base/token presence and optional model presence booleans; never secret values |
| qm_sdk_smoke | none | Exact string after original QM tool context/actual SDK file+execution+listing+removal round trip and owned fixture absence; no model; private transient files |
| qm | prompt: required nonempty string1..32768UTF8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final reply as stdout, actual source/qm/node/sdk identities, native_completed, original model_calls/native_tool_calls/native_tool_results, completed sdk_calls, stopped/pending_approvals and exit_code0; native tool file changes persist |

Requests serialize; overlap fails busy. Native process stdout/stderr256KiB each and anonymous request256KiB. Per SDK tool command: explicit Bash, minimal environment/private HOME,64KiB per returned stream, deadline1..120seconds and identity-pinned process-group/nonce/pidfd descendant cleanup. Backend exec allows up to50seconds startup/cleanup allowance; model wrapper up to90seconds. Give the client at least80seconds extra for backend exec and130seconds for qm. File library bytes max1MiB, public named text/read32KiB, directory names max1024and32KiBJSON. Larger values fail; no silent truncation. Resolved file paths stay inside the selected project; SDK helpers independently reject traversal/symlink escapes and root removal. Shell tools have the outer user's OS authority; cwd is not a separate OS security boundary.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/app | Existing caller project root, captured at startup |
| QM_SANDBOX_BASE_URL | http://127.0.0.1:9000 | Actual SDK data-plane server on the same owned computer; literal local HTTP only, no userinfo/query/fragment/path |
| QM_SANDBOX_TOKEN | empty; optional | SDK server's independent Bearer token; falls back to ABX_SERVER_TOKEN for the default same server |
| ABX_SERVER_TOKEN | empty; optional | Command server's independent Bearer credential |
| QM_MODEL_API_KEY | empty; required for qm | Approved compatible model key; anonymous stdin/private native memory |
| QM_MODEL_BASE_URL | empty; required for qm | Explicit HTTPS compatible Chat Completions API base; local HTTP for authored fixtures only; no userinfo/query/fragment, max2048characters |
| QM_MODEL | empty; required for qm | Actual model identifier, max200allowed characters; no default vendor fallback |

Captured when commands.py loads; read-only setup flags do not prove connectivity. SDK token max8192/noCRLF/NUL; model key max8192/no control characters. Node worker receives configuration by anonymous stdin and no model/cloud/GitHub credentials in its environment. Model/tool child Bash gets a separate minimal environment and private HOME; same-user OS access remains. Private native HOME/cache/settings/model-catalog/temporary workspace mirrors are removed after every call. Literal and JSON-escaped configured keys/bases/tokens are redacted from returned strings. Original QM native Pi builtins are disabled in favor of its original QM tools; no extensions/skills/context files or session children are loaded. Only execute/files read/write approval identities are enabled; no delegation, Slack/email delivery or control service. Caller project/artifacts persist until caller removes them or kills the outer sandbox.

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000, enforced8GiB image rootfs budget. No Docker/KVM/GPU/root capabilities. Actual native dependencies and the bounded Express profile pass below; peak memory was not measured and declared memory is not a workload estimate. Package/source download and SDK endpoint access are needed; coding additionally requires approved model tool calling/egress. No other provider or full multiplayer durability is claimed.

## Verified

No project-recognized receipt certifies the current workflow manifest. Historical acceptance records retain only their original input and call-path scope; see [workflow verification](../docs/workflows.md).

## Secondary development

```bash
python -m pytest -q qm-sandbox/test_runtime.py qm-sandbox/test_commands.py
python -m pytest -q qm/test_terminal.py
python scripts/check_template.py qm --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py qm --sandbox-create sdk --http --asset-transport oss
```

For original SDK HTTP fixtures, run `python qm-sandbox/prepare_sdk_tests.py /tmp/qm-sdk-tests-<unique-run>`, then `ABX_QM_TEST_SDK_ENTRY=/tmp/qm-sdk-tests-<unique-run>/dist/index.js node --test qm-sandbox/test_adapter.mjs`. Node>=20 suffices for SDK-only unit fixtures; actual original QM requires the pinned Node24.16.0 profile. Without that explicit original SDK build, these HTTP fixture tests are skipped, never a native/backend pass.

Original sources/locks/notices remain authoritative. Native workers execute only on a newly owned disposable target for actual acceptance; source-only checks explicitly skip missing native runtime and never opt in to a model. The coding controller requires positive original model/tool and completed SDK counts, preserved original tests, changed source, new report/exact nonce, complete original3plus4held-out post-return cases and fresh ACK. A marker/configuration/version alone is insufficient. Backend acceptance separately checks original tool context/real SDK file/execution and independent target bytes/absence.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), project/documentation standards and source-bound evidence rules. Keep both README languages, design, catalog, API, immutable pins and indexed engineering records consistent. Preserve every failure and independently verified resource recovery.

## Issues

Track [Issue44](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/44). Template/native adapter issues belong here; Python server/client to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), Node HTTP client to [nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues), CLI to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized versions/scope, never keys/private endpoints/raw prompts or reasoning.

## License

Authored wrapper/backend Apache-2.0; original QM MIT, original Node and SDK retain their licenses/notices. [Original distribution notice](UPSTREAM-NOTICE.md), [QM license](UPSTREAM-QM-LICENSE). Complete original notices stay installed; no third-party relicensing.
