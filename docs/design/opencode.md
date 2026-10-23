# opencode

## Purpose

People who want the OpenCode coding agent (`sst/opencode`, npm package `opencode-ai`) inside an Agent Sandbox. The sandbox installs the pinned CLI and exposes it as named commands. A caller sends one headless prompt, or starts OpenCode's own HTTP server and opens that port with `sb.network.get_url`.

## Capabilities

After the sandbox is READY the image has `opencode` 1.19.0 on `PATH`, git, and ripgrep. The platform process is `agent-sandbox-server` on port 9000.

The primary API is `opencode_run`: one `opencode run` invocation, JSON events, then a single JSON result. Parameters cover the prompt, `provider/model`, agent name, session continue (`--continue` or `--session`), and the working directory.

The secondary API is `opencode serve` on port 4096. It is not started by `start_cmd`. `opencode_serve_start` launches it, `opencode_serve_status` reports it, and `opencode_serve_stop` stops it. Clients that speak the OpenCode HTTP API use `sb.network.get_url(4096)`. `GET /global/health` on that port returns `{"healthy": true, "version": "1.19.0"}`.

`opencode_version` and `opencode_setup_check` do not call a model. `opencode` remains as a compatibility alias of `opencode_run` and returns sanitized JSON-event stdout.

The interactive TUI is not started. Express has no separate TTY for the platform process, and a named command is one request and one JSON body.

## Exposed API

`opencode_run(prompt, model="", agent="", session="", continue_session=false, cwd="") -> {text, stdout, session_id, model, agent, cwd}`

Upstream argv, as a list, with stdin `/dev/null`:

```text
opencode run --pure --format json --auto --model <model> --dir <cwd> [--agent <agent>] [--session <id>] [--continue] -- <prompt>
```

`<model>` is the `model` argument, else `OPENCODE_MODEL`, else `dashscope/qwen3.8-flash`. `<cwd>` defaults to the module directory (`/home/user/app` inside the image). `--auto` approves permissions the agent has not explicitly denied. `--pure` skips external plugins. A non-zero exit raises `RuntimeError` with the exit code; subprocess stdout/stderr are omitted so prompts and tool arguments cannot leak through errors. Success JSON events redact secret environment values, including JSON-escaped strings. The child `OPENCODE_CONFIG` points at the image `opencode.json`, or at a temp copy when the requested DashScope model id is not already listed.

`opencode(prompt, model="", agent="", session="", continue_session=false, cwd="") -> stdout string`

Same argv as `opencode_run`. Kept so callers of the previous `opencode` command still receive the CLI stdout. New callers should use `opencode_run`.

`opencode_version() -> "1.19.0"`

Argv: `opencode --version`.

`opencode_setup_check() -> "ok"`

Argv: `opencode --version`, then a read of `opencode.json`. Checks the pinned version and that provider `dashscope` uses `@ai-sdk/openai-compatible` with `{env:ABX_LLM_BASE_URL}` and `{env:ABX_LLM_API_KEY}`. No network call.

`opencode_serve_start(port=4096, hostname="0.0.0.0") -> {running, port, hostname, pid, healthy}`

Argv: `opencode serve --pure --hostname <hostname> --port <port>`. Waits until `GET /global/health` on `127.0.0.1` reports `healthy: true`. The bind address is `0.0.0.0` so the sandbox port proxy can reach it. A second start with the same port and hostname returns the current status. All lifecycle operations hold one process-local RLock. Only a Popen child owned by this interpreter authorizes signaling, with its process-group identity checked before each signal. PID/state files are never read or written. Stop waits for and reaps its child. Restarting the command server does not adopt an older serve process; recycle the sandbox to clean up such a process.

`opencode_serve_status() -> {running, port, hostname, pid, healthy}`

No upstream process is spawned. Checks the interpreter-owned Popen child and probes its `/global/health` under the same lifecycle lock.

`opencode_serve_stop() -> "stopped"`

Sends `SIGTERM` only to the live process group of the interpreter-owned Popen child; mismatched ownership or group identity refuses signals. Waits for child exit (SIGKILL only after its timeout), then reaps the child. Idempotent. A stale PID file cannot authorize any signal.

## How to build

