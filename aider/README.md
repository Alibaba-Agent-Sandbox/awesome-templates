# Aider

## What it does

Runs the official `aider-chat==0.86.2` CLI against an explicitly selected git
working tree. The default is read-only **ask** mode. `allow_write=true` permits
whole-file edits to explicitly listed source/artifact paths. The wrapper stages
only those files, runs Aider, checks the original files have not changed, then
copies back selected results. It never auto-commits.

## Stack

Alibaba FC base `v0.0.49`, its Python 3.13 server and Node 20 remain intact.
Aider requires Python `>=3.10,<3.13`; a separate SHA256-verified official
python-build-standalone **3.12.12 / 20260211** runs Aider in `/opt/aider`.
The server uses a source-built wheel or the fixed SDK commit in the Dockerfile.
No browser, Node upgrade or additional HTTP server is installed.

## Problem solved

Run a reproducible code review or bounded edit without installing Aider into the
caller's environment, mixing its pinned Python dependencies with the server, or
sending the entire repository/configuration to a model by default. This is a
selected-file workflow, not a general replacement for interactive Aider.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

```bash
abx template install alibaba-agent-sandbox/awesome-templates//aider
abx template deploy ./aider -y
abx create --template <template-id>
abx exec <sandbox-id> --background --env AIDER_API_KEY=REPLACE_ME \
  --env AIDER_BASE_URL=https://example.invalid/v1 --env AIDER_MODEL=your-model \
  -- agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py
abx exec <sandbox-id> -- agent-sandbox-server healthcheck --port 9010
abx run <sandbox-id> aider_setup_check --server-port 9010
abx exec <sandbox-id> -- sh -c 'mkdir -p /home/user/app/project && cd /home/user/app/project && git init -q'
abx run <sandbox-id> aider --server-port 9010 --json-args '{"prompt":"Explain the selected file","cwd":"/home/user/app/project","files":"[\"calculator.py\"]"}'
```

Upload your source with `abx upload` first. Explicit write request:

```bash
abx run <sandbox-id> aider --server-port 9010 --json-args '{"prompt":"Fix calculator.py and write REPORT.md","cwd":"/home/user/app/project","files":"[\"calculator.py\",\"REPORT.md\"]","allow_write":true,"command_timeout":180}'
abx exec <sandbox-id> -- sh -c 'cd /home/user/app/project && git diff -- calculator.py'
abx kill <sandbox-id>
```

Wait for the port-9010 healthcheck and all three setup booleans before calling
Aider. The CLI env options and JSON prompts are host argv; use the SDK process
`env` example below when credentials must stay out of host argv/history.

The caller creates/owns the working tree. Review diffs and run your own tests;
exit code zero means the CLI completed, not that generated code is correct.

## Quick start (Python SDK)

Install the paired `agent-sandbox-client` / server from a
[pinned SDK source](../docs/python-client-installation.md) while the release is
unpublished. `pip install agent-sandbox` is an unrelated project.

```python
import asyncio
import json
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600)
    stream = None
    server_task = None
    try:
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py",
            env={"AIDER_API_KEY": os.environ["AIDER_API_KEY"],
                 "AIDER_BASE_URL": os.environ["AIDER_BASE_URL"],
                 "AIDER_MODEL": os.environ["AIDER_MODEL"],
                 "ABX_SERVER_BASE_DIR": "/home/user/app"}, timeout=600)
        async def drain():
            async for _ in stream:
                pass
        server_task = asyncio.create_task(drain())
        for attempt in range(30):
            try:
                state = await sb.run("aider_setup_check", server_port=9010, timeout=10)
            except Exception:
                if attempt == 29:
                    raise
                await asyncio.sleep(1)
                continue
            if not all(state[name] for name in ("api_key_set", "base_url_set", "model_set")):
                raise RuntimeError("the configured server did not receive all settings")
            break
        await sb.commands.run("mkdir -p /home/user/app/project && cd /home/user/app/project && git init -q")
        await sb.files.write("/home/user/app/project/calculator.py", "def add(a,b): return a-b\n")
        result = await sb.run("aider", prompt='Fix add and write REPORT.md', cwd="/home/user/app/project",
            files=json.dumps(["calculator.py", "REPORT.md"]), allow_write=True,
            server_port=9010, command_timeout=180, timeout=210)
        print(result["changed_files"])
        print(await sb.files.read("/home/user/app/project/REPORT.md"))
    finally:
        await sb.kill()
        if server_task is not None:
            server_task.cancel()
            await asyncio.gather(server_task, return_exceptions=True)
        if stream is not None:
            await stream.cancel()

asyncio.run(main())
```

