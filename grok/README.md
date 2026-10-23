# grok

## What it does

Runs genuine official xAI `@xai-official/grok@1.0.62` headless coding. The native Rust binary reads anonymous stdin through --prompt-file /dev/stdin, uses its real tools and returns buffered JSON plus actual exit code. An explicitly configured approved compatible model is selected. This is xAI Grok Build, not the unrelated community grok-dev CLI; compatible-model success does not qualify xAI-hosted Grok models or subscriptions.

[Official xAI source snapshot](https://github.com/xai-org/grok-build/tree/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8), [native custom models](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md), [headless protocol](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md).

## Stack

Alibaba generation2 basev0.0.49/Python3.13, SHA256-pinned official Node24.16.0 and npm integrity-locked Grok Build1.0.62 with its unmodified Linuxx64 native Rust binary. Native binary SHA2562a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa is checked before every native invocation. Server source e2cb27e24fde0a67112f82b8d44af463445a5d1a; non-root user, app/home workspace and port9000. [Dockerfile](Dockerfile), [dependency lock](package-lock.json), [design](../docs/design/grok.md).

## Problem solved

Make the real Grok Build coding agent available through named commands without interactive login, shared developer config or a host-installed CLI. The actual package/help/source tag were inspected; no assumed CLI flags or substitute agent is used. The selected provider/base/model remain explicit and model-generated code runs only inside the caller's newly owned disposable sandbox during acceptance.

## Quick start (CLI)

Install the [verified native CLI entry](../docs/platform-steps.md), configure authorized Express access, publish the exact source commit when preparation needs public COPY inputs, and replace unique-run/template/sandbox placeholders with your own values. Named commands use `abx run`; CLI0.4.1 selects this entry as `abx --native run`. Wait for official READY before creation. The dated Verified section records the actual tested source and scope.

```bash
python scripts/prepare_steps.py grok --output /tmp/grok-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/grok-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> grok_version
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

The expected diagnostic is `{"native_version":"1.0.62"}`. Automatic native step/SDK acceptance uses:

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py grok --sandbox-create sdk --http
```

Once the command server has the model configuration below, a genuine task can use `abx --native run <owned-sandbox-id> grok --json-args '{"prompt":"Inspect the existing project and fix its failing tests","cwd":"project","command_timeout":300}'`. The project directory must already exist inside WORKSPACE. Inspect `exit_code` and native `stopReason`; installing or echoing a marker does not prove coding success.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` using the [paired source instructions](../docs/python-client-installation.md); import `agent_sandbox`. The model-free example owns and cleans its new sandbox.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("grok_version", timeout=60))
    finally:
        await sb.kill()

asyncio.run(main())
```

For real coding, first configure `GROK_MODEL_API_KEY`, `GROK_MODEL_BASE_URL`, `GROK_MODEL` on the command server before startup. [Explicit process configuration](../docs/runtime-environment.md) explains prewarmed servers: later create-time environment does not reconfigure9000. Verify presence through `grok_setup_check`. Then call `await sb.run("grok", prompt="Fix the existing calc.py and preserve test_calc.py", cwd="project", command_timeout=300, timeout=330)`. This returns `{stdout,stderr,exit_code,native_version}` directly; it does not stream stdout chunks. Nonzero native exit remains a nonzero exit_code, never a success claim.

## Quick start (HTTP POST)

ABX_SERVER_URL is `sb.network.get_url(9000)`. Configure the command server's own ABX_SERVER_TOKEN separately from model/provider credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/grok_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 returns `{"result":{"native_version":"1.0.62"}}`. `POST /commands/grok` accepts direct `{prompt,cwd,command_timeout}` JSON, without an args wrapper. Missing/type-invalid/unknown arguments return400, authentication failure401, unknown command404, semantic guards or execution exceptions500 with `{error,type}`. A completed native process returns its structured result including nonzero exit_code when applicable. Client disconnect does not cancel the bounded process; finally cleanup still owns native descendants/private state.

## Command reference

| Command | Parameters | Return / side effects |
| --- | --- | --- |
| grok_version | none | Actual pinned native version, `{"native_version":"1.0.62"}`; no model/auth |
| grok_setup_check | none | mode `openai-compatible-byok`; base_url_set/api_key_set/model_set booleans; xai_account_required:false; no network/secret values |
| grok | prompt: required nonempty string1..32768UTF-8 bytes, no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"1.0.62"}`; native tool execution and workspace file changes |

Fixed native flags select --output-format json, --always-approve, --no-plan, --no-subagents, --disable-web-search, --sandbox off, --model abx-approved, --max-turns20 and --prompt-file /dev/stdin. The tools allowlist contains read_file/search_replace/grep/list_dir/run_terminal_cmd; Agent is denied. Native sandbox off leaves tool OS authority inside the caller’s trusted disposable outer sandbox; cwd containment is only an argument boundary. Native tool approvals are automatic; no rollback is promised. Prompt and model key values never enter argv.

Native output is capped256KiB per stream, with whole-process-group/pidfd/unique-owner descendant cleanup on success/failure/timeout/overflow. Calls serialize; overlap fails busy. The caller's original HOME is not used. Explicit model key/base values and JSON-escaped variants are redacted before returning output. Retain only the requested workspace artifacts; owned runtime HOME/config/cache/session/team files are removed after the call.


## Configuration

| Name | Required / default | Meaning |
| --- | --- | --- |
| GROK_MODEL_API_KEY | model required; empty | Approved compatible endpoint key; only forwarded as native ABX_GROK_MODEL_KEY |
| GROK_MODEL_BASE_URL | model required; empty | Explicit HTTPS API base, literal localhost HTTP for authored development only; no userinfo/query/fragment; max2048characters |
| GROK_MODEL | model required; empty | Actual model identifier, max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing workspace root |
| ABX_SERVER_TOKEN | optional; empty | Independent named-server Bearer credential |

Values are captured when commands.py loads. A private0600 config.toml stores explicit model/base and env_key="ABX_GROK_MODEL_KEY" without the key value. Custom api_backend="chat_completions" prevents selecting a hosted vendor model. Private GROK_HOME/HOME/cache/session state is removed after each call; auto-update, leader, telemetry/trace upload, memory and background workflows are disabled. Native shell_environment_policy inherits core with default secret exclusion; no caller cloud/GitHub/vendor account token is forwarded. Agent tools still have OS authority in the disposable sandbox.

## Resources

Linuxx64 only,2vCPU,4096MB, port9000, about10GiB Express rootfs;8GiB image budget enforced. No nested Docker/KVM/GPU is required for this CLI slice. Compatible model tool calling and authorized network egress are required for coding. No hosted Grok Build/extension/other-provider acceptance or workload memory estimate is claimed.

## Verified

No project-recognized receipt certifies the current workflow manifest. Historical acceptance records retain only their original input and call-path scope; see [workflow verification](../docs/workflows.md).

## Secondary development

```bash
python -m pytest -q grok/test_commands.py grok/test_model_controller.py
python scripts/check_template.py grok --strict
python scripts/check_docs.py
```

Actual official binary reports `grok1.0.62 (1474f9cbdd91)` and matching SHA256. Public source snapshot2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 documents the custom model/headless contracts; it is not claimed as the binary build commit. The real Python SDK named command is followed by independent HTTP source/artifact/original-tests and fresh post-return held-out checks on a newly owned cloud target. JSON requires end_turn, positive actual num_turns and real session/request IDs; a text marker alone is insufficient. Local fixture controls and keyless help/version are not native model/cloud passes.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md) and [template spec](../docs/template-spec.md). Keep source pins, contract version, translations and immutable acceptance records consistent.

## Issues

[Template Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40). [SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) and [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) defects use `[templates]` prefixes. Keep credentials/private logs out of public reports.

## License

Wrapper and official xAI Grok Build: Apache-2.0. [Repository license](../LICENSE), [upstream license](UPSTREAM-LICENSE.md), [official binary third-party notices](THIRD_PARTY_NOTICES.md). Distribution dependencies retain their notices; no hosted subscription, model or trademark rights are implied.
