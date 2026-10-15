# opencode

## Purpose

People who want the OpenCode coding agent (`sst/opencode`, npm package `opencode-ai`) inside an Agent Sandbox. The sandbox installs the pinned CLI and exposes it as named commands. A caller sends one headless prompt, or starts OpenCode's own HTTP server and opens that port with `sb.network.get_url`.

## Capabilities

After the sandbox is READY the image has `opencode` 1.19.0 on `PATH`, git, and ripgrep. The platform process is `agent-sandbox-server` on port 9000.

The primary API is `opencode_run`: one `opencode run` invocation, JSON events, then a single JSON result. Parameters cover the prompt, `provider/model`, agent name, session continue (`--continue` or `--session`), and the working directory.

The secondary API is `opencode serve` on port 4096. It is not started by `start_cmd`. `opencode_serve_start` launches it, `opencode_serve_status` reports it, and `opencode_serve_stop` stops it. Clients that speak the OpenCode HTTP API use `sb.network.get_url(4096)`. `GET /global/health` on that port returns `{"healthy": true, "version": "1.19.0"}`.

`opencode_version` and `opencode_setup_check` do not call a model. `opencode` remains as a compatibility alias of `opencode_run` and returns the raw JSON-event stdout.

The interactive TUI is not started. Express has no separate TTY for the platform process, and a named command is one request and one JSON body.

## Exposed API

`opencode_run(prompt, model="", agent="", session="", continue_session=false, cwd="") -> {text, stdout, session_id, model, agent, cwd}`

Upstream argv, as a list, with stdin `/dev/null`:

```text
opencode run --pure --format json --auto --model <model> --dir <cwd> [--agent <agent>] [--session <id>] [--continue] <prompt>
```

`<model>` is the `model` argument, else `OPENCODE_MODEL`, else `dashscope/qwen3.8-flash`. `<cwd>` defaults to `/home/user/app` when that directory exists. `--auto` approves permissions the agent has not explicitly denied. `--pure` skips external plugins. A non-zero exit raises `RuntimeError`. The child `OPENCODE_CONFIG` points at the image `opencode.json`, or at a temp copy when the requested DashScope model id is not already listed.

`opencode(prompt, model="", agent="", session="", continue_session=false, cwd="") -> stdout string`

Same argv as `opencode_run`. Kept so callers of the previous `opencode` command still receive the CLI stdout. New callers should use `opencode_run`.

`opencode_version() -> "1.19.0"`

Argv: `opencode --version`.

`opencode_setup_check() -> "ok"`

Argv: `opencode --version`, then a read of `opencode.json`. Checks the pinned version and that provider `dashscope` uses `@ai-sdk/openai-compatible` with `{env:ABX_LLM_BASE_URL}` and `{env:ABX_LLM_API_KEY}`. No network call.

`opencode_serve_start(port=4096, hostname="0.0.0.0") -> {running, port, hostname, pid, healthy}`

Argv: `opencode serve --pure --hostname <hostname> --port <port>`. Waits until `GET /global/health` on `127.0.0.1` reports `healthy: true`. The bind address is `0.0.0.0` so the sandbox port proxy can reach it. A second start on the same port returns the current status.

`opencode_serve_status() -> {running, port, hostname, pid, healthy}`

No upstream process is spawned. Reads the pid file and probes `/global/health`.

`opencode_serve_stop() -> "stopped"`

Sends `SIGTERM` to the serve process group. Idempotent.

## How to build

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

`ABX_LLM_API_KEY`, `OPENCODE_API_KEY`, `ABX_SERVER_TOKEN`, and `OPENCODE_SERVER_PASSWORD` are declared empty and injected at create. The image and `opencode.json` store `{env:...}` placeholders, not values. Exception text strips values of environment variables whose names contain `KEY`, `SECRET`, `TOKEN`, or `PASSWORD`.

`opencode_run` passes `--auto`, so tool permissions that the agent has not explicitly denied are approved. That is required for a non-interactive run and is the dangerous flag upstream documents.

`opencode serve` logs a warning when `OPENCODE_SERVER_PASSWORD` is unset. The sandbox gateway still fronts the port. Set the password when the OpenCode HTTP API should require basic auth (`OPENCODE_SERVER_USERNAME` defaults to `opencode` in the CLI).

The CLI is pinned and `OPENCODE_DISABLE_AUTOUPDATE=true`, so a running sandbox does not download a newer binary. Model ids in `opencode.json` are the ones this endpoint answered with (`qwen3.8-flash`, `qwen3.8-max`). Another endpoint needs `model` set to an id that endpoint serves. OpenCode Zen (`opencode/big-pickle`, `OPENCODE_API_KEY`) is not the default; pass `model` to use it.

The template does not start the TUI, does not run `opencode upgrade`, and does not write credentials into the image.

## Test plan

L0: `python3 scripts/run_local_e2e.py`. `e2e_test.py` checks `GET /health`, the command list (including parameter names on `opencode_run`), and HTTP 400 for `POST /commands/opencode_run` without `prompt`. When `opencode` is on `PATH`, it also expects `opencode_version` `1.19.0`, `opencode_setup_check` `ok`, and a serve start on 127.0.0.1 with `/global/health`. `E2E_RUN_LLM=0` skips the model call. CI does not install the CLI; those cases SKIP and the process still exits 0.

L1: `docker build` with the Alibaba base image. The log shows `opencode-ai@1.19.0` and `opencode --version` printing `1.19.0`.

L2: `python3 scripts/express_e2e.py opencode` on `alicloud-express`. Smoke is `opencode_version` expecting `1.19.0` and `opencode_setup_check` expecting `ok`, through `abx run` and `Sandbox.run`. No model key.

L3: create one sandbox with `ABX_LLM_API_KEY` and `ABX_LLM_BASE_URL`, call `opencode_run` with a prompt that asks for `ABX_E2E_OK`, assert the marker in the result, then delete the sandbox. The key in this environment is the OpenAI-compatible DashScope endpoint already used for the local probe. An empty key is a failure when `E2E_REQUIRE_LLM=1`.

L4: not planned. No other provider is in this run.