## Quick start (HTTP POST)

Port 9000 is the sandbox server. Obtain its URL from `sb.network.get_url(9010)`.
Use the configured process URL from `sb.network.get_url(9010)`. Send the command's
direct argument object, without an `args` wrapper:

```http
POST /commands/aider
Content-Type: application/json
Authorization: Bearer REPLACE_ME

{"prompt":"Explain calculator.py","cwd":"/home/user/app/project","files":"[\"calculator.py\"]","allow_write":false,"command_timeout":180}
```

The shape is `{"result":{"stdout":"...","stderr":"...","exit_code":0,"changed_files":[]}}`.
The bearer token is needed only when you configure `ABX_SERVER_TOKEN`; provider
gateway authentication is separate. Configure `sb.server_at(9010, token=...)`
when using server authentication. Do not substitute the envd gateway token for
the server bearer token. HTTP 400 means missing/mistyped arguments or malformed
request framing, 401 authentication failure, 404 unknown command, and 500 a
semantic validation/upstream/deadline error. Error bodies contain `error` and
`type`; upstream error text is deliberately omitted.

The named command buffers output. `command_timeout` limits the owned CLI process
group. SDK `timeout` controls the HTTP client wait and should be longer. An HTTP
client disconnect does not cancel an in-flight command. For long background work,
use the sandbox process API and explicitly kill its process or destroy the owned
sandbox. Python cancellation/timeout within the wrapper kills its owned group
and removes its temporary staging/profile files.

## Command reference

| Command | Arguments | Result / upstream |
| --- | --- | --- |
| `aider_version` | none | string `aider 0.86.2`; executes `aider --version` |
| `aider_setup_check` | none | booleans for installed/configured/home-blocked, pin and workspace; no secret/endpoint values |
| `aider` | required `prompt: string` (1–100000 chars); `cwd: string=""`; `files: string="[]"` containing a JSON list of at most 32 relative paths; `allow_write: boolean=false`; `command_timeout: integer=600` (1–1800) | dictionary with redacted stdout/stderr, exit code and selected changed paths |

Each file is at most 1 MiB. `cwd` must exist inside a git working tree. Existing
file symlinks, symlink parents, traversal, absolute paths, duplicates and `.git`,
`.env` or `.aider` paths are rejected. Missing selected names are new artifacts.
Non-selected staged output is discarded. Automatic confirmation is explicitly
disabled (`yes-always: false`), and the owned stdin feeder continually answers
`n` until process exit, so upstream refuses creation or editing of paths that
were not added to the selected stage. In this pinned version config false alone
leaves confirmation unset, and EOF would accept the default Yes. Detected concurrent source changes reject
writeback; this is not an isolation boundary against hostile concurrent writers.
Writes are atomic per file, preserve an existing file's permission bits and are
not an all-files transaction. Ask mode never copies staged edits back.

The upstream argv uses `--chat-mode ask|whole`, `--message-file`, the selected
paths, explicit model/base/settings, and disables commits, lint/test execution,
shell suggestions, URL detection, browser use, analytics and update checks.
A fixed text prefix keeps prompts beginning with `/` or `!` as model input,
preventing upstream slash/bang command dispatch. Prompts and API keys are not
placed in argv; the key is provided in child env.

## Configuration

| Name | Default / meaning |
| --- | --- |
| `AIDER_API_KEY` | empty; required compatible API credential |
| `AIDER_BASE_URL` | empty; required HTTP(S) endpoint, without embedded credentials/query/fragment |
| `AIDER_MODEL` | empty; required model ID, `openai/` prefix added for LiteLLM |
| `WORKSPACE` | `/home/user/app`; default working directory |
| `ABX_SERVER_TOKEN` | empty; optional server authentication |

**Prewarmed-server boundary:** `Sandbox.create(envs=...)` configures envd and
subsequent native processes; it does not retroactively configure the already
started port-9000 named-command server. Start an owned server from the installed
image commands on port 9010 with explicit `commands.start(env=...)`, consume its
stream, and address that port in CLI/SDK/HTTP. The examples preserve HOME and do
not replace image source. Destroying the owned sandbox stops both servers.

