# Awesome Templates for Agent Sandbox

A curated collection of sandbox templates for the
[Agent Sandbox](https://pypi.org/project/agent-sandbox/) SDK and the `abx` CLI.
Each template is a self-contained sandbox: `template.yaml`, a `Dockerfile`
(`FROM python:3.12-slim`, `WORKDIR /app`, `CMD ["python3", "commands.py"]`),
`commands.py` (the in-sandbox `agent_sandbox.server` process), `e2e_test.py`,
and a README. Images install `agent-sandbox-server`.

The index in [`awesome-templates.yaml`](./awesome-templates.yaml) is the
catalog `abx template search` and `abx template install <name>` read.

## Templates

| Template | Description |
|----------|-------------|
| [python-hello](./python-hello/) | A minimal Python hello world template for testing |
| [browser-automation](./browser-automation/) | Browser automation sandbox with Playwright + Chromium for web scraping and UI testing |
| [claude-code](./claude-code/) | Claude Code Agent runtime — Anthropic Claude-powered AI coding assistant |
| [codex](./codex/) | OpenAI Codex CLI Agent runtime for AI-driven code generation and execution |
| [codex-agent-api](./codex-agent-api/) | Self-hosted OpenAI Agents API compatible service powered by Codex CLI |
| [qoder](./qoder/) | Qoder AI coding assistant runtime with Python and Node.js integrated dev sandbox |
| [agents-cli](./agents-cli/) | Agents API for Codex and Qwen Code. The image does not preinstall either CLI. |
| [qwen-code](./qwen-code/) | Qwen Code Agent runtime — Dashscope-powered AI autonomous deployment agent |
| [deepseek-harness](./deepseek-harness/) | DeepSeek Agent Runtime — DeepSeek model-driven AI coding agent |
| [hermes-agent](./hermes-agent/) | Hermes Agent runtime — NousResearch Hermes model-driven AI agent with tool calling |
| [node-web](./node-web/) | Node.js web service runtime for Express, Fastify and other frameworks |
| [openclaw](./openclaw/) | OpenClaw AI Agent runtime — open-source AI coding agent gateway |
| [opencode](./opencode/) | OpenCode agent (`opencode run`). Experimental until the image build and a keyed run are recorded. |
| [amp](./amp/) | Amp agent (`amp -x`). Experimental until the image build and a keyed run are recorded. |
| [droid](./droid/) | Factory Droid (`droid exec`). Experimental until the image build and a keyed run are recorded. |
OpenSandbox's public sandbox images (code-interpreter, code-interpreter-base, desktop, playwright, vscode) are resolved by the SDK. This catalog does not vendor those Dockerfiles.

`abx template install` builds the twelve Dockerfile templates on
`alicloud-express` only. The CLI does not load the other providers.
`base` and `code-interpreter-v1` are CLI builtins, so a bare install does
not use the directories in this repo. OpenSandbox create takes an image
URI and replaces the container entrypoint, so these Dockerfiles do not
start there until the image is pushed and the server is started by hand.

The static registry page is [registry/index.html](./registry/index.html).
It is the page intended for `registry.agent-sandbox.cn`; that DNS name is
not wired up here.

## Deploy

Install from this index (builds and registers the template):

```bash
abx template install python-hello
abx template install alibaba-agent-sandbox/awesome-templates//codex@v1.0.0
```

Publish the template in the current directory:

```bash
abx deploy
```

`abx template install ./<name> --registry-type local --download-only` only
fills the local cache (`~/.abx/templates/`) and does not build an image.
Search the index with `abx template search python` or
`abx template search ai-agent --status official`.

Top-level shortcuts are `create`, `list`, `info`, `kill`, `exec`, `connect`,
`upload`, `download`, `run`, and `deploy`. Scaffold and install a template
with `abx template init` and `abx template install`.

## Local end-to-end tests

One command, from this directory, with `agent-sandbox-server` and `httpx`
installed:

```bash
python3 scripts/run_local_e2e.py
```

It starts `python3 commands.py` for each of the 12 templates on an ephemeral
port, sets `E2E_BASE_URL`, runs that directory's `e2e_test.py`, and stops the
process. Every template must exit 0. The same script is
[`.github/workflows/e2e.yml`](./.github/workflows/e2e.yml).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). A template is one directory plus one
entry in `awesome-templates.yaml`. The bar for adding one is
[docs/acceptance.md](./docs/acceptance.md).

## License

MIT
