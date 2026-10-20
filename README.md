# Awesome Templates for Agent Sandbox

A curated collection of sandbox templates for the
[Agent Sandbox](https://github.com/Alibaba-Agent-Sandbox/python-sdk) SDK and the `abx` CLI.

How to build, list, and accept a template is
[docs/template-spec.md](./docs/template-spec.md)
([中文](./docs/template-spec.zh-CN.md)).
[`_skeleton/`](./_skeleton/README.md) is a directory that passes that spec.
It is not a catalog entry.

Repository maintenance follows the [project standards and definition of done](docs/project-standards.md)
([中文](docs/project-standards.zh-CN.md)) and [documentation standard](docs/documentation-standards.md)
([中文](docs/documentation-standards.zh-CN.md)). Contribution instructions are
[English](CONTRIBUTING.md) / [中文](CONTRIBUTING.zh-CN.md).

The index in [`awesome-templates.yaml`](./awesome-templates.yaml) is what
`abx template search` and `abx template install <name>` read.
**Verified on** lists a provider only when that template has a passing
evidence file under `<name>/evidence/`. An empty cell means no passing run
is recorded.

## Templates

2026-10-20 Express platform-step checkpoint: **34/34 step and required full HTTP PASS** with real READY, CLI/SDK smoke and independent cleanup. [Auditable per-template matrix](.agents/evidence/verify/2026-10-20-complete-platform-steps-matrix.json) · [operations and scope](docs/platform-steps.md) ([中文](docs/platform-steps.zh-CN.md)). Model and image acceptance remain separate.

The [2026-10-18 acceptance review](docs/verification-2026-10-18.md) ([中文](docs/verification-2026-10-18.zh-CN.md)) records the historical23-template checkpoint and its unresolved gates. Current scoped receipts are linked below.

| Template | Description | Status | Verified on |
|----------|-------------|--------|-------------|
| [python-hello](./python-hello/README.md) | A minimal Python hello world template for testing | experimental | [alicloud-express (1.1.1 full HTTP)](./python-hello/evidence/express-2026-10-19T183219Z.json) |
| [browser-use](./browser-use/README.md) | Native text-DOM browser agent with private Chromium | experimental | [alicloud-express (1.0.0 SDK image, real model)](./browser-use/evidence/express-2026-10-20.json) |
| [browser-automation](./browser-automation/README.md) | Browser automation sandbox with Playwright + Chromium for web scraping and UI testing | experimental | [alicloud-express (SDK steps, PDF and HTTP37)](./browser-automation/evidence/express-2026-10-20T103410Z.json) |
| [claude-code](./claude-code/README.md) | Claude Code Agent runtime — Anthropic Claude-powered AI coding assistant | experimental | [alicloud-express (1.1.1 steps smoke)](./claude-code/evidence/express-2026-10-19T183255Z.json) |
| [copilot-cli](./copilot-cli/README.md) | Native GitHub Copilot CLI1.0.100, explicit BYOK and bounded file-edit profile | experimental | [alicloud-express1.0 SDK steps/model17](./copilot-cli/evidence/express-2026-10-20T165141Z.json) |
| [codex](./codex/README.md) | OpenAI Codex CLI (@openai/codex@0.162.1). codex exec, JSON events, sandbox bypass, OpenAI-compatible config.toml. | experimental | [alicloud-express (2.0.0 SDK image, strict model17)](./codex/evidence/express-2026-10-20.json) |
| [codex-agent-api](./codex-agent-api/README.md) | Codex 0.162.1 HTTP session adapter with bounded turns and SSE; project API subset | experimental | [alicloud-express (steps smoke)](./codex-agent-api/evidence/express-2026-10-19.json) |
| [qoder](./qoder/README.md) | Qoder coding CLI @qoder-ai/qodercli@1.1.72 with version, read-only setup and bounded headless execution. | experimental | [alicloud-express (1.1.1 steps smoke)](./qoder/evidence/express-2026-10-19T184147Z.json) |
| [agents-cli](./agents-cli/README.md) | Restricted local Agents HTTP API with pinned Codex 0.162.1 and Qwen Code 0.23.0. | experimental | [alicloud-express (2.0.1 steps smoke)](./agents-cli/evidence/express-2026-10-19T183102Z.json) |
| [qwen-code](./qwen-code/README.md) | Qwen Code Agent runtime — Dashscope-powered AI autonomous deployment agent | experimental | [alicloud-express (2.1.1 image, SDK create, model17)](./qwen-code/evidence/express-2026-10-20.json) |
| [deepseek-harness](./deepseek-harness/README.md) | Bounded DeepSeek-compatible coding agent with read, write, list and shell tools. | experimental | [alicloud-express (1.1.1 image, SDK create, model17)](./deepseek-harness/evidence/express-2026-10-20.json) |
| [kimi-code](./kimi-code/README.md) | Official Kimi Code 2.2.0 with private headless turns and explicit tool permission. | experimental | [alicloud-express (steps + model)](./kimi-code/evidence/express-2026-10-19.json) |
| [hermes-agent](./hermes-agent/README.md) | NousResearch Hermes 0.22.1 with pinned upstream runtime, local file/terminal tools and bounded headless execution. | experimental | [alicloud-express (1.1.1 image, strict model)](./hermes-agent/evidence/express-2026-10-20.json) |
| [node-web](./node-web/README.md) | Node.js web service runtime for Express, Fastify and other frameworks | experimental | [alicloud-express (1.1.1 full HTTP)](./node-web/evidence/express-2026-10-19T183324Z.json) |
| [openclaw](./openclaw/README.md) | OpenClaw 2026.10.4 gateway with authenticated health, owned process lifecycle and Node.js 24.16.0. | experimental | [alicloud-express (2.1 SDK image/steps + authenticated full HTTP)](./openclaw/evidence/express-2026-10-20T165241Z.json) |
| [opencode](./opencode/README.md) | OpenCode coding agent. Headless opencode run and optional opencode serve. Package opencode-ai@1.19.0. | experimental | [alicloud-express (2.0.2 steps, full HTTP15)](./opencode/evidence/express-2026-10-20T160725Z.json) |
| [amp](./amp/README.md) | Sourcegraph Amp CLI. amp_execute runs amp -x; amp_version and amp_setup_check do not need a key. | experimental | [alicloud-express (steps smoke)](./amp/evidence/express-2026-10-19.json) |
| [droid](./droid/README.md) | Factory Droid. Command droid exec. Package @factory/cli@0.241.1. | experimental | [alicloud-express (1.1.1 steps smoke)](./droid/evidence/express-2026-10-19T183451Z.json) |
| [gemini](./gemini/README.md) | Gemini CLI. Command gemini -p. Package @google/gemini-cli@0.64.0. | experimental | [alicloud-express (2.0.1 steps smoke)](./gemini/evidence/express-2026-10-19T183608Z.json) |
| [osworld](./osworld/README.md) | OSWorld Linux browser slice with real X11 input, screenshots, AT-SPI and selected task evaluators. | experimental |[alicloud-express1.0 SDK steps/desktop18](./osworld/evidence/express-2026-10-20T170423Z.json) |
| [pi](./pi/README.md) | Official Pi CLI 1.3.0 with ephemeral compatible-model settings and explicit writable tools. | experimental | [alicloud-express (1.0.1 image, strict model)](./pi/evidence/express-2026-10-20.json) |
| [ocr](./ocr/README.md) | CPU English image OCR with pinned Tesseract 5.5.0 and bounded private TXT/TSV artifacts. | experimental | [alicloud-express (1.0.1 image, full HTTP19)](./ocr/evidence/express-2026-10-20.json) |
| [document-tools](./document-tools/README.md) | Markdown/HTML, DOCX, TXT, PPTX and headless Writer PDF. | experimental | [alicloud-express (1.1 SDK image/steps, full HTTP36)](./document-tools/evidence/express-2026-10-20.json) |
| [media-tools](./media-tools/README.md) | Bounded CPU FFmpeg presets and native JSON argv. | experimental |[alicloud-express1.1image/steps](./media-tools/evidence/express-2026-10-20T133417Z.json) |
| [aider](./aider/README.md) | Official Aider 0.86.2 with read-only ask and explicit selected-file edits. | experimental | [alicloud-express (1.0.1 image, strict model)](./aider/evidence/express-2026-10-20.json) |
| [swe](./swe/README.md) | Real mini-swe-agent 2.4.6 and one independently evaluated SWE-bench instance; no official Docker score. | experimental | [alicloud-express (1.1.0 SDK image, strict model14)](./swe/evidence/express-2026-10-20.json) |

OpenSandbox's public sandbox images (code-interpreter, code-interpreter-base, desktop, playwright, vscode) are resolved by the SDK. This catalog does not vendor those Dockerfiles.

`abx template install` builds these Dockerfile templates on
`alicloud-express` only through its built-in Dockerfile deployment workflow.
The CLI also loads installed provider plugins; template operations require the
plugin's declared template capability. A provider that accepts an existing
template ID does not thereby support building this catalog's Dockerfiles.
`base` and `code-interpreter-v1` are CLI builtins, so a bare install does
not use the directories in this repo. OpenSandbox create takes an image
URI and replaces the container entrypoint, so these Dockerfiles do not
start there until the image is pushed and the server is started by hand.

Catalog provider values are preparation prerequisites, not verification. See
[provider-owned source preparation](docs/provider-preparation.md) ([中文](docs/provider-preparation.zh-CN.md));
missing capabilities remain unsupported and provider IDs never convert across clouds.

The maintained registry website and ingestion code live in the separate
[registry repository](https://github.com/Alibaba-Agent-Sandbox/registry).
The public site is [registry.agent-sandbox.cn](https://registry.agent-sandbox.cn).
This repository owns `awesome-templates.yaml` and template docs, which that
registry ingests. The unused local `registry/index.html`/`catalog.json` copy has
been retired; consumers should use the maintained registry's public catalog.

For installation prerequisites, all three calling interfaces, evidence levels
and provider limits, start with [Using templates](docs/using-templates.md)
([中文](docs/using-templates.zh-CN.md)). Each template README contains its own
CLI, Python SDK and HTTP POST examples plus command/authentication/error details.

## Deploy

Install the CLI and paired Python packages using the [source-aware setup guide](docs/using-templates.md#installation), then configure the selected provider.

Install from this index (builds and registers the template):

```bash
abx template install python-hello
abx template install alibaba-agent-sandbox/awesome-templates//codex@052051411a5f78743083d68467ba952a4e71e08b
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

## Automatic preparation on another provider

Use a CLI build that includes `template launch` and configure the selected provider once. The adapter builds or registers the source and passes its returned ID, name or image directly to sandbox creation:

```sh
abx --provider e2b template launch alibaba-agent-sandbox/awesome-templates//python-hello --yes
```

Third-party providers remain Beta. `provider-prepared` is a workflow hint, not a native verification receipt. Required runtime capabilities are checked before building; a missing PTY/code feature is not repaired by converting a reference. Native base images, registry access and cluster requirements belong to each provider. See the [provider preparation guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/template-launch.md). Existing provider/template evidence remains authoritative; no Verified-on claim changes here.

## 在其他提供方上自动准备

使用包含 `template launch` 的 CLI，并完成一次提供方配置。适配器构建或登记本目录，把返回的 ID、名称或镜像直接传给沙箱创建，无需手动查找 ID：

```sh
abx --provider e2b template launch alibaba-agent-sandbox/awesome-templates//python-hello --yes
```

第三方提供方继续为 Beta。`provider-prepared` 是流程提示，不是原生验收记录。构建前会检查运行时能力，引用转换不会补齐 PTY 或代码执行能力。原生基础镜像、镜像仓库和集群条件由各提供方维护。见[自动准备指南](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/template-launch.md)。已有验收证据仍为准，本次不修改 Verified-on 声明。

[Next.js/Vite preview template](next-app/README.md) · experimental; [alicloud-express1.1.0 SDK image and independent forwarded HTTP](next-app/evidence/express-2026-10-20.json).
Browser IDE: [code-server](code-server/README.md) (experimental; [alicloud-express1.0.0 SDK image and sdk-local browser](code-server/evidence/express-2026-10-20.json)).
Pinned Go/Rust/Java runtime: [polyglot-toolchain](polyglot-toolchain/README.md) (experimental; verification gates recorded separately).
Model-free file tool: [apply-patch](apply-patch/README.md) (experimental).

Native local DeepAgents: [deepagents](deepagents/README.md) (experimental; [alicloud-express1.0.0 SDK image and model17](deepagents/evidence/express-2026-10-20.json)).

Official terminal agent: [goose](goose/README.md) (experimental; [alicloud-express1.0.0 SDK image + model17](goose/evidence/express-2026-10-20.json)).

## Provider-managed runtime catalog

| ID | Provider | Documentation | Verified scope |
| --- | --- | --- | --- |
| base | alicloud-express | [English](docs/managed/base/README.md) · [中文](docs/managed/base/README.zh-CN.md) | shell, files, SDK shell-fallback code, CLI exec; owned cleanup |
| code-interpreter-v1 | alicloud-express | [English](docs/managed/code-interpreter-v1/README.md) · [中文](docs/managed/code-interpreter-v1/README.zh-CN.md) | shell, files, SDK shell-fallback code, CLI exec; owned cleanup |

These provider-managed IDs are listed separately from buildable source templates.
Native interpreter service was HTTP404 in both recorded tests; no native interpreter
or other-provider certification is claimed.

Official native Crush: [crush](crush/README.md) (experimental; [alicloud-express1.0.0 SDK image and model17](crush/evidence/express-2026-10-20.json)).
[Development database template](dev-services/README.md) · experimental; [alicloud-express1.1.0 SDK image and HTTP6](dev-services/evidence/express-2026-10-20.json).
