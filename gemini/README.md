# gemini

## What it does

Run original official Google Gemini CLI0.64.0 planning and text/file/shell tools. Existing gemini/setup/version APIs remain; gemini_byok adds explicit compatible Chat transport through an authored GenerateContent-to-Chat text/tool adapter. Original CLI/tool engine is unchanged; Google Gemini model access, OAuth, hosted subscriptions and full feature compatibility are not claimed. [Official configuration](https://geminicli.com/docs/reference/configuration/).

## Stack

Alibaba generation2basev0.0.49/Linuxx64/Python3.13/Node20; original npm0.64.0/SHA512 integrity lock; all449original package files/98597935bytes independently SHA256-pinned in [upstream.json](upstream.json), archive20841287bytes/SHA256891a794e55c8319b6b78f6f8f13d6b8b2782a4709dfd2fcabf3a1f63ae8365e6. `npm ci --omit=optional --ignore-scripts` omits interactive native PTY/keychain add-ons and scripts. Original bundled notices/code remain unchanged. Server34e7e011c5569f77b7f605e65313be7498f6cf02, stdlib authored adapter/process controls. [Dockerfile](Dockerfile), [design](../docs/design/gemini.md), [notice](UPSTREAM-NOTICE.md).

## Problem solved

Give an explicitly approved Chat gateway access to original Gemini text/tool planning without sending its key to a default Google endpoint. The adapter translates original function schemas, arguments and correlated results; it does not execute tools or replace the native planner. Native API environment variables select only the owned local adapter, with a fresh token and no real child key.

## Quick start (CLI)

The `abx run` native entry is `abx --native run`. Use verified CLI0.4.1/existing authorized Express settings. Replace placeholders, publish exact source before immutable COPY, choose a unique owned manifest name, wait for official READY and retain IDs for cleanup.

```bash
python scripts/prepare_steps.py gemini --output /tmp/gemini-steps-<unique-run> \
  --server-commit 34e7e011c5569f77b7f605e65313be7498f6cf02
python - <<'CONFIG'
from pathlib import Path
import yaml
p=Path('/tmp/gemini-steps-<unique-run>/template.yaml')
v=yaml.safe_load(p.read_text());v['name']='gemini-<unique-run>'
p.write_text(yaml.safe_dump(v,sort_keys=False))
CONFIG
abx --native template deploy /tmp/gemini-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> gemini_version
abx --native run <owned-sandbox-id> gemini_native_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

Canonical ownership: `ABX='abx --native' python scripts/run_steps_e2e.py gemini --sandbox-create sdk --http`. Native steps require no local Docker daemon and do not certify Docker image cloud deployment. On a configured process, call `abx --native run <owned-sandbox-id> gemini_byok --json-args '{"prompt":"Repair existing calc.py and preserve tests","cwd":"project","command_timeout":300}'`.

## Quick start (Python SDK)

Install distribution agent-sandbox-client through the [paired fixed source instructions](../docs/python-client-installation.md).

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox
async def main():
    sb=await Sandbox.create(template='<owned-template-id>',timeout=900)
    try:
        print(await sb.run('gemini_version',timeout=60))
        print(await sb.run('gemini_native_check',timeout=60))
    finally:
        await sb.kill()
asyncio.run(main())
```

Set all GEMINI_BYOK_* variables before the named-command server starts; inspect gemini_byok_setup_check, then `await server.commands.run('gemini_byok',prompt='Repair existing calc.py; preserve tests',cwd='project',command_timeout=300,timeout=420)`. Create the project first. For an independent process use sb.server_at(port,token=...) and close the borrowed client. A prewarmed9000process does not acquire later create-time env; follow [explicit process configuration](../docs/runtime-environment.md). A separately configured9010server uses its matching independent token. Results are buffered direct objects.

## Quick start (HTTP POST)

ABX_SERVER_URL is sb.network.get_url(port) of the configured process; its Bearer is separate from platform/model credentials.

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gemini_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' --data '{}'
```

HTTP200 returns {"result":"0.64.0"}. POST/commands/gemini_byok accepts direct {prompt,cwd,command_timeout} JSON. Missing/unknown/type arguments400, authentication401, unknown command404; native/semantic errors500 with sanitized diagnostics. Disconnect does not cancel a provider job; bounded owned cleanup still runs.

## Command reference

| Command | Parameters | Result / effects |
| --- | --- | --- |
| gemini_version | none | Original CLI0.64.0; no model |
| gemini_native_check | none | Exact original449file identity plus actual help flags original_native/headless_json/explicit_approval/owned_project_include |
| gemini_byok_setup_check | none | mode/model_key_set/model_base_set/model_set, vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true; no values/network |
| gemini_byok | prompt required nonempty1..32768UTF8bytes/noNUL; cwd default empty string/max4096bytes/existing resolved directory within WORKSPACE; command_timeout integer1..600seconds/default300/no bool | stdout/exit_code0/native_completed/native_version/archive_sha256/model/protocol/model_calls/native_tool_results/relay_calls; native tools modify caller project; no raw transcript |
| gemini_setup_check | none | Legacy installed/version/pinned_version/key/model presence/workspace/settings path/existence/JSON-validity inspection; no changes/authentication |
| gemini | prompt required nonempty string; model default empty string then GEMINI_MODEL then gemini-3.1-flash-lite; cwd default empty/contained existing directory; command_timeout integer600/range1..1800seconds; yolo booleanFalse | Legacy original buffered JSON string. yoloFalse selects plan, True explicitly permits tool execution. Requires GEMINI_API_KEY, no implicit OpenAI-key/OAuth fallback. New BYOK isolation guarantees do not certify legacy mode |

New fixed profile: --prompt/--model/--output-format json/--approval-mode yolo/--include-directories <contained-project>. Launch cwd is a fresh private directory; prompt includes absolute project path. Hash-pinned root-owned /opt/gemini/profile.json system settings force gemini-api-key auth,16model session turns, hooks/skills/subagents/update/telemetry disabled, no configured MCP/installed extensions. Original core tools are read_file/write_file/replace/run_shell_command/list_directory/glob/grep_search. No delegation tool. Native original file/tool code executes only on an owned disposable sandbox; project instructions remain untrusted input.

Translate only text and original function declarations/results with exact IDs or deterministic same-history name correlation when native IDs are absent. Google schema type case/nullability is mapped explicitly. Unsupported images/thinking/content/tool types, mismatched results, truncated replies, wrong model path/token and redirects are refused. Upstream Chat is buffered and emitted as original GenerateContent SSE; actual usage comes from upstream.32requests/2MiBrequest/4MiBresponse/16native turns,256KiB each stdout/stderr; command deadline plus up to90seconds owned cleanup, client timeout at least command_timeout+120. Concurrent BYOK returns busy. Completion requires original successful nonempty response, completed upstream requests and no failed responses; coding also requires positive native tool results and independent artifacts/tests.

## Configuration

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| GEMINI_BYOK_API_KEY | empty; required for BYOK | Explicit compatible upstream key, parent adapter only |
| GEMINI_BYOK_BASE_URL | empty; required for BYOK | HTTPS Chat base/max2048chars/no userinfo/query/fragment; literal-loopback HTTP for fixtures |
| GEMINI_BYOK_MODEL | empty; required for BYOK | Actual selected identifier1..200allowed characters |
| GEMINI_API_KEY | empty; legacy only | Existing Google/native-compatible key; BYOK never silently reuses it |
| GEMINI_MODEL | gemini-3.1-flash-lite; legacy only | Existing legacy default; separate from explicit BYOK selection |
| WORKSPACE | /home/user/app | Existing caller project root |
| ABX_SERVER_TOKEN | empty/optional | Separate command-server Bearer |

BYOK settings captured at module import; key max8192/no control characters. Native environment has only fresh local adapter token, minimal PATH and private HOME/config/cache; real upstream key is sent only to exact approved Chat origin. Same-user OS access remains; cwd/environment filters are not another tenant boundary. Existing legacy configuration behavior stays separate. No private endpoints/keys/transcripts in results or errors.

## Resources

Declared2vCPU4096MB/Linuxx64/port9000/8GiBrootfs budget; no KVM/nested Docker/GPU/display. Original package98.6MB, Node20 already in base; optional interactive add-ons omitted. Approved model egress required. Peak memory, image cloud deployment, other providers, Google OAuth/subscription, full interactive/resume/PTY/image/thinking/MCP/plugin/delegation product not certified.

## Verified

Template2.1.4 / original CLI0.64.0, tested2026-10-21 at source393c5cc.

| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | Immutable native steps; actual SDK create and CLI/SDK smoke; full HTTP10/10; original native two-turn read_file API fixture; actual approved compatible model source-edit19/19; independent owned cleanup | [receipt](evidence/express-2026-10-21T085925Z.json), [full proof](evidence/verification-steps-2026-10-21T085924Z-real-model.json) |

The synthetic API fixture makes2completed requests with1original tool result and0failed responses; it is separate from the real model run. The real model is qwen3.8-flash through the explicit authored text/tool adapter. Original3test bytes, report, exact fresh nonce,3original and4held-out assertions and fresh post-return ACK pass. Google-hosted model/account/OAuth authentication remains NOT_RUN. Current source393c5cc image-build CI passed; final documentation-head CI/review/merge are separate gates. Local93testsPASS1SKIP9.49seconds; missing operator-native CLI is the skip. Historical2.0.1 receipts do not qualify2.1.4.

## Secondary development

```bash
python -m pytest -q gemini/test_byok.py gemini/test_adapter.py gemini/test_controller.py gemini/test_commands.py gemini/test_e2e_protocol.py
python scripts/check_template.py gemini --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py gemini --sandbox-create sdk --http
```

Preserve exact original inventory/lock/notices, real-key isolation, strict origin and content refusal, owned process/RPC/private/listener cleanup. Local replies are fixed non-executable fixtures; original native/generated-code acceptance only on fresh explicitly owned cloud. Main e2e dispatches strict current BYOK controller; legacy helpers/regressions remain. Record both dispatch and byok_e2e_test.py hashes. Require changed source, original3test bytes/report/exact nonce/original3+4held-outs/fresh post-returnACK and independent owned absence.

## Contributing

Read [CONTRIBUTING](../CONTRIBUTING.md), [project standards](../docs/project-standards.md), [documentation standards](../docs/documentation-standards.md) and [template spec](../docs/template-spec.md). Include owner note/evidence, bilingual contracts, latest-head review/checks and normal merge.

## Issues

[Issue30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30), [templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), [Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Original upstream behavior uses upstream channels. Never attach credentials/private transcripts.

## License

Authored template/adapter and original Gemini CLI are Apache-2.0 under their respective original [licenses/notices](UPSTREAM-NOTICE.md); retain bundled third-party terms. [Repository license](../LICENSE). No Google endorsement or hosted model access claim.

The text/tool adapter accepts only the original CLI fixed `skip_thought_signature_validator` placeholder on function calls and removes that metadata during translation. Other thought signatures and thinking content remain unsupported and rejected.