Template2.0.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` (the platform image already has Python 3.13 and Node.js 20). `npm view opencode-ai version` on 2026-10-15 still resolved `latest` to `1.19.0`; the Dockerfile installs `opencode-ai@1.19.0` and runs `opencode --version`.

`agent-sandbox-server` comes from a wheel injected by `abx template deploy` when one is in the build context. Otherwise the Dockerfile installs python-sdk main `61c43e0be65a1f57aa09186d578e7b399e48429b` (the commit on `main` that includes PR #21) with:

```text
pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/61c43e0be65a1f57aa09186d578e7b399e48429b.tar.gz#subdirectory=server-sdk"
```

The PyPI pin `agent-sandbox-server==0.3.0` is recorded in the Dockerfile comment and is not what the image runs. That release predates the Express server fixes.

`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`

`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`

No `CMD` or `ENTRYPOINT`. Runtime user `user`. Work directory `/home/user/app`. The context file `opencode.json` is copied there.

Provider config (V1 schema, verified with `opencode-ai@1.19.0` against an OpenAI-compatible DashScope URL):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "dashscope/qwen3.8-flash",
  "provider": {
    "dashscope": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "DashScope",
      "options": {
        "baseURL": "{env:ABX_LLM_BASE_URL}",
        "apiKey": "{env:ABX_LLM_API_KEY}"
      },
      "models": {
        "qwen3.8-flash": {"name": "Qwen3.8 Flash"},
        "qwen3.8-max": {"name": "Qwen3.8 Max"}
      }
    }
  }
}
```

`{env:NAME}` is the substitution OpenCode documents for 1.x config. A local `opencode run --format json --model dashscope/qwen3.8-flash` against `ABX_LLM_BASE_URL` returned a `text` event containing `ABX_E2E_OK`.

## Express feasibility

Feasible: yes

Limiting factor: none

Express (non-root `user`, 2 vCPU, no KVM, no Docker, no extra capabilities, about 10G rootfs, egress allowed) can run this CLI. The binary is a standalone ELF from the npm postinstall; it does not need Docker or KVM. Egress is required for a real model call and for `npm install` at image build. Memory is 2048 MB, which covers the CLI plus one headless run. The serve process is an extra Node-free native binary on port 4096 and fits the same limit.

## Risks

`ABX_LLM_API_KEY`, `OPENCODE_API_KEY`, `ABX_SERVER_TOKEN`, and `OPENCODE_SERVER_PASSWORD` are declared empty and injected at create. The image and `opencode.json` store `{env:...}` placeholders, not values. Successful JSON event output redacts values of environment variables whose names contain `KEY`, `SECRET`, `TOKEN`, `PASSWORD`, or `CREDENTIAL`. CLI failure output is omitted entirely. Serve stdout/stderr are discarded instead of storing a raw log. Health probes support the configured basic-auth password without returning it.

`opencode_run` passes `--auto`, so tool permissions that the agent has not explicitly denied are approved. That is required for a non-interactive run and is the dangerous flag upstream documents.

`opencode serve` logs a warning when `OPENCODE_SERVER_PASSWORD` is unset. The sandbox gateway still fronts the port. Set the password when the OpenCode HTTP API should require basic auth (`OPENCODE_SERVER_USERNAME` defaults to `opencode` in the CLI).

The CLI is pinned and `OPENCODE_DISABLE_AUTOUPDATE=true`, so a running sandbox does not download a newer binary. Model ids in `opencode.json` are the ones this endpoint answered with (`qwen3.8-flash`, `qwen3.8-max`). Another endpoint needs `model` set to an id that endpoint serves. OpenCode Zen (`opencode/big-pickle`, `OPENCODE_API_KEY`) is not the default; pass `model` to use it.

The template does not start the TUI, does not run `opencode upgrade`, and does not write credentials into the image.

## Test plan

L0: run `python3 opencode/e2e_test.py` against `E2E_BASE_URL`, or use the repository local runner. Install the pinned CLI on the server first. CLI absence or a different version fails; no check consults the tester's own PATH or keys. The tests check registration, HTTP argument errors, actual target Python execution through `/shell`, download and cleanup of its file through `/files/download-stream`, pinned version/config, and serve start/status/idempotence/stop. Serve health is checked inside the target, including version and basic auth; the tester never probes its own localhost for a remote service. The optional public port proxy remains a separate L2 check. The latest local run uses isolated `opencode-ai@1.19.0`; a synthetic serve password verifies the authenticated health probe. `opencode/test_commands.py` protects positional prompt handling, secret redaction (including short and JSON-escaped values), error/timeout traceback omission, session validation, read-only setup, stale PID safety, interpreter ownership, and concurrent start serialization. Setup reads configuration and runs `--version`; it never starts serve or writes a config.

