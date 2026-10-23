# muse

## What it does

Run the unchanged official Meta Muse Code1.4.11-R6667.1 native headless agent, original miniswe tools and native runtime records on one owned Express computer. Coding uses an explicitly configured compatible Responses model. The authored local relay supplies the selected model catalogue and keeps the upstream key out of native/tool environments; Responses requests and streams pass unchanged. This is the original Muse binary, not a same-named substitute. [Original documentation](https://dev.meta.ai/docs/muse-code).

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13, root-owned original native ELF384809176bytes with its published SHA256, Python stdlib relay/process controls, pinned server34e7e011c5569f77b7f605e65313be7498f6cf02. No new Python/Node dependencies. [Dockerfile](Dockerfile), [provenance](upstream.json), [upstream notice](UPSTREAM-NOTICE.md), [design](../docs/design/muse.md). The template source license does not relicense the original upstream artifact. A task-owned local gzip cache can be rehashed and streamed to private OSS without a second384.8MB operator disk copy; the target still checks unchanged original bytes.

## Problem solved

Provide genuine original Muse file/tool execution through named SDK/HTTP commands with private per-call configuration and verified ownership. A generic compatible gateway lacks the original CLI's required `/muse-code/models`: the narrow local relay supplies that metadata, then forwards original `/responses` bytes to exactly the configured endpoint with no tool/model translation. No vendor/account/subscription fallback.

## Quick start (CLI)

The `abx run` native surface is selected as `abx --native run`. Use verified CLI0.4.1's explicit native entry and existing authorized Express settings. Publish the exact source before immutable COPY preparation; replace placeholders and give the generated manifest a unique owned name before deployment. Wait for official READY before creation. The same keyless operation is used by CLI, Python SDK and HTTP.

```bash
python scripts/prepare_steps.py muse --output /tmp/muse-steps-<unique-run> \
  --asset-transport parallel --server-commit 34e7e011c5569f77b7f605e65313be7498f6cf02
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/muse-steps-<unique-run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "muse-<unique-run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/muse-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> muse_version
abx --native run <owned-sandbox-id> muse_native_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Canonical ownership/cleanup: `ABX='abx --native' python scripts/run_steps_e2e.py muse --sandbox-create sdk --http --asset-transport oss`. Manual callers own all created IDs. Native steps require no local Docker daemon; steps acceptance does not certify image cloud deployment.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` (import `agent_sandbox`) using the [paired source instructions](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    try:
        print(await sb.run("muse_version", timeout=60))
        print(await sb.run("muse_native_check", timeout=60))
    finally:
        await sb.kill()

asyncio.run(main())
```

For coding, configure all three MUSE_MODEL_* variables **before the named-command server starts**, inspect `muse_setup_check`, then call `await server.commands.run("muse",prompt="Repair existing calc.py and preserve its tests",cwd="project",command_timeout=300,timeout=380)`. The project must already exist. Use `sb.server_at(port,token=...)` for an independently authenticated server and close that borrowed client afterwards. A prewarmed9000process is not reconfigured by later create-time env: follow [explicit process setup](../docs/runtime-environment.md); a separately configured9010server needs its own matching token. Results are buffered/direct, not transport-streamed native events.

## Quick start (HTTP POST)

ABX_SERVER_URL is the configured server's `sb.network.get_url(port)`; ABX_SERVER_TOKEN is separate from model/platform credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/muse_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 returns `{"result":"Muse Code 1.4.11 (1.4.11-R6667.1)"}`. `POST /commands/muse` takes direct `{prompt,cwd,command_timeout}` JSON. Missing/unknown/type arguments400, authentication401, unknown command404; semantic/native errors500 with sanitized `{error,type}`. HTTP disconnect does not cancel the native process or upstream provider job; bounded owned cleanup still runs.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| muse_version | none | `Muse Code 1.4.11 (1.4.11-R6667.1)` after exact original ELF verification; no model |
| muse_native_check | none | `{original_native:true,headless_json:true,anonymous_api_key_stdin:true,no_session_log:true}` from actual headless help; no model |
| muse_setup_check | none | mode `original-native-muse-explicit-responses`, native_present/model_key_set/model_base_set/model_set flags; model_account_verified:false/provider_default_fallback:false/catalog_relay:true; no values/network |
| muse | prompt: required nonempty string1..32768UTF8bytes/noNUL; cwd: string default empty, max4096bytes, existing resolved directory inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final stdout, native_completed, actual model_calls/native_tool_results, exit_code0, original binary/version/model/protocol and completed relay_calls. Original tools may edit caller project files; no raw transcript |

Fixed original argv: `exec --json --api-key-stdin --provider meta --model <configured> --preset miniswe --reasoning-effort minimal --max-model-steps16 --no-session-log --disable-reminders --no-foreign-personal-context --disable-web-tools --yolo --workspace <contained-project>`. Original settings schema_version1, endpoint_transport base_url/auth bearer and agents.execution_capacity1 are private per call. Original miniswe has no available subagent_spawn; no delegated model/tool tree is selected. Caller project instructions may load after the explicit trust flag.

Native completion requires exact correlated original model/usage/terminal records, positive completed model calls, no failed/cancelled/child calls and nonempty final text. Coding acceptance additionally requires positive original tool results and independent artifacts/tests. Model requests32maximum,2MiB each,4MiB per response,16native model steps; native stdout/stderr256KiB each. Issued relay requests drain before completion. Owned close/process cleanup may add up to50seconds; SDK timeout should be at least command_timeout+80. Concurrent model calls fail busy.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| MUSE_MODEL_API_KEY | empty; required for coding | Key for the explicitly selected compatible endpoint; retained only in parent relay |
| MUSE_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS Responses base, max2048characters, no userinfo/query/fragment; literal-loopback HTTP only for authored fixtures |
| MUSE_MODEL | empty; required for coding | Actual upstream model identifier,1..200allowed identifier characters |
| WORKSPACE | `/home/user/app` | Existing caller project root |
| ABX_SERVER_TOKEN | empty; optional | Independent command-server Bearer credential |

Captured at commands.py import; presence flags do not prove authentication. Key max8192/no control characters. Native receives only a fresh per-call local relay token by anonymous stdin. The parent relay uses the upstream key only for the exact approved Responses endpoint, rejects redirects and wrong route/token/model, and retains no transcript. Native/tools use a minimal environment and private HOME/cache/config; caller project artifacts persist. Same-user OS access remains; cwd containment and environment filtering are not another tenant boundary. `--yolo` selects the disposable outer sandbox as the execution boundary.

## Resources

Declared2vCPU/2048MB/Linuxx64, port9000,8GiB image rootfs budget, no KVM/Docker/GPU or extra privileges. Original artifact downloads384.8MB; model requests need approved egress. The bounded actual image/step/fullHTTP/model slice passes below; peak memory was not measured. Other providers, interactive sessions, retained resume, voice/local weights, MCP/plugin services and Meta-hosted subscriptions are outside this profile.

## Verified

No project-recognized receipt certifies the current workflow manifest. Historical acceptance records retain only their original input and call-path scope; see [workflow verification](../docs/workflows.md).

## Secondary development

```bash
python -m pytest -q muse/test_commands.py muse/test_relay.py muse/test_terminal.py
python scripts/check_template.py muse --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py muse --sandbox-create sdk --http --asset-transport oss
```

Use fixed non-executable replies for local relay/parser fixtures. Native/generated-code acceptance runs only on a fresh explicitly owned cloud target. Preserve original binary and notices, exact bounds, redirect refusal, anonymous input and process/relay cleanup. Formal coding checks require changed source, original test bytes, new report/exact nonce, original3plus4held-outs/fresh post-return ACK and independent owned absence.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include owner note/evidence and both README languages; merge only after actual required checks/review pass.

## Issues

[Template Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71) owns this delivery. [Template bugs](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); original Muse behavior belongs to its upstream support. Never attach credentials or raw private transcripts.

## License

Authored template code/documentation: [Apache-2.0](../LICENSE). Original Meta artifact terms/notices remain separate; see [attribution](UPSTREAM-NOTICE.md). No upstream open-source license, vendor endorsement or hosted-model account is asserted.
