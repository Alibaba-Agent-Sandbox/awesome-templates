# Agent Sandbox Templates

**English** | [中文](README.zh-CN.md)

Reusable environments for AI agents: browser automation, coding tools, web services, document processing and benchmark tasks. Each template documents its own setup, commands and resource cleanup.

[Browse templates](https://registry.agent-sandbox.cn/en/templates/) · [Usage guide](docs/using-templates.md) · [Provider setup](docs/provider-preparation.md)

This branch uses `specVersion: 1` and requires matching development CLI/SDK builds. Published CLI0.5.10 does not support this format. Read the [resource specification](docs/template-spec.md) before running these recipes.

## Quick start

Follow the [usage guide](docs/using-templates.md#installation) to install a matching YAML v1 development CLI and Python client, and prepare platform credentials and build tools. Download the matching template revision, then run inside the introductory template directory; it needs no model:

```bash
cd python-hello
abx deploy . --yes
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
abx sandbox command run <sandbox-id> hello --arg name=Ada
abx sandbox delete <sandbox-id> --yes
```

Use the template ID returned by deploy and the Sandbox ID returned by run.py. The script generates a private application token in the session file, which later calls reuse. Expected result: `Hello, Ada!`. Model templates document their extra credentials. Manage reusable templates and images separately using the [cleanup instructions](docs/using-templates.md#export-files-and-clean-up).

## Choose a template

Source templates need a build. Browse by task below; each template explains its exact dependencies, arguments and supported scope. The Registry provides launch instructions for each platform.

### Getting started and services

| Template | Purpose |
| --- | --- |
| [python-hello](python-hello/README.md) | Minimal Python application with a named hello command |
| [node-web](node-web/README.md) | Node.js web services |
| [agents-api](agents-api/README.md) | One Gateway for session-owned Agents, files and results; requires the managed runtime release |
| [next-app](next-app/README.md) | Next.js and Vite projects with preview servers |
| [code-server](code-server/README.md) | Authenticated browser IDE |
| [dev-services](dev-services/README.md) | PostgreSQL and Redis services |
| [polyglot-toolchain](polyglot-toolchain/README.md) | Go, Rust and Java compilation |

### Browser and desktop

| Template | Purpose |
| --- | --- |
| [browser-automation](browser-automation/README.md) | Playwright and Chromium automation |
| [browser-use](browser-use/README.md) | Model-driven browser automation with browser-use |
| [stagehand](stagehand/README.md) | Browser actions and extraction with Stagehand |
| [chrome](chrome/README.md) | Headed Chrome with CDP and a remote desktop |
| [osworld](osworld/README.md) | OSWorld Linux browser tasks |

### Coding and assistant agents

| Template | Purpose |
| --- | --- |
| [claude-code](claude-code/README.md) | Claude Code coding agent |
| [copilot-cli](copilot-cli/README.md) | Copilot Cli coding agent |
| [codex](codex/README.md) | Codex coding agent |
| [qoder](qoder/README.md) | Qoder coding agent |
| [qwen-code](qwen-code/README.md) | Qwen Code coding agent |
| [deepagents](deepagents/README.md) | DeepAgents file and shell agent |
| [deepseek-harness](deepseek-harness/README.md) | Deepseek Harness coding agent |
| [hermes-agent](hermes-agent/README.md) | Hermes assistant with file and terminal tools |
| [openclaw](openclaw/README.md) | OpenClaw assistant gateway |
| [opencode](opencode/README.md) | Opencode coding agent |
| [amp](amp/README.md) | Amp coding agent |
| [droid](droid/README.md) | Droid coding agent |
| [gemini](gemini/README.md) | Gemini coding agent |
| [pi](pi/README.md) | Pi coding agent |
| [aider](aider/README.md) | Aider coding agent |
| [swe](swe/README.md) | Flask repair task with mini-swe-agent |
| [kimi-code](kimi-code/README.md) | Kimi Code coding agent |
| [goose](goose/README.md) | Goose coding agent |
| [crush](crush/README.md) | Crush coding agent |
| [grok](grok/README.md) | Grok coding agent |
| [cline](cline/README.md) | Cline coding agent |
| [prime-agent](prime-agent/README.md) | Prime Agent coding agent |
| [muse](muse/README.md) | Muse coding agent |
| [cursor-agent](cursor-agent/README.md) | Cursor Agent coding agent |
| [devin](devin/README.md) | Devin coding agent |

### Agent APIs and tools

| Template | Purpose |
| --- | --- |
| [codex-agent-api](codex-agent-api/README.md) | HTTP sessions for Codex |
| [agents-cli](agents-cli/README.md) | Local HTTP API for Codex and Qwen Code |
| [apply-patch](apply-patch/README.md) | Apply Codex-format file patches |
| [qm-sandbox](qm-sandbox/README.md) | QM tools backed by the Node HTTP SDK |
| [qm](qm/README.md) | QM Pi agent harness with an SDK backend |

### Documents, media and benchmarks

| Template | Purpose |
| --- | --- |
| [document-tools](document-tools/README.md) | Document conversion, presentations and PDF export |
| [media-tools](media-tools/README.md) | FFmpeg audio and video processing |
| [ocr](ocr/README.md) | English text recognition with Tesseract |
| [tau2-bench](tau2-bench/README.md) | Tau2 text retail tasks and evaluation |
| [appworld](appworld/README.md) | AppWorld tasks and evaluator |

## Provider-managed runtimes

These entries use an existing runtime on their owning platform. Select that provider and follow its setup:

| ID | Provider | Guide |
| --- | --- | --- |
| base | alicloud-express | [README](docs/managed/base/README.md) |
| code-interpreter-v1 | alicloud-express | [README](docs/managed/code-interpreter-v1/README.md) |
| desktop | e2b | [README](docs/managed/desktop/README.md) |
| opensandbox-code-interpreter | opensandbox | [README](docs/managed/opensandbox-code-interpreter/README.md) |

## Customize and contribute

Search with `abx template list python`. Download an editable copy without creating cloud resources:

```bash
abx template init ./python-hello --from Alibaba-Agent-Sandbox/awesome-templates//python-hello
```

This repository owns the source templates and [`awesome-templates.yaml`](awesome-templates.yaml), read by the CLI and Registry. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [template specification](docs/template-spec.md) before changing or adding a template. Report template problems in [Issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).

## License

[Apache-2.0](LICENSE). Tools and assets used by individual templates also retain their upstream licenses.
