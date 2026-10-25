# Aider

## What it does

Runs the official `aider-chat==0.86.2` CLI against an explicitly selected git
working tree. The default is read-only **ask** mode. `allow_write=true` permits
whole-file edits to explicitly listed source/artifact paths. The wrapper stages
only those files, runs Aider, checks the original files have not changed, then
copies back selected results. It never auto-commits.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

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

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./aider --yes
abx run <sandbox-id> aider_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('aider_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/aider_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "aider 0.86.2"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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
| `ABX_SERVER_TOKEN` | Export an independent application token before the application workflow launch; separate from model and gateway credentials |

Export `AIDER_API_KEY`, `AIDER_BASE_URL`, `AIDER_MODEL` and the independent application token before `template launch`. This path starts the named server for the instance; no second port-9010 server is needed. Changing the host environment does not reconfigure an existing application; launch a new instance after changing configuration.

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

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical verification

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

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py aider` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

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

### Additional current-version platform-step acceptance

[Actual steps](evidence/express-2026-10-20T135354Z.json) and [external HTTP attempt](evidence/verification-steps-2026-10-20T135354Z.json): official READY, Python SDK creation, CLI/SDK smoke and 9 HTTP PASS / 0 FAIL / 1 SKIP. Model calls remain NOT_RUN in this receipt. Independent sandbox/template and private same-account asset-cache object/bucket cleanup passed before publication. Earlier image/model receipts retain their own scope.
