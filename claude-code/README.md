# claude-code

## What it does

Run unchanged official Claude Code2.0.76 headless planning and Read/Edit/Write/Bash tools. Existing `claude` retains its Anthropic-oriented API; new `claude_byok` explicitly uses an authored Messages-to-OpenAI-Chat text/tool adapter. Compatible-model use is experimental and [not supported by Anthropic](https://code.claude.com/docs/en/llm-gateway); no Claude-model/subscription/vendor endorsement claim.

## Stack

Alibaba generation2 basev0.0.49/Linuxx64/Python3.13/Node20; original npm package2.0.76 from its SHA512 integrity lock; exact original cli.js SHA256 in [upstream.json](upstream.json). `npm ci --omit=optional --ignore-scripts` excludes optional image codecs and package hooks. Original CLI, embedded tool code and bundled notices remain unchanged. Server source34e7e011c5569f77b7f605e65313be7498f6cf02, authored stdlib adapter/process ownership. [Dockerfile](Dockerfile), [license notice](UPSTREAM-NOTICE.md), [design](../docs/design/claude-code.md).

## Problem solved

Expose original native tool execution through SDK/HTTP, with a new explicitly selected compatible text/tool profile when the approved gateway only provides Chat. The adapter translates protocol messages, preserves original tool names/arguments/results and leaves tool execution to the original CLI. It does not implement another planner or forward credentials to a default vendor.

## Quick start (CLI)

The `abx run` native entry is `abx --native run`. Use verified CLI0.4.1 native entry, existing authorized Express settings and a unique owned run. Publish the exact source before immutable COPY preparation. Replace all placeholders; wait for official READY and retain all owned IDs for cleanup.

```bash
python scripts/prepare_steps.py claude-code --output /tmp/claude-steps-<unique-run> \
  --server-commit 34e7e011c5569f77b7f605e65313be7498f6cf02
python - <<'CONFIG'
from pathlib import Path
import yaml
p=Path('/tmp/claude-steps-<unique-run>/template.yaml')
v=yaml.safe_load(p.read_text());v['name']='claude-<unique-run>'
p.write_text(yaml.safe_dump(v,sort_keys=False))
CONFIG
abx --native template deploy /tmp/claude-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> claude_version
abx --native run <owned-sandbox-id> claude_native_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Canonical owned steps: `ABX='abx --native' python scripts/run_steps_e2e.py claude-code --sandbox-create sdk --http`. Steps do not certify Docker image cloud deployment. For configured coding, `abx --native run <owned-sandbox-id> claude_byok --json-args '{"prompt":"Repair existing calc.py and preserve its tests","cwd":"project","command_timeout":300}'`.

## Quick start (Python SDK)

Install distribution `agent-sandbox-client` using the [paired pinned source instructions](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox
async def main():
    sb=await Sandbox.create(template='<owned-template-id>',timeout=900)
    try:
        print(await sb.run('claude_version',timeout=60))
        print(await sb.run('claude_native_check',timeout=60))
    finally:
        await sb.kill()
asyncio.run(main())
```

Set all three CLAUDE_MODEL_* variables before the named-command process starts, check `claude_setup_check`, and invoke `await server.commands.run('claude_byok',prompt='Repair existing calc.py; preserve its tests',cwd='project',command_timeout=300,timeout=420)`. Create the project first. Use `sb.server_at(port,token=...)` and close that borrowed client after use. A prewarmed9000process does not acquire later create-time env; follow [explicit process configuration](../docs/runtime-environment.md). An independently configured9010server needs a separate matching Bearer token. Results are buffered direct objects.

## Quick start (HTTP POST)

ABX_SERVER_URL is `sb.network.get_url(port)` for the configured process; its Bearer token is independent of model/platform credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/claude_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' --data '{}'
```

HTTP200 returns `{"result":"2.0.76 (Claude Code)"}`. `POST /commands/claude_byok` takes direct `{prompt,cwd,command_timeout}` JSON. Missing/unknown/type arguments400, auth401, unknown command404; semantic/native errors500 with sanitized diagnostics. Disconnect does not cancel an issued provider job; bounded owned process/adapter cleanup still runs.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| claude_version | none | Original CLI `2.0.76 (Claude Code)`; no model |
| claude_native_check | none | Original cli.js hash and help flags: original_native/isolated_settings/no_session_persistence/strict_mcp booleans |
| claude_setup_check | none | Mode and model_key_set/model_base_set/model_set presence, vendor_account_verified:false/provider_default_fallback:false; no values/network |
| claude_byok | prompt: required string1..32768UTF8bytes/nonempty/noNUL; cwd: default empty string, max4096bytes, existing resolved directory within WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | stdout/exit_code0/native_completed/native_version/cli_sha256/model/protocol/model_calls/native_tool_results/relay_calls. Original tools edit project; no raw transcript |
| claude | prompt: required nonempty string; model: string default sonnet; cwd: string default empty/contained existing directory; allowed_tools: string default Read,Edit,Write; resume: string default empty; command_timeout: integer300/range1..900seconds | Legacy original JSON encoded as a string, sanitized for environment secrets. Uses existing Anthropic credential/settings behavior; bounded isolated BYOK guarantees do not certify this legacy mode |

New fixed profile: `-p --model <selected> --output-format json --permission-mode dontAsk --tools Read,Edit,Write,Bash --allowedTools Read,Edit,Write,Bash --settings <owned> --setting-sources '' --no-session-persistence --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --no-chrome --max-turns16`. Hooks disabled, thinking tokens0; no Task tool, subagents, MCP, plugin or project/local settings loading. Project instructions remain untrusted input; use only an owned disposable target.

Text and original tool schemas/results are translated; unsupported image/thinking/content/tool types, truncated replies, wrong model/token/path and redirects fail closed. Upstream Chat is buffered then emitted as native Messages SSE.32requests/2MiBrequest/4MiBresponse maximum,16native turns,256KiB each native stdout/stderr. Actual native successful result and positive completed transport counts are required. Coding qualification additionally requires positive native tool results and independently downloaded files/tests. Own process/private state and issued RPCs drain before return; cleanup may add up to90seconds, client timeout at least command_timeout+120. Concurrent BYOK calls fail busy.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| CLAUDE_MODEL_API_KEY | empty; required for BYOK | Explicit approved compatible upstream key; parent adapter only |
| CLAUDE_MODEL_BASE_URL | empty; required for BYOK | HTTPS Chat base/no userinfo/query/fragment/max2048chars; literal-loopback HTTP for fixed fixtures |
| CLAUDE_MODEL | empty; required for BYOK | Selected model1..200identifier characters |
| ANTHROPIC_API_KEY | empty; legacy mode only | Existing Anthropic-compatible legacy configuration; not silently reused by BYOK |
| WORKSPACE | /home/user/app | Existing project root |
| ABX_SERVER_TOKEN | empty; optional | Separate command-server credential |

New settings captured at module import. Key max8192/no control characters; no default provider/model/key fallback. Native/tool environment gets only an ephemeral local adapter token and minimal private HOME/config/cache; real upstream key remains in the parent and is sent only to exact configured Chat origin. Original command results and error messages omit credentials/private endpoints/transcripts. Same-user OS access remains; environment filtering/cwd containment is not another tenant boundary. Legacy resume/settings behavior is retained and outside BYOK isolation claims.

## Resources

Declared2vCPU2048MB, Linuxx64, port9000,8GiB image rootfs budget; no KVM/Docker/GPU/display requirement. Official npm archive26.4MB/original package70.9MB, Node20 already in base. Approved model egress required; optional image codecs omitted. Peak memory not measured. Full Claude service, OAuth/subscription, interactive/resumed sessions, images/thinking/MCP/plugins/delegation remain unverified.

## Verified

Current1.2.0 provider/native/model acceptance is PENDING. Earlier1.1.1 receipts remain immutable historical evidence and do not qualify this changed profile. Local38fixed transport/privacy/process controls PASS; this is not a cloud/model pass. Final actual Express, image, original CLI and model evidence must be recorded before qualification or Issue closure.

## Secondary development

```bash
python -m pytest -q claude-code/test_byok.py claude-code/test_adapter.py
python scripts/check_template.py claude-code --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py claude-code --sandbox-create sdk --http
```

Keep original package and notices, lockfile/integrity/hash, explicit approved origin, no real child key, unsupported-feature refusal and owned descendants/listener/private cleanup. Fixed non-executable protocol replies may run locally. Original native/generated-code verification runs only on a fresh owned cloud target; preserve original tests and independently assert artifacts and post-return held-outs.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include bilingual docs, owner note/evidence and current-head review/checks.

## Issues

[Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15), [template defects](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses its support channels. Never attach credentials or private transcripts.

## License

Authored template/adapter: [Apache-2.0](../LICENSE). Original Anthropic package remains all rights reserved under its [original terms/notices](UPSTREAM-NOTICE.md); no relicensing or vendor endorsement.