`E2E_RUN_LLM=0` explicitly prints L3 NOT RUN. L0 success establishes the local HTTP/CLI lifecycle only and cannot establish that a model works. L3 requires both `E2E_RUN_LLM=1` and `E2E_REQUIRE_LLM=1`. The test does not inspect the tester's model key: a remote server may already have its own injected key. L3 seeds a broken existing calc.py and fixed test_calc.py through the remote files API, then reproduces the failing tests before calling the agent. The agent must repair calc.py without changing tests, run the tests, and create report.txt plus an exact acceptance.txt artifact. The harness downloads all four files, verifies the existing source changed and fixed tests stayed byte-identical, reruns all three tests through /shell with the project cwd, and executes additional held-out assertions. It deletes only its unique owned project directory. A response marker or a newly written file alone cannot pass this acceptance. After those checks pass, a second `opencode_run` receives exactly the first returned `session_id` through `session`; it never uses global `continue_session`. Before the call, `resume.json` must be absent. The resumed agent reads the existing report and source, computes the report SHA-256 from its actual bytes, calls the repaired `add` for additional ordered input pairs, and creates `resume.json`. The controller independently computes the expected digest/results without putting them in the prompt, checks the returned session id, downloads and validates the new artifact, requires the original source/tests/report/acceptance bytes to remain unchanged, and reruns held-out assertions. Wrong sessions, missing or incorrect artifacts, and original-file mutations fail. `test_e2e_protocol.py` uses a fake remote model and real subprocesses to protect the success branch and reject marker-only output, tampered tests, wrong resume sessions, incorrect hashes/results, missing resume artifacts, and resume-time source/report/test mutations; it is regression coverage, not real model/provider evidence. Response bodies and prompts are never dumped into the test log. External target HTTP clients respect the environment proxy configuration. Only the sandbox-internal loopback serve health probe uses a dedicated direct connection, so it checks its own local process rather than an external proxy.

L1: `docker build` with the Alibaba base image. Not run in the restored environment because Docker is unavailable.

L2: `python3 scripts/express_e2e.py opencode` on `alicloud-express`. The smoke commands run through the actual provider API and SDK. No provider pass or `tested_on` entry is claimed until that run succeeds and is recorded. A serve port proxy probe uses the provider URL for port 4096, rather than the tester's localhost.

L3: the real agent/file and exact-session continuation acceptance above with provider-injected model configuration. Local credential-free checks never establish this result. The 2026-10-16 Express source-runtime run recorded 28 HTTP checks passing with a real `dashscope/qwen3.8-flash` model, including the coding turn, exact-session continuation, independent artifact/hash/calculation checks and owned-project cleanup. A separate repeat rebuilt the server wheel from clean SDK source (`bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea`), verified all 56 packaged Python modules against that git archive, and passed the same 28 checks. Each owning sandbox was killed in `finally`. Source-runtime checks use uploaded commands/configuration and separately installed dependencies on an existing base template. They do not verify this Dockerfile or deployment of a newly built template image; keep `tested_on` empty until the image L1/L2 gates pass.

L4: no other provider has been accepted. All provider evidence remains empty.


## Independent verifier completion

The legacy held-out process accepted a static marker with exit zero even when
source exited before assertions. A real local subprocess reproduction confirmed
this gap. Three separate post-agent processes now use isolated Python with trusted
stdlib loaded before the project, direct compilation of actual source bytes and
fresh controller-generated completion acknowledgements. Original tests must run
exactly three cases with no skipped/expected failures; both held-out phases also
check the original cases, continuation cases and an additional decimal pair.
The agent API, exact-session flow and runtime files are unchanged. Same-user
hostile-code containment is not claimed. Historical genuine model results remain
history and do not establish this new gate. Actual hardened-image/model recheck,
canonical deployment, parents and final remote checks remain pending.

Release readiness 2.0.3: align default and injected server SDK source to `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; preserve historical receipts and require new image/workflow acceptance.
