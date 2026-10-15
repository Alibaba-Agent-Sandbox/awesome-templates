# Awesome Templates for Agent Sandbox

A curated collection of sandbox templates for the
[Agent Sandbox](https://pypi.org/project/agent-sandbox/) SDK and the `abx` CLI.

How to build, list, and accept a template is
[docs/template-spec.md](./docs/template-spec.md)
([中文](./docs/template-spec.zh-CN.md)).
[`_skeleton/`](./_skeleton/README.md) is a directory that passes that spec.
It is not a catalog entry.

The index in [`awesome-templates.yaml`](./awesome-templates.yaml) is what
`abx template search` and `abx template install <name>` read.
**Verified on** lists a provider only when that template has a passing
evidence file under `<name>/evidence/`. An empty cell means no passing run
is recorded.

## Templates

| Template | Description | Status | Verified on |
|----------|-------------|--------|-------------|
| [python-hello](./python-hello/README.md) | A minimal Python hello world template for testing | official | alicloud-express |
| [browser-automation](./browser-automation/README.md) | Browser automation sandbox with Playwright + Chromium for web scraping and UI testing | official | |
| [claude-code](./claude-code/README.md) | Claude Code Agent runtime — Anthropic Claude-powered AI coding assistant | official | |
| [codex](./codex/README.md) | OpenAI Codex CLI Agent runtime for AI-driven code generation and execution | official | |
| [codex-agent-api](./codex-agent-api/README.md) | Self-hosted OpenAI Agents API compatible service powered by Codex CLI | official | |
| [qoder](./qoder/README.md) | Python and Node.js dev sandbox. qoder_run executes a local script; the Qoder CLI is not installed. | official | |
| [agents-cli](./agents-cli/README.md) | Agents API for Codex and Qwen Code. The image does not preinstall either CLI. | official | |
| [qwen-code](./qwen-code/README.md) | Qwen Code Agent runtime — Dashscope-powered AI autonomous deployment agent | official | |
| [deepseek-harness](./deepseek-harness/README.md) | DeepSeek Agent Runtime — DeepSeek model-driven AI coding agent | official | |
| [hermes-agent](./hermes-agent/README.md) | Chat completion against an OpenAI-compatible endpoint. This template does not register tools. | official | |
| [node-web](./node-web/README.md) | Node.js web service runtime for Express, Fastify and other frameworks | official | |
| [openclaw](./openclaw/README.md) | OpenClaw AI Agent runtime — open-source AI coding agent gateway | official | |
| [opencode](./opencode/README.md) | OpenCode coding agent. Headless opencode run and optional opencode serve. Package opencode-ai@1.19.0. | experimental | |
| [amp](./amp/README.md) | Sourcegraph Amp CLI. amp_execute runs amp -x; amp_version and amp_setup_check do not need a key. | official | alicloud-express |
| [droid](./droid/README.md) | Factory Droid. Command droid exec. Package @factory/cli@0.241.1. | experimental | |
| [gemini](./gemini/README.md) | Gemini CLI. Command gemini -p. Package @google/gemini-cli@0.64.0. | experimental | |
OpenSandbox's public sandbox images (code-interpreter, code-interpreter-base, desktop, playwright, vscode) are resolved by the SDK. This catalog does not vendor those Dockerfiles.

`abx template install` builds these Dockerfile templates on
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

From this directory, with `agent-sandbox-server`, `httpx`, and `pyyaml`
installed:

```bash
python3 scripts/check_template.py --all
python3 scripts/run_local_e2e.py
```

`run_local_e2e.py` starts `python3 commands.py` for every template directory
that has `commands.py` and `e2e_test.py`, on an ephemeral port, sets
`E2E_BASE_URL`, runs that directory's `e2e_test.py`, and stops the process.
It also runs the checker. Every template's e2e must exit 0. A
`spec_version: 2` template that fails the checker fails this script.
Directories that predate the spec are listed and do not fail it.
`E2E_RUN_LLM=0` makes the model call a SKIP. That skip is not acceptance of
the agent. The same script is
[`.github/workflows/e2e.yml`](./.github/workflows/e2e.yml).

Express (L2) is `python3 scripts/express_e2e.py <name>`. Credentials and
exit codes are in the spec. It deletes the sandbox and the template it
created.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). A template is one directory plus one
entry in `awesome-templates.yaml`. The bar for adding one is
[docs/template-spec.md](./docs/template-spec.md).

## License

Apache-2.0. See [LICENSE](./LICENSE).
