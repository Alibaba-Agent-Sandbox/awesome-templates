# prime-agent

## What it does

Runs the unchanged stable Prime Agent0.10.0 native Rust CLI with its original CPython REPL tool named `ipython`. Uses an explicitly approved compatible model and supported fixed kernel interpreter. This bounded headless coding slice does not qualify daemon sessions, recursive agents, subscription models or research benchmarks. [official release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0); [pinned native source](https://github.com/PrimeIntellect-ai/prime-agent/tree/763094e1b6a7c17450ee8399b06cda1853847ca5).

## Stack

Alibaba generation2 basev0.0.49/Python3.13/Linuxx64; original release archive and executable verified against official manifest SHA256s. Full original sidecars/runtime source0.1.0/protocol3 and licenses retained. Isolated49-package Python hash lock; native supported fixed interpreter skips floating uv/bootstrap. Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a, non-root user, port9000. [Dockerfile](Dockerfile), [provenance](upstream.json), [lock](requirements.lock), [design](../docs/design/prime-agent.md).

## Problem solved

Expose actual native coding through Agent Sandbox without interactive account login, shared developer configuration or operator-side generated-code execution. Native provider resolution, CPython protocol, terminal events and owned cleanup are checked separately; installation/version output alone does not establish coding success.

## Quick start (CLI)

Install the [verified native CLI entry](../docs/platform-steps.md), configure authorized Express access and replace angle-bracket placeholders with unique owned values. Publish the exact source commit before steps preparation uses immutable public COPY inputs. Wait for official READY before creation. CLI0.4.1 uses `abx --native run`; the named-command interface is `abx run`.

```bash
python scripts/prepare_steps.py prime-agent --output /tmp/prime-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/prime-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> prime_agent_version
abx --native run <owned-sandbox-id> prime_agent_kernel_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```
Expected version is `{"native_version":"0.10.0"}`. After configuring the command server, a real task is `abx --native run <owned-sandbox-id> prime_agent --json-args '{"prompt":"Inspect the existing project and fix failing tests","cwd":"project","command_timeout":300}'`. Existing project path must be contained in WORKSPACE. Native completion and independent file/tests are required before accepting coding success.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` from the [paired source instructions](../docs/python-client-installation.md); import `agent_sandbox`. This model-free example owns and removes its sandbox. Examples are syntax checked; real-cloud qualification remains in Verified.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("prime_agent_version", timeout=60))
        print(await sb.run("prime_agent_kernel_check", timeout=90))
    finally:
        await sb.kill()

asyncio.run(main())
```
Configure PRIME_MODEL_API_KEY/PRIME_MODEL_BASE_URL/PRIME_MODEL before command-server startup. [Prewarmed process configuration](../docs/runtime-environment.md) explains that later create-time environment does not reconfigure an existing9000 process. Verify presence with `prime_agent_setup_check`, then `await sb.run("prime_agent", prompt="Fix existing source and preserve its tests", cwd="project", command_timeout=300, timeout=330)`. Result is returned directly; it is buffered, without streaming events.

## Quick start (HTTP POST)

ABX_SERVER_URL is `sb.network.get_url(9000)`. The server token is separate from model and provider credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/prime_agent_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```
HTTP200 returns `{"result":{"native_version":"0.10.0"}}`. `POST /commands/prime_agent` accepts direct `{prompt,cwd,command_timeout}` JSON. Type/unknown/missing arguments400, authentication401, unknown command404, semantic guards/execution exceptions500 with `{error,type}`. A completed original process returns its actual exit_code even when nonzero. Disconnect does not cancel the bounded native operation; final cleanup still runs.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| prime_agent_version | none | Actual checked binary/version: `{native_version:"0.10.0"}`; no model |
| prime_agent_kernel_check | none | Original CPython runtime protocol3,12 required imports: `{protocol_version:3,required_imports_checked:12}`; no model or bootstrap |
| prime_agent_setup_check | none | mode `original-native-prime-cpython-repl`; subscription_required:false; api_key_set/base_url_set/model_set booleans; read-only |
| prime_agent | prompt: required nonempty string1..32768UTF-8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"0.10.0",native_completed:bool}`; real original native tools may modify files |

Fixed flags: --offline --mode json --provider abx-approved --model <configured-model> --thinking off --no-session --no-skills --no-prompt-templates --no-themes --no-context-files --cwd <private-git-root> --print. Prompt enters anonymous stdin with the absolute selected project path. The actual native cwd is a private Git root so caller project settings cannot replace the explicit provider. Native `ipython` executes original CPython code. Tool processes have the disposable sandbox user's OS permissions; the cwd guard is not an additional OS sandbox.

Transparent event filtering preserves original settled NDJSON records unchanged and discards incremental update duplicates: raw stdout16MiB, line1MiB, retained stdout256KiB, stderr256KiB. Native exit status/signals are retained. native_completed requires exit0, native turn_end/agent_end and final assistant stopReason=stop. Coding acceptance additionally requires a successful original ipython tool result and independent original/held-out tests. Calls serialize; overlap fails busy. Deadline/overflow/failure cleans the owned process group, nonce-identified descendants and private HOME/config/cache/kernel state.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| PRIME_MODEL_API_KEY | empty; required for coding | Approved compatible-model key |
| PRIME_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS base; literal local HTTP for authored fixtures only; no userinfo/query/fragment; max2048characters |
| PRIME_MODEL | empty; required for coding | Actual model identifier; max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing caller project root |
| ABX_SERVER_TOKEN | optional; empty | Independent command-server Bearer token |

Captured when commands.py loads. Private0700HOME/0600models.json uses apiKey="ABX_PRIME_MODEL_KEY", storing an environment reference instead of key bytes. No operator cloud/GitHub/vendor credentials are inherited. The fixed kernel launcher removes ABX_PRIME_MODEL_KEY before original CPython starts; same-user OS access means this is environment minimization, not credential isolation. Literal/JSON-escaped key and base values are redacted from returned output. Telemetry/traces/refinement/compaction/factory and discovery are disabled; rlmMaxDepth0 is set. Original print mode supplies no child host and therefore uses NoRlmChildren: no delegated agent is launched. No daemon mode is started. Custom model pricing is unspecified; zero defaults are not a free-service claim.

## Resources

Linuxx64, declared2vCPU/2048MB, port9000,8GiB enforced rootfs budget within Express storage. No nested Docker/KVM/GPU needed. Model tool calling, explicit API access and egress are required for coding. Runtime peak-memory/workload capacity has not been measured.

## Verified

No provider has a passing run recorded for this template.

Native version/help and authored local checks are partial evidence only. Current image/Express/native-kernel/real-model and independent cleanup gates remain pending. [Dated research](../.agents/evidence/verify/2026-10-20-prime-agent-native-research.md).

## Secondary development

```bash
python -m pytest -q prime-agent/test_commands.py prime-agent/test_terminal.py
python scripts/check_template.py prime-agent --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py prime-agent --sandbox-create sdk --http
```

Real-model controller opts in only on an explicitly owned remote target. It repairs seeded existing source, preserves original test bytes, downloads a new report/exact fresh nonce, independently runs original3 plus4held-out cases and issues a fresh post-return ACK. Fixed synthetic protocol fixtures and source-only native skips do not establish a model/cloud pass.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), project/documentation standards and immutable evidence rules. Preserve original licenses and full release sidecars; update both README languages, design, manifest, catalog and engineering record together.

## Issues

Track [Issue69](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69). Report sanitized reproducible wrapper/native/provider failures with source/version and explicit test tier. Never attach private keys/endpoints or raw prompts/model output.

SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Authored wrapper Apache-2.0. Original Prime Agent MIT; original PHOTON third-party notice Apache-2.0. [Distribution and attribution](UPSTREAM-NOTICE.md); full upstream notices remain installed without relicensing.
