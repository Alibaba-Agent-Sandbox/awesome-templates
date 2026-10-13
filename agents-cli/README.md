# agents-cli

Agents API for Codex and Qwen Code. The image does not preinstall either CLI.

## What it is

`commands.py` starts `agent-sandbox-server` with an endpoint policy. The
`agents` group is off by default; an exact endpoint rule turns on each route
the policy lists, and `ServerPolicy.only` closes everything else. The policy
exposes:

- `POST /v1/agents/sessions`
- `GET /v1/agents/sessions`
- `GET /v1/agents/sessions/{id}`
- `POST /v1/agents/sessions/{id}/events`
- `GET /v1/agents/sessions/{id}/items`
- `GET /v1/agents/runtimes`

Shell, file routes, and the rest of `/v1/agents/*` stay closed. A turn
looks up `codex` or `qwen` on `PATH` and writes the output into the session.
Other adapter names, including Claude Code, are HTTP 404. Each response
includes `X-Agent-Sandbox-Local: 1`.

Install only the CLI you call, in your own Dockerfile or inside a running
sandbox. Codex reads `OPENAI_API_KEY` or `CODEX_API_KEY`. Qwen Code reads
`OPENAI_API_KEY` and `OPENAI_BASE_URL`. Pass keys when the sandbox is
created; do not bake them into the image.

```bash
npm install -g @openai/codex
npm install -g @qwen-code/qwen-code
```

## Deploy

```bash
abx template install alibaba-agent-sandbox/awesome-templates//agents-cli
```

From this directory (build, push, and register):

```bash
abx deploy
```

## Local e2e

No model key. When `E2E_RUN_LLM=0`, `commands.py` prepends `e2e-bin/` to
`PATH`. Those scripts stand in for the CLIs.

From the repository root, with `agent-sandbox-server` installed:

```bash
python3 scripts/run_local_e2e.py
```

Or only this template, in two terminals:

```bash
E2E_RUN_LLM=0 ABX_SERVER_PORT=9000 python3 commands.py
E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py
```
