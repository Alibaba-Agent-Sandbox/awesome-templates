# SWE local evaluation slice

## What it does

Runs official `mini-swe-agent==2.4.6` against the genuine SWE-bench Verified instance `pallets__flask-5014`. Prepares the pinned Flask base plus original benchmark tests, reproduces 1 failure and 59 passes, lets an explicitly authorized agent edit source, and evaluates its patch in a fresh checkout and venv. Retrieves a source patch and a JSON report.

This single-instance portability slice does not run the official Docker harness, reproduce its complete original dependency/system environment, or produce a SWE-bench score. Evaluation now pins the instance’s original Python 3.11.10; the dependencies and Debian base below remain a separately tested environment. SWE-agent, SWE-rebench, arbitrary dataset instances and batch benchmarks are outside this slice.

## Stack

Alibaba base `v0.0.49` (resolved by the builder), Python 3.13 server/agent, independent official-SHA Python 3.11.10 evaluation runtime, existing Node.js 20, mini-swe-agent 2.4.6, LiteLLM 1.82.6, pytest 8.3.5. The in-sandbox server uses source `e2cb27e24fde0a67112f82b8d44af463445a5d1a`. See [Dockerfile](./Dockerfile) for all pins. No nested Docker, system installs at runtime or full dataset download.

## Problem solved

Separates an actual source repair from an agent saying it finished. The evaluator reconstructs the original snapshot and test patch, imports only the supported `src/flask/blueprints.py` diff, and requires exactly all 60 declared test identities. Editing agent-side tests or printing a marker cannot supply a passing report. `resolved_slice` is a result for this environment, never an official benchmark score.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