The compatible-model settings disable thinking with `extra_body.enable_thinking=false`.
This was chosen for the verified Qwen-compatible route; adjust and retest this
setting when extending another backend. Credentials are not written to stage
files. Model input still leaves the sandbox for your configured endpoint.

**Native-home limitation:** fixed upstream Aider and configargparse always search
native-home defaults before appending `--config` and `--env-file`; those flags
cannot promise complete isolation. The wrapper refuses existing native-home
`.aider.conf.yml`, `.env`, model-settings/metadata and OAuth-key files before launch.
It does not replace `HOME`, modify a shared profile or import project config.
`PYTHON_DOTENV_DISABLED=1` disables dotenv loading. Aider's own cache/install and
analytics-disabled state can remain in the dedicated sandbox's native `.aider`
until that sandbox is destroyed. Do not run real calls on a shared host home.

## Resources

2 vCPU, 2048 MiB, port 9000. A dependency-only metadata resolution found 108
compatible distributions / 118 MiB compressed Linux x86-64 wheels on Python 3.11;
this is not an installed-image size. The separate Python 3.12 archive adds about
32 MiB compressed on x86-64. Actual image acceptance is recorded separately.

## Verified

[Express supplemental image/runtime acceptance](evidence/image-runtime-2026-10-16-configured.json)
passed against the actual CI-built image: official READY, exact source/server
provenance, SDK/HTTP/CLI version and configured-target checks, actual CLI guards,
and qwen3.8-flash coding with 21 checks, independent tests and retrieved artifacts.
The configured model server runs on 9010; the prewarmed 9000 server is separate.
All owned helper/instances/template/registry resources were cleaned and read back.
The [earlier failed run](evidence/image-runtime-2026-10-16-attempt1.json) is retained.

[Hardened-controller image recheck](evidence/image-runtime-hardened-2026-10-16.json)
subsequently passed 21 genuine model checks with no failures or skips, using
controller `f76687e` against the same immutable image. Actual source compilation,
complete original-test execution and fresh completion acknowledgements now reject
early-exit and stale-cache false positives. Seven owned-resource cleanup checks
and a separate strict official template-absence readback passed. Earlier evidence
is preserved and predates this completion guard.

The catalog remains experimental with `tested_on: []`: the canonical
`scripts/express_e2e.py` → `abx template deploy` L2 wrapper has not passed.
Other providers remain unverified. See [design](../docs/design/aider.md).

## Secondary development

Edit `commands.py`, add a guarded named command, extend the API table and both
languages, and add positive/negative tests. Preserve the selected-file boundary,
process-group cleanup and original-file checks. Upgrade Python/Aider pins only
with official metadata, actual help/version and a new image/model run. Keep
upstream licenses in installed distributions and standalone Python archives.

## Contributing

See [repository contribution rules](../CONTRIBUTING.md). Run
`python3 scripts/check_template.py aider`, `python3 -m pytest aider -q`, and
`python3 scripts/run_local_e2e.py`.
Local keyless checks are L0 only; real coding requires `E2E_REQUIRE_LLM=1` on a
fresh dedicated sandbox and independent tests plus artifact retrieval. Do not
edit old evidence or commit keys/raw model logs.

## Issues

[Template issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
SDK/server issues belong in [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues);
CLI deployment issues in [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template glue is Apache-2.0. [Aider](https://github.com/Aider-AI/aider) is Apache-2.0;
its installed dependencies and [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
retain their respective notices. See [official installation](https://aider.chat/docs/install.html)
and [compatible API guidance](https://aider.chat/docs/llms/openai-compat.html).

Actual installed-CLI guard check (fresh dedicated sandbox only):

```bash
python3 aider/verify_upstream_guards.py
```

This uses a deterministic loopback model to verify slash/bang and unselected-path
refusals. It is separate from real-model coding and image deployment acceptance.

### Independent test completion

The coding controller verifies all three unchanged original tests in an isolated
Python process, compiles actual source bytes, rejects skipped/expected-failing or
incomplete tests, and requires fresh acknowledgements chosen after the agent
exits. Held-out calculations have a separate acknowledgement. Static marker output,
premature exit and cached bytecode do not establish a pass. These are completion
checks within the disposable sandbox, not an OS security boundary. Earlier real
model evidence is retained separately; the hardened verifier needs its own run.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
