# cline

## What it does

Runs genuine official `cline@3.0.73` in bounded headless JSON/yolo mode. The CLI reads a prompt from anonymous stdin, edits the selected workspace using its native tools and returns buffered NDJSON plus its actual exit code. It uses an explicitly configured OpenAI-compatible provider; a Cline hosted account is not selected. This is the CLI product, with no VS Code extension or desktop UI claim.

## Stack

Alibaba generation2 basev0.0.49/Python3.13, SHA256-pinned official Node24.16.0 and npm integrity-locked Cline3.0.73 with its unmodified Linuxx64 native binary/Bun runtime. Native binary SHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7 is checked before every native invocation. Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a; non-root user, app/home workspace and port9000. [Dockerfile](Dockerfile), [dependency lock](package-lock.json), [design](../docs/design/cline.md).

## Problem solved

Make the real Cline coding agent available through named commands without interactive login, shared developer config or a host-installed CLI. The actual package/help/source tag were inspected; no assumed CLI flags or substitute agent is used. The selected provider/base/model remain explicit and model-generated code runs only inside the caller's newly owned disposable sandbox during acceptance.

## Quick start (CLI)

Install the [verified native CLI entry](../docs/platform-steps.md), configure authorized Express access, publish the exact source commit when preparation needs public COPY inputs, and replace unique-run/template/sandbox placeholders with your own values. Named commands use `abx run`; CLI0.4.1 selects this entry as `abx --native run`. Wait for official READY before creation. This recipe has not itself established a provider pass.

```bash
python scripts/prepare_steps.py cline --output /tmp/cline-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/cline-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> cline_version
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

The expected diagnostic is `{"native_version":"3.0.73"}`. Automatic native step/SDK acceptance uses:

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py cline --sandbox-create sdk --http
```

Once the command server has the model configuration below, a genuine task can use `abx --native run <owned-sandbox-id> cline --json-args '{"prompt":"Inspect the existing project and fix its failing tests","cwd":"project","command_timeout":300}'`. The project directory must already exist inside WORKSPACE. Inspect `exit_code` and native `run_result.finishReason`; installing or echoing a marker does not prove coding success.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` using the [paired source instructions](../docs/python-client-installation.md); import `agent_sandbox`. The model-free example owns and cleans its new sandbox.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("cline_version", timeout=60))
    finally:
        await sb.kill()

asyncio.run(main())
```

For real coding, first configure `CLINE_MODEL_API_KEY`, `CLINE_MODEL_BASE_URL`, `CLINE_MODEL` on the command server before startup. [Explicit process configuration](../docs/runtime-environment.md) explains prewarmed servers: later create-time environment does not reconfigure9000. Verify presence through `cline_setup_check`. Then call `await sb.run("cline", prompt="Fix the existing calc.py and preserve test_calc.py", cwd="project", command_timeout=300, timeout=330)`. This returns `{stdout,stderr,exit_code,native_version}` directly; it does not stream stdout chunks. Nonzero native exit remains a nonzero exit_code, never a success claim.

## Quick start (HTTP POST)

ABX_SERVER_URL is `sb.network.get_url(9000)`. Configure the command server's own ABX_SERVER_TOKEN separately from model/provider credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/cline_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 returns `{"result":{"native_version":"3.0.73"}}`. `POST /commands/cline` accepts direct `{prompt,cwd,command_timeout}` JSON, without an args wrapper. Missing/type-invalid/unknown arguments return400, authentication failure401, unknown command404, semantic guards or execution exceptions500 with `{error,type}`. A completed native process returns its structured result including nonzero exit_code when applicable. Client disconnect does not cancel the bounded process; finally cleanup still owns native descendants/private state.

## Command reference

