# Awesome Templates for Agent Sandbox

Reusable sandbox templates for the [Agent Sandbox](https://github.com/Alibaba-Agent-Sandbox/python-sdk) SDK and `abx` CLI.

Choose a template below, configure its provider and application credentials, then launch it. Start with [Using templates](docs/using-templates.md) ([中文](docs/using-templates.zh-CN.md)); each template includes CLI, Python SDK and HTTP examples.

选择下方模板，配置对应提供方和应用凭据后启动。[模板使用指南](docs/using-templates.zh-CN.md)介绍安装与配置，各模板提供 CLI、Python SDK 和 HTTP 示例。

## Launch a template / 启动模板

Install the CLI and configure the provider using the [setup guide](docs/using-templates.md#installation). Run:

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello
```

Interactive launch asks for missing configuration before building or creating a sandbox. `ABX_SERVER_TOKEN` protects the application API; choose your own private token, or select **Save for future commands** and press Enter to generate one. It is separate from your Sandbox API key and does not come from a cloud console. Later application calls use the same token.

交互启动会在构建和创建沙箱前引导补齐配置。`ABX_SERVER_TOKEN` 用于保护应用 API，可以自行设置私有令牌，也可以选择 **Save for future commands** 后按回车生成。它与 Sandbox API Key 分开，无需去云控制台申请；后续调用应用时使用同一令牌。

Source templates require the selected provider's build prerequisites. For another provider, install and configure it first, then change `--provider`. For automation, configure all required values before adding `--yes`. See [provider setup](docs/provider-preparation.md) ([中文](docs/provider-preparation.zh-CN.md)).

源码模板需要对应提供方的构建环境。使用其他提供方时，先安装和配置，再修改 `--provider`。自动化运行须预先配置所需值，再添加 `--yes`。

Search with `abx template search python`. To download an editable copy without creating cloud resources:

```bash
abx template install python-hello --download-only --dir ./python-hello
```

## Templates

| Template | Description | Status |
| --- | --- | --- |
| [python-hello](./python-hello/README.md) | A minimal Python hello world template for testing | experimental |
| [browser-use](./browser-use/README.md) | Native browser-use0.13.11 with private local pinned Chromium and explicit model. | experimental |
| [browser-automation](./browser-automation/README.md) | Browser automation sandbox with Playwright + Chromium for web scraping and UI testing | experimental |
| [claude-code](./claude-code/README.md) | Claude Code Agent runtime — Anthropic Claude-powered AI coding assistant | experimental |
| [copilot-cli](./copilot-cli/README.md) | Pinned native GitHub Copilot CLI1.0.100 with explicit OpenAI-compatible BYOK and owned process lifecycle. | experimental |
| [codex](./codex/README.md) | OpenAI Codex CLI (@openai/codex@0.162.1). codex exec, JSON events, sandbox bypass, OpenAI-compatible config.toml. | experimental |
| [codex-agent-api](./codex-agent-api/README.md) | Codex 0.162.1 HTTP session adapter with bounded turns and SSE; project API subset, not full OpenAI API compatibility. | experimental |
| [qoder](./qoder/README.md) | Qoder coding CLI @qoder-ai/qodercli@1.1.72 with version, read-only setup and bounded headless execution. | experimental |
| [agents-cli](./agents-cli/README.md) | Restricted local Agents HTTP API with pinned Codex 0.162.1 and Qwen Code 0.23.0. | experimental |
| [qwen-code](./qwen-code/README.md) | Qwen Code Agent runtime — Dashscope-powered AI autonomous deployment agent | experimental |
| [deepagents](./deepagents/README.md) | Native DeepAgents0.7.25 local file/shell compatible-provider runtime with no subagents. | experimental |
| [deepseek-harness](./deepseek-harness/README.md) | Bounded DeepSeek-compatible coding agent with read, write, list and shell tools. | experimental |
| [hermes-agent](./hermes-agent/README.md) | NousResearch Hermes 0.22.1 with pinned upstream runtime, local file/terminal tools and bounded headless execution. | experimental |
| [node-web](./node-web/README.md) | Node.js web service runtime for Express, Fastify and other frameworks | experimental |
| [openclaw](./openclaw/README.md) | OpenClaw 2026.10.4 gateway with authenticated health, owned process lifecycle and Node.js 24.16.0. | experimental |
| [opencode](./opencode/README.md) | OpenCode coding agent. Headless opencode run and optional opencode serve. Package opencode-ai@1.19.0. | experimental |
| [amp](./amp/README.md) | Sourcegraph Amp CLI. amp_execute runs amp -x; amp_version and amp_setup_check do not need a key. Package @ampcode/cli@0.0.1792022479-ge66e24. | experimental |
| [droid](./droid/README.md) | Genuine Factory Droid0.241.1, explicit compatible BYOK and isolated bounded coding. | experimental |
| [gemini](./gemini/README.md) | Gemini CLI. Command gemini -p. Package @google/gemini-cli@0.64.0. | experimental |
| [document-tools](./document-tools/README.md) | Bounded Markdown/HTML to DOCX, TXT, PPTX and headless LibreOffice PDF. | experimental |
| [media-tools](./media-tools/README.md) | Bounded offline CPU FFmpeg presets and native JSON argv with real process results. | experimental |
| [pi](./pi/README.md) | Official Pi CLI 1.3.0 with ephemeral compatible-model settings and explicit writable tools. | experimental |
| [ocr](./ocr/README.md) | CPU English image OCR with pinned Tesseract 5.5.0 and bounded private TXT/TSV artifacts. | experimental |
| [aider](./aider/README.md) | Official Aider 0.86.2 with read-only ask and guarded selected-file writeback. | experimental |
| [swe](./swe/README.md) | mini-swe-agent 2.4.6 with one real SWE-bench Flask instance and independent non-Docker evaluation. | experimental |
| [osworld](./osworld/README.md) | Pinned OSWorld Linux browser slice: real X11 input, screenshots, AT-SPI and selected task evaluators. | experimental |
| [polyglot-toolchain](./polyglot-toolchain/README.md) | Pinned Go, Rust and Temurin JDK with real compile-and-run verification. | experimental |
| [kimi-code](./kimi-code/README.md) | Official Kimi Code 2.2.0 with isolated headless turns and explicit tool permission. | experimental |
| [apply-patch](./apply-patch/README.md) | Official Codex patch dialect with bounded native execution and relative workspace paths. | experimental |
| [goose](./goose/README.md) | Official Goose1.54.0 with private compatible-provider config and explicit developer tools. | experimental |
| [code-server](./code-server/README.md) | Pinned authenticated browser IDE with private configuration and owned process lifecycle. | experimental |
| [dev-services](./dev-services/README.md) | Pinned non-root PostgreSQL17.11 and Redis8.0.2 with owned lifecycle. | experimental |
| [next-app](./next-app/README.md) | Pinned Next.js16.4.2 and Vite8.3.4 frontend scaffold and owned preview lifecycle. | experimental |
| [crush](./crush/README.md) | Official Crush0.98.1 with private compatible-provider turns and explicit tools. | experimental |
| [stagehand](./stagehand/README.md) | Native Stagehand4.3.0 local Chromium act/extract with explicit compatible model transport. | experimental |
| [grok](./grok/README.md) | Official xAI Grok Build1.0.62 native CLI with explicit compatible model and isolated bounded coding. | experimental |
| [cline](./cline/README.md) | Pinned genuine Cline3.0.73 CLI, private compatible provider and bounded headless coding. | experimental |
| [tau2-bench](./tau2-bench/README.md) | Original Tau2 text retail runner with native agent/user models and strict trajectory replay. | experimental |
| [chrome](./chrome/README.md) | Pinned headed Chrome145 with native CDP and authenticated visible noVNC desktop | experimental |
| [prime-agent](./prime-agent/README.md) | Original stable Prime Agent0.10.0 native CLI and fixed CPython REPL with explicit compatible provider. | experimental |
| [appworld](./appworld/README.md) | Original AppWorld engine/evaluator with private encrypted bundles and an explicit compatible-model API bridge | experimental |
| [qm-sandbox](./qm-sandbox/README.md) | Original QM tool context backed by the actual Agent Sandbox Node HTTP SDK. | experimental |
| [qm](./qm/README.md) | Original QM Pi harness and tools with an actual SDK backend and explicit compatible model. | experimental |
| [muse](./muse/README.md) | Original native Meta Muse Code with explicit compatible Responses and an owned catalogue/credential relay. | experimental |
| [cursor-agent](./cursor-agent/README.md) | Pinned original Cursor Agent CLI with explicit owned-sandbox native tools. | experimental |
| [devin](./devin/README.md) | Pinned original Devin CLI with private original account-file integration and explicit tools. | experimental |

## Provider-managed runtime catalog

These templates use the listed provider's existing runtime. Select that provider when launching; they are separate from buildable source templates.

这些模板使用对应提供方的现成运行时，启动时须选择该提供方；它们与可构建的源码模板分开列出。

| ID | Provider | Documentation |
| --- | --- | --- |
| base | alicloud-express | [English](docs/managed/base/README.md) · [中文](docs/managed/base/README.zh-CN.md) |
| code-interpreter-v1 | alicloud-express | [English](docs/managed/code-interpreter-v1/README.md) · [中文](docs/managed/code-interpreter-v1/README.zh-CN.md) |
| desktop | e2b | [English](docs/managed/desktop/README.md) · [中文](docs/managed/desktop/README.zh-CN.md) |
| opensandbox-code-interpreter | opensandbox | [English](docs/managed/opensandbox-code-interpreter/README.md) · [中文](docs/managed/opensandbox-code-interpreter/README.zh-CN.md) |

## Catalog

[`awesome-templates.yaml`](awesome-templates.yaml) is the catalog used by the CLI. Browse it at [registry.agent-sandbox.cn](https://registry.agent-sandbox.cn). The registry is maintained in its [own repository](https://github.com/Alibaba-Agent-Sandbox/registry).

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) ([中文](CONTRIBUTING.zh-CN.md)), the [template specification](docs/template-spec.md) ([中文](docs/template-spec.zh-CN.md)) and [documentation standard](docs/documentation-standards.md) ([中文](docs/documentation-standards.zh-CN.md)).

## License

Apache-2.0. See [LICENSE](LICENSE).