Install the CLI using the [project instructions](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox#readme), then build with Docker available locally:

```bash
abx template deploy ./swe
# Create a dedicated sandbox from the resulting template through the SDK below.
abx run "$SANDBOX_ID" swe_version
ABX_HTTP_TIMEOUT=240 abx run "$SANDBOX_ID" swe_prepare --server-port 9010
ABX_HTTP_TIMEOUT=660 abx run "$SANDBOX_ID" swe_run_agent --server-port 9010 --arg run_id="$RUN_ID" --arg allow_execution=true --arg max_steps=30 --arg command_timeout=600
ABX_HTTP_TIMEOUT=240 abx run "$SANDBOX_ID" swe_evaluate --server-port 9010 --arg run_id="$RUN_ID"
abx run "$SANDBOX_ID" swe_report --server-port 9010 --arg run_id="$RUN_ID"
abx run "$SANDBOX_ID" swe_cleanup --server-port 9010 --arg run_id="$RUN_ID"
```

`RUN_ID` is the opaque field returned by prepare. Use a client HTTP timeout longer than the command deadline for the model call. The SDK recipe below starts the configured server; create-time env values may arrive after a prewarmed default server has started. Do not assume they configure that existing process.

## Quick start (Python SDK)

Use `agent-sandbox-client` with its paired `agent-sandbox-server`; follow [the pinned source installation recipe](../docs/python-client-installation.md).

Install the paired source packages using [the pinned SDK installation recipe](../docs/python-client-installation.md). The Python import is `agent_sandbox`.

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sandbox = await Sandbox.create(os.environ['SWE_TEMPLATE'], provider='alicloud-express', timeout=900)
    stream = None
    consumer = None
    try:
        stream = await sandbox.commands.start(
            'agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py',
            env={key: os.environ[key] for key in ('SWE_API_KEY', 'SWE_BASE_URL', 'SWE_MODEL')}
                | {'WORKSPACE': '/home/user/app', 'ABX_SERVER_BASE_DIR': '/home/user/app', 'SWE_MODEL_PROTOCOL': 'toolcall'},
            timeout=900,
        )
        async def drain():
            async for _ in stream:
                pass
        consumer = asyncio.create_task(drain())  # stream consumption starts the process
        for attempt in range(30):
            try:
                assert await sandbox.run('swe_version', server_port=9010) == 'mini-swe-agent 2.4.6'
                break
            except Exception:
                if attempt == 29:
                    raise
                await asyncio.sleep(1)
        prepared = await sandbox.run('swe_prepare', server_port=9010, timeout=240)
        run_id = prepared['run_id']
        await sandbox.run('swe_run_agent', run_id=run_id, allow_execution=True,
                          max_steps=30, command_timeout=600, server_port=9010, timeout=660)
        report = await sandbox.run('swe_evaluate', run_id=run_id, server_port=9010, timeout=240)
        patch = await sandbox.files.read(report['patch_path'])
        assert report['resolved_slice'] and report['passed'] == 60 and patch
        await sandbox.run('swe_cleanup', run_id=run_id, server_port=9010)
    finally:
        await sandbox.kill()
        if consumer:
            consumer.cancel()
            await asyncio.gather(consumer, return_exceptions=True)
        if stream:
            await stream.cancel()

asyncio.run(main())
```

## Quick start (HTTP POST)

Use `sandbox.network.get_url(9010)` from the configured SDK recipe as `BASE_URL`. The body is the direct argument object, and successful responses wrap the result in `{"result": ...}`.

```bash
curl -fsS -X POST "$BASE_URL/commands/swe_prepare" -H 'Content-Type: application/json' -d '{}'
curl -fsS --max-time 660 "$BASE_URL/commands/swe_run_agent" -H 'Content-Type: application/json' \
  -d '{"run_id":"<prepare run_id>","allow_execution":true,"max_steps":30,"command_timeout":600}'
curl -fsS --max-time 240 "$BASE_URL/commands/swe_evaluate" -H 'Content-Type: application/json' \
  -d '{"run_id":"<prepare run_id>"}'
```

Protect the named server using the server's documented token configuration if exposing it to other callers; authenticate through `sandbox.server_at(9010, token=...)` and HTTP bearer headers. That configuration must be present when the new process starts. Starting another process does not change the default port 9000 server.

## Command reference

| Command | Parameters | Result / execution |
|---|---|---|
| `swe_version` | none | Actual `mini --help` and installed distribution version; no key |
| `swe_setup_check` | none | Boolean runtime/key/base/model availability, no secret values |
| `swe_prepare` | `instance_id: str = "pallets__flask-5014"` | Opaque `run_id`, independently reproduced baseline; other instances rejected |
| `swe_run_agent` | `run_id: str` required; `allow_execution: bool = false`; `max_steps: int = 12` (1–30); `command_timeout: int = 300` (30–900) | Actual `mini -c <installed default.yaml or mini.yaml> -c <private config.yaml> -o <private trajectory>`; requires explicit shell permission; returns model-call count and Submitted status |
| `swe_evaluate` | `run_id: str` required | Fresh base + original tests + supported source diff; exact test states, counts, `resolved_slice`, `official_benchmark_score: false`, patch/report artifact paths |
| `swe_report` | `run_id: str` required | Last evaluation and artifact paths; refuses before evaluation |
| `swe_cleanup` | `run_id: str` required | Deletes only that owned run; returns true |

Malformed types/unknown arguments return HTTP 400. Invalid instance/run ID, missing explicit permission/settings, upstream failure, missing test identities or deadlines return HTTP 500 with sanitized errors. A failed test is a real report with `resolved_slice: false`; collection errors produce no score. Same-run operations use an exclusive lock and refuse conflicts. Operations are synchronous; an HTTP client disconnect is not a cancellation API. Set the command deadline or destroy the owned sandbox to stop work.

## Configuration

The verified real-instance workflow explicitly permits30 agent steps and600 seconds, with a660-second HTTP deadline. Public API defaults remain12 steps/300 seconds; those conservative defaults did not complete the configured model in earlier attempts. A separate owned-cloud diagnostic submitted after25 calls and independently passed all60 original test identities. The strict repeat with that budget still failed before submission; that diagnostic success does not qualify the current template. Version1.1.0 adds the upstream native bash-tool protocol: set `SWE_MODEL_PROTOCOL=toolcall` when starting the configured command server. It selects official `mini.yaml` and LiteLLM native function calls. Default `text` retains the original `default.yaml` text protocol for existing clients. Unknown values fail before a run. Setup reports `native_tool_calls`; the strict controller requires this flag. Test identities, fresh evaluator and scoring/assertion gates remain unchanged. The fresh1.1.0 image and actual cloud/model acceptance passed as recorded below.


Empty `SWE_API_KEY`, `SWE_BASE_URL`, `SWE_MODEL` are declared in YAML and must be injected explicitly into the server process. Model keys go only to the agent process environment; they are excluded from model-action environments. Credentials are absent from argv, config JSON, returned errors and persisted reports. The private trajectory/config directory is removed in `finally`. This is process hygiene, not protection from malicious code running as the same user.

HOME is preserved. Official `MSWEA_GLOBAL_CONFIG_DIR` points to a new private directory, `MSWEA_CONFIGURED=true` prevents interactive setup, dotenv loading is disabled, and installed default config is addressed by its absolute package path. Model/provider, proxy and Git environment overrides are not inherited. Default official local actions create separate sessions; this template uses its documented environment extension interface so ordinary action descendants share the one owned CLI session and can be cleaned up at exit/deadline. Explicitly detached malicious processes are outside this guarantee.

Use only trusted tasks/models in a disposable sandbox: mini executes model-generated bash with the user's filesystem/network permissions. A selected source diff constrains evaluation input; it does not restrict where the running agent can write. Destroy the entire sandbox after the run. Run IDs are not an authentication mechanism.

## Resources

2 vCPU, 2048 MiB; port 9000 by default and 9010 in the explicit configuration recipe. The immutable Flask archive is 692792 bytes; only one instance is embedded. Separate agent and Python 3.11.10 evaluation venvs avoid package collisions. Each run and independent evaluation receives a copy of the pinned evaluation venv. Explicit cleanup frees owned run files; destroy the sandbox afterward.

## Verified

Version1.1.0 passed actual SDK-created Express image registration and official READY, CLI/SDK version smoke and14 strict compatible-model assertions. The actual mini2.4.6 native bash-tool protocol with qwen3.8-flash edited source, preserved all original tests, passed all60 exact test identities in an independent fresh evaluator and retrieved the source patch and report. Sandbox/template/registry cleanup and post-runtime digest were independently confirmed. This is the single-instance portability slice, not an official SWE-bench score. Other providers and full official harness remain unverified.

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.1.0 | alicloud-express | [image](evidence/express-2026-10-20.json), [HTTP](evidence/image-http-2026-10-20T091111Z.json), [strict model14](evidence/model-image-2026-10-20T091111Z.json) |

## Historical verification

No provider has a passing run recorded for this template.

L0 contract checks can skip missing upstream runtime/model prerequisites, and such skips do not prove agent execution. L1/L2/L3 status is recorded in the PR and owner evidence. The initial Python3.13 image reproduced 2PASS/58ERROR because upstream treats deprecated pkgutil.get_loader as an error; its tests/warning filters were preserved. With pinned original Python3.11.10, the actual CI image passed the exact1FAIL59PASS baseline, real mini/Qwen3.8-flash repair, fresh60PASS evaluation and remote patch/report retrieval (14PASS/0FAIL/0SKIP). All10owned cleanup flags and additional strict absence readbacks passed; see [actual image evidence](./evidence/image-runtime-2026-10-16-configured.json) and [strict readback](./evidence/image-runtime-2026-10-16-strict-readback.json). Canonical local abx template deploy remains unrun, so formal provider verification stays empty. Full official Docker harness and other providers remain unverified. Do not publish this report as a benchmark score.

## Secondary development

Read [design](../docs/design/swe.md) and [spec](../docs/template-spec.md). Add another instance only after verifying its pinned source archive, license, original test patch, precise FAIL_TO_PASS/PASS_TO_PASS lists, compatible locked dependencies and independent failing/passing tests. Do not expose arbitrary shell test commands, URL downloads or caller-supplied patches through this API. The manifest deliberately excludes the upstream gold solution patch.

### Agent Sandbox platform steps
The actual1.1.0 step attempt did not reach independently confirmed READY within1200seconds. It is a [failed attempt](evidence/verification-steps-2026-10-20T091943Z.json), with [separate confirmed cleanup](evidence/steps-cleanup-2026-10-20.json); it does not qualify step builds. The passing current image/model receipt remains separate.


From a repository checkout, `python scripts/run_steps_e2e.py swe` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Run `python -m pytest -q swe/test_commands.py swe/test_e2e_protocol.py`, `python3 scripts/check_template.py swe`, `python3 scripts/test_spec_tools.py`, and `python3 scripts/run_local_e2e.py`. Build the actual image, run the [canonical Express deployment](../scripts/express_e2e.py), and run `E2E_REQUIRE_LLM=1 E2E_RUN_LLM=1 E2E_BASE_URL=<configured server> python swe/e2e_test.py` with a compatible model. Preserve failures/skips and record exact source revisions, test identities, patch retrieval and owned resource cleanup. Never submit raw trajectories, credentials or private resource IDs.

## Issues

[Template Issue #35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35) owns this partial implementation and remaining official/full deployment gates. SDK/server problems belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI problems in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper Apache-2.0. mini-swe-agent 2.4.6 is MIT; Flask is BSD-3-Clause. SWE-bench Verified metadata/test patch follows the dataset's MIT license. Bundled CPython retains its distribution license files. Provenance and upstream license links are in [NOTICE](./NOTICE.md); upstream source archives retain their own license files.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).

### Current platform-step acceptance

The later [current-version real step receipt](evidence/express-2026-10-20T143844Z.json) and [full external HTTP result](evidence/verification-steps-2026-10-20T143844Z.json) supersede the earlier failed step attempt for current readiness: official READY, actual Python SDK creation, CLI/SDK smoke and 5 HTTP PASS / 0 FAIL / 1 explicit model SKIP passed in 1090.426 seconds. Independent owned sandbox/template and temporary private asset-cache cleanup passed. This step receipt is model-free; earlier image/model receipts keep their own scope.