| Command | Parameters | Return / side effects |
| --- | --- | --- |
| cline_version | none | Actual pinned native version, `{"native_version":"3.0.73"}`; no model/auth |
| cline_setup_check | none | mode `openai-compatible-byok`; base_url_set/api_key_set/model_set booleans; cline_account_required:false; no network/secret values |
| cline | prompt: required nonempty string1..32768UTF-8 bytes, no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"3.0.73"}`; native tool execution and workspace file changes |

The native argv fixes `--json --yolo --provider openai-compatible --model <configured> --cwd <resolved> --compaction off --retries 2 --timeout <seconds>`, plus per-call private `--config` and `--data-dir`. Prompt text enters anonymous stdin, never flags or a shell. Yolo is an unsupervised native act profile with tool auto-approval; native spawn/team tools are disabled by that upstream profile. It is not read-only or a filesystem/tenant boundary. Use trusted callers and a new disposable sandbox without valuable files/other credentials. Argument cwd containment does not remove the native agent's OS authority. Existing caller files may change; no rollback is promised.

Native output is capped256KiB per stream, with whole-process-group/pidfd/unique-owner descendant cleanup on success/failure/timeout/overflow. Calls serialize; overlap fails busy. The caller's original HOME is not used. Explicit model key/base values and JSON-escaped variants are redacted before returning output. Retain only the requested workspace artifacts; owned runtime HOME/config/cache/session/team files are removed after the call.

Pinned3.0.73 checks JSON mode before reading piped input. A fixed, non-secret positional sentence enables that preflight; the actual task still arrives only through anonymous stdin and is appended by upstream. Runtime1.0.1 corrects the real1.0.0 cloud failure; no user prompt or credential is placed in argv.

Runtime1.0.2 writes the provider profile at the exact native-resolved private data/settings/providers.json path: --data-dir overrides CLINE_PROVIDER_SETTINGS_PATH before native startup. Earlier1.0.1 was stopped after independent inspection found its intended base absent from the native-resolved profile. Routing is not qualified until a fresh synthetic-key native wire check confirms the exact owned endpoint before any approved real-model key is provided.

## Configuration

| Name | Required / default | Meaning |
| --- | --- | --- |
| CLINE_MODEL_API_KEY | model required; empty | Approved compatible endpoint key; only forwarded as native OPENAI_API_KEY |
| CLINE_MODEL_BASE_URL | model required; empty | Explicit HTTPS API base, literal localhost HTTP for authored development only; no userinfo/query/fragment; max2048characters |
| CLINE_MODEL | model required; empty | Actual model identifier, max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing workspace root |
| ABX_SERVER_TOKEN | optional; empty | Independent named-server Bearer credential |

Values are captured when commands.py loads. The wrapper writes only provider/model/base metadata into private0600settings, not a model key value; native key resolution uses its documented environment support. Native state is private and removed on return/failure. Global telemetry/auto-update and runtime file logging are disabled; public/private model catalog refresh is disabled. Cline config/data/team/MCP paths are per-call and no caller GitHub/cloud keys, alternate binary override or Cline account token is forwarded. Host operator credentials never enter the native coding process.

## Resources

Linuxx64 only,2vCPU,4096MB, port9000, about10GiB Express rootfs;8GiB image budget enforced. No nested Docker/KVM/GPU is required for this CLI slice. Compatible model tool calling and authorized network egress are required for coding. No hosted Cline/extension/other-provider acceptance or workload memory estimate is claimed.

## Verified

Current native image/Express/SDK/model qualification is pending. `tested_on: []`, catalog experimental. Local source fixtures and real keyless binary version/help are not a real coding/deployment pass.

## Secondary development

```bash
python -m pytest -q cline/test_commands.py cline/test_model_controller.py
python scripts/check_template.py cline --strict
python scripts/check_docs.py
```

Pinned source `cli-v3.0.73`, commitc718573538d76310f464541617ab665108a6c999, defines actual JSON `run_result` with completed finishReason/iterations/text. The external controller invokes the actual paired Python SDK ServerClient.commands.run for the model command and uses independent HTTP files/shell verification. It requires that native terminal event, seeds existing buggy source, preserves original test bytes, downloads fresh report/nonce artifact, reruns complete controller-owned original tests and held-out cases with fresh post-return ACKs, and checks exact owned project absence. Generated source execution is refused on operator loopback and requires explicit owned-cloud opt-in. Required real-model execution never silently skips. Local authored process/NDJSON/credential fixtures prove verifier boundaries only. [Steps guide](../docs/platform-steps.md) covers exact source transfer and resource recovery.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [template spec](../docs/template-spec.md). Keep source pins, contract version, translations and immutable acceptance records consistent.

## Issues

[Template Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Keep credentials/private logs out of public reports.

## License

Wrapper and Cline: Apache-2.0. [Repository license](../LICENSE), [pinned upstream Cline license](UPSTREAM-LICENSE.md). Third-party runtime/dependencies retain their unmodified distribution notices; no hosted account or trademark rights are implied.
