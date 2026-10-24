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
**Historical evidence** retains original input and call-path scope. It does not certify the new workflow manifest. The previous table lists a provider only when that template had a passing
evidence file under `<name>/evidence/`. An empty cell means no passing run
is recorded.

## Templates

Start with [Using templates](docs/using-templates.md) ([中文](docs/using-templates.zh-CN.md)). The catalog contains 46 source recipes and four provider-managed entries; the latter use their own backend and are not portable source builds. On 2026-10-24, the [public launch matrix](.agents/evidence/verify/2026-10-24-public-template-matrix.md) passed all 46 sources on Express and default direct OpenSandbox: 92 cases, 438 CLI/Python/HTTP smoke calls and independently confirmed owned cleanup. Inputs were public CLI 0.4.16, host Python packages 0.3.1a5 and fixed template/provider checkouts. [Remote Git journeys](.agents/evidence/verify/2026-10-24-public-git-journeys.md) and [managed runtime checks](.agents/evidence/verify/2026-10-24-managed-template-usage.md) have separate scope. This is dated smoke evidence, not certification of real-model tasks, PTY or every interpreter/desktop interface.

Historical 2026-10-22 source-image acceptance (before workflow schema v4): **Express regular-image runtime and independent cleanup46/46; complete image HTTP46/46; original OpenSandbox source images46/46**. Every OpenSandbox result includes real provider CLI and SDK named calls, the complete HTTP controller and independent SDK/container/process cleanup. [Full matrix](.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json) · [reproduce](docs/source-image-acceptance.md) ([中文](docs/source-image-acceptance.zh-CN.md)). Model/vendor-account skips and unsupported generic `run_code`/CLI launch capabilities remain separate limits. Existing Express step46/46 and full HTTP46/46 were [rechecked after qualification metadata changed](.agents/evidence/verify/2026-10-22-current-steps-after-backend-qualification.json); earlier checkpoints remain below.


Historical 2026-10-21 46-template Express platform-step checkpoint: **46/46 current native/runtime and required full HTTP PASS**, with actual CLI/SDK calls and independently verified owned cleanup. [Current46matrix](.agents/evidence/verify/2026-10-21-current-native-http46-devin101.json) · [operations and scope](docs/platform-steps.md) ([中文](docs/platform-steps.zh-CN.md)). These were receipt matches at that checkpoint, not46new deployments or universal model/Docker/vendor acceptance. Per-template Verified sections retain the exact product/model scope.

Historical [44matrix](.agents/evidence/verify/2026-10-21-current-native-http44.json), [43matrix](.agents/evidence/verify/2026-10-21-current-native-http43.json), [41matrix](.agents/evidence/verify/2026-10-21-current-native-http41.json), [Prime40matrix](.agents/evidence/verify/2026-10-21-current-native-http40.json), [AppWorld40matrix](.agents/evidence/verify/2026-10-21-current-native-http40-appworld.json), [Chrome39matrix](.agents/evidence/verify/2026-10-20-current-native-http39.json), [Droid38matrix](.agents/evidence/verify/2026-10-20-current-native-http38-droid.json), [earlier38matrix](.agents/evidence/verify/2026-10-20-current-native-http38.json), [37matrix](.agents/evidence/verify/2026-10-20-current-native-http37.json), [35matrix](.agents/evidence/verify/2026-10-20-current-native-http35.json) and [34matrix](.agents/evidence/verify/2026-10-20-complete-platform-steps-matrix.json) remain unchanged.


The [2026-10-18 acceptance review](docs/verification-2026-10-18.md) ([中文](docs/verification-2026-10-18.zh-CN.md)) records the historical23-template checkpoint and its unresolved gates. Historical per-template receipts are linked below.

| Template | Description | Status | Historical evidence |
|----------|-------------|--------|-------------|
| [python-hello](./python-hello/README.md) | A minimal Python hello world template for testing | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./python-hello/evidence/full-http-steps-2026-10-19T183219Z.json) · [Express image + HTTP](python-hello/evidence/image-http-2026-10-22T103900Z.json) · [OpenSandbox image + HTTP](python-hello/evidence/opensandbox-2026-10-22T112700Z.json) |
| [browser-use](./browser-use/README.md) | Native browser-use0.13.11 with private local pinned Chromium and explicit model. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./browser-use/evidence/verification-steps-2026-10-20T153859Z.json) · [Express image + HTTP](browser-use/evidence/image-http-2026-10-20T144122Z.json) · [OpenSandbox image + HTTP](browser-use/evidence/opensandbox-2026-10-22T110655Z.json) |
| [browser-automation](./browser-automation/README.md) | Browser automation sandbox with Playwright + Chromium for web scraping and UI testing | experimental | [alicloud-express 2.2.0; steps/runtime + HTTP](./browser-automation/evidence/full-http-steps-2026-10-20T103410Z.json) · [Express image + HTTP](browser-automation/evidence/image-http-2026-10-22T101142Z.json) · [OpenSandbox image + HTTP](browser-automation/evidence/opensandbox-2026-10-22T110653Z.json) |
| [claude-code](./claude-code/README.md) | Claude Code Agent runtime — Anthropic Claude-powered AI coding assistant | experimental | [alicloud-express 1.3.1; steps/runtime + HTTP](./claude-code/evidence/verification-steps-2026-10-21T094126Z.json) · [Express image + HTTP](claude-code/evidence/image-http-2026-10-22T102154Z.json) · [OpenSandbox image + HTTP](claude-code/evidence/opensandbox-2026-10-22T110508Z.json) |
| [copilot-cli](./copilot-cli/README.md) | Pinned native GitHub Copilot CLI1.0.100 with explicit OpenAI-compatible BYOK and owned process lifecycle. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./copilot-cli/evidence/verification-steps-2026-10-20T171425Z.json) · [Express image + HTTP](copilot-cli/evidence/image-http-2026-10-22T105025Z.json) · [OpenSandbox image + HTTP](copilot-cli/evidence/opensandbox-2026-10-22T110834Z.json) |
| [codex](./codex/README.md) | OpenAI Codex CLI (@openai/codex@0.162.1). codex exec, JSON events, sandbox bypass, OpenAI-compatible config.toml. | experimental | [alicloud-express 2.0.0; steps/runtime + HTTP](./codex/evidence/verification-steps-2026-10-20T154825Z.json) · [Express image + HTTP](codex/evidence/image-http-2026-10-20T145436Z.json) · [OpenSandbox image + HTTP](codex/evidence/opensandbox-2026-10-22T110946Z.json) |
| [codex-agent-api](./codex-agent-api/README.md) | Codex 0.162.1 HTTP session adapter with bounded turns and SSE; project API subset, not full OpenAI API compatibility. | experimental | [alicloud-express 2.0.0; steps/runtime + HTTP](./codex-agent-api/evidence/native-model-sdk-steps-2026-10-20T175340Z.json) · [Express image + HTTP](codex-agent-api/evidence/image-http-2026-10-22T105026Z.json) · [OpenSandbox image + HTTP](codex-agent-api/evidence/opensandbox-2026-10-22T110910Z.json) |
| [qoder](./qoder/README.md) | Qoder coding CLI @qoder-ai/qodercli@1.1.72 with version, read-only setup and bounded headless execution. | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./qoder/evidence/verification-steps-2026-10-21T093940Z.json) · [Express image + HTTP](qoder/evidence/image-http-2026-10-22T113531Z.json) · [OpenSandbox image + HTTP](qoder/evidence/opensandbox-2026-10-22T112920Z.json) |
| [agents-cli](./agents-cli/README.md) | Restricted local Agents HTTP API with pinned Codex 0.162.1 and Qwen Code 0.23.0. | experimental | [alicloud-express 2.0.1; steps/runtime + HTTP](./agents-cli/evidence/verification-steps-2026-10-20T154625Z.json) · [Express image + HTTP](agents-cli/evidence/image-http-2026-10-22T103934Z.json) · [OpenSandbox image + HTTP](agents-cli/evidence/opensandbox-2026-10-22T110057Z.json) |
| [qwen-code](./qwen-code/README.md) | Qwen Code Agent runtime — Dashscope-powered AI autonomous deployment agent | experimental | [alicloud-express 2.1.1; steps/runtime + HTTP](./qwen-code/evidence/verification-steps-2026-10-20T155502Z.json) · [Express image + HTTP](qwen-code/evidence/image-http-2026-10-20T073522Z.json) · [OpenSandbox image + HTTP](qwen-code/evidence/opensandbox-2026-10-22T113215Z.json) |
| [deepagents](./deepagents/README.md) | Native DeepAgents0.7.25 local file/shell compatible-provider runtime with no subagents. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./deepagents/evidence/verification-steps-2026-10-20T141151Z.json) · [Express image + HTTP](deepagents/evidence/image-http-2026-10-22T110056Z.json) · [OpenSandbox image + HTTP](deepagents/evidence/opensandbox-2026-10-22T111055Z.json) |
| [deepseek-harness](./deepseek-harness/README.md) | Bounded DeepSeek-compatible coding agent with read, write, list and shell tools. | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./deepseek-harness/evidence/verification-steps-2026-10-20T154957Z.json) · [Express image + HTTP](deepseek-harness/evidence/image-http-2026-10-20T073449Z.json) · [OpenSandbox image + HTTP](deepseek-harness/evidence/opensandbox-2026-10-22T111057Z.json) |
| [hermes-agent](./hermes-agent/README.md) | NousResearch Hermes 0.22.1 with pinned upstream runtime, local file/terminal tools and bounded headless execution. | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./hermes-agent/evidence/verification-steps-2026-10-20T151019Z.json) · [Express image + HTTP](hermes-agent/evidence/image-http-2026-10-20T110933Z.json) · [OpenSandbox image + HTTP](hermes-agent/evidence/opensandbox-2026-10-22T111713Z.json) |
| [node-web](./node-web/README.md) | Node.js web service runtime for Express, Fastify and other frameworks | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./node-web/evidence/full-http-steps-2026-10-19T183324Z.json) · [Express image + HTTP](node-web/evidence/image-http-2026-10-22T111340Z.json) · [OpenSandbox image + HTTP](node-web/evidence/opensandbox-2026-10-22T112111Z.json) |
| [openclaw](./openclaw/README.md) | OpenClaw 2026.10.4 gateway with authenticated health, owned process lifecycle and Node.js 24.16.0. | experimental | [alicloud-express 2.1.0; steps/runtime + HTTP](./openclaw/evidence/verification-steps-2026-10-20T170739Z.json) · [Express image + HTTP](openclaw/evidence/image-http-2026-10-22T112320Z.json) · [OpenSandbox image + HTTP](openclaw/evidence/opensandbox-2026-10-22T112327Z.json) |
| [opencode](./opencode/README.md) | OpenCode coding agent. Headless opencode run and optional opencode serve. Package opencode-ai@1.19.0. | experimental | [alicloud-express 2.0.2; steps/runtime + HTTP](./opencode/evidence/verification-steps-2026-10-20T160725Z.json) · [Express image + HTTP](opencode/evidence/image-http-2026-10-22T112305Z.json) · [OpenSandbox image + HTTP](opencode/evidence/opensandbox-2026-10-22T112437Z.json) |
| [amp](./amp/README.md) | Sourcegraph Amp CLI. amp_execute runs amp -x; amp_version and amp_setup_check do not need a key. Package @ampcode/cli@0.0.1792022479-ge66e24. | experimental | [alicloud-express 1.2.0; steps/runtime + HTTP](./amp/evidence/verification-steps-2026-10-20T154625Z.json) · [Express image + HTTP](amp/evidence/image-http-2026-10-22T103927Z.json) · [OpenSandbox image + HTTP](amp/evidence/opensandbox-2026-10-22T110057Z.json) |
| [droid](./droid/README.md) | Genuine Factory Droid0.241.1, explicit compatible BYOK and isolated bounded coding. | experimental | [alicloud-express 1.2.0; steps/runtime + HTTP](./droid/evidence/verification-steps-2026-10-20T212811Z.json) · [Express image + HTTP](droid/evidence/image-http-2026-10-22T110246Z.json) · [OpenSandbox image + HTTP](droid/evidence/opensandbox-2026-10-22T111346Z.json) |
| [gemini](./gemini/README.md) | Gemini CLI. Command gemini -p. Package @google/gemini-cli@0.64.0. | experimental | [alicloud-express 2.2.0; steps/runtime + HTTP](./gemini/evidence/verification-steps-2026-10-21T091644Z.json) · [Express image + HTTP](gemini/evidence/image-http-2026-10-22T110330Z.json) · [OpenSandbox image + HTTP](gemini/evidence/opensandbox-2026-10-22T111421Z.json) |
| [document-tools](./document-tools/README.md) | Bounded Markdown/HTML to DOCX, TXT, PPTX and headless LibreOffice PDF. | experimental | [alicloud-express 1.1.0; steps/runtime + HTTP](./document-tools/evidence/full-http-steps-2026-10-20T143722Z.json) · [Express image + HTTP](document-tools/evidence/image-http-2026-10-20T150549Z.json) · [OpenSandbox image + HTTP](document-tools/evidence/opensandbox-2026-10-22T112219Z.json) |
| [media-tools](./media-tools/README.md) | Bounded offline CPU FFmpeg presets and native JSON argv with real process results. | experimental | [alicloud-express 1.1.0; steps/runtime + HTTP](./media-tools/evidence/full-http-steps-2026-10-20T131812Z.json) · [Express image + HTTP](media-tools/evidence/image-http-2026-10-20T133417Z.json) · [OpenSandbox image + HTTP](media-tools/evidence/opensandbox-2026-10-22T112438Z.json) |
| [pi](./pi/README.md) | Official Pi CLI 1.3.0 with ephemeral compatible-model settings and explicit writable tools. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./pi/evidence/verification-steps-2026-10-20T155246Z.json) · [Express image + HTTP](pi/evidence/image-http-2026-10-20T112202Z.json) · [OpenSandbox image + HTTP](pi/evidence/opensandbox-2026-10-22T112547Z.json) |
| [ocr](./ocr/README.md) | CPU English image OCR with pinned Tesseract 5.5.0 and bounded private TXT/TSV artifacts. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./ocr/evidence/full-http-steps-2026-10-20T061143Z.json) · [Express image + HTTP](ocr/evidence/image-http-2026-10-20T054627Z.json) · [OpenSandbox image + HTTP](ocr/evidence/opensandbox-2026-10-22T112402Z.json) |
| [aider](./aider/README.md) | Official Aider 0.86.2 with read-only ask and guarded selected-file writeback. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./aider/evidence/verification-steps-2026-10-20T135354Z.json) · [Express image + HTTP](aider/evidence/image-http-2026-10-20T112118Z.json) · [OpenSandbox image + HTTP](aider/evidence/opensandbox-2026-10-22T110057Z.json) |
| [swe](./swe/README.md) | mini-swe-agent 2.4.6 with one real SWE-bench Flask instance and independent non-Docker evaluation. | experimental | [alicloud-express 1.1.0; steps/runtime + HTTP](./swe/evidence/verification-steps-2026-10-20T143844Z.json) · [Express image + HTTP](swe/evidence/image-http-2026-10-20T091111Z.json) · [OpenSandbox image + HTTP](swe/evidence/opensandbox-2026-10-22T113251Z.json) |
| [osworld](./osworld/README.md) | Pinned OSWorld Linux browser slice: real X11 input, screenshots, AT-SPI and selected task evaluators. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./osworld/evidence/verification-steps-2026-10-20T171144Z.json) · [Express image + HTTP](osworld/evidence/image-http-2026-10-22T113339Z.json) · [OpenSandbox image + HTTP](osworld/evidence/opensandbox-2026-10-22T113506Z.json) |
| [polyglot-toolchain](./polyglot-toolchain/README.md) | Pinned Go, Rust and Temurin JDK with real compile-and-run verification. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./polyglot-toolchain/evidence/verification-steps-2026-10-20T135358Z.json) · [Express image + HTTP](polyglot-toolchain/evidence/image-http-2026-10-20T070826Z.json) · [OpenSandbox image + HTTP](polyglot-toolchain/evidence/opensandbox-2026-10-22T112736Z.json) |
| [kimi-code](./kimi-code/README.md) | Official Kimi Code 2.2.0 with isolated headless turns and explicit tool permission. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./kimi-code/evidence/verification-steps-2026-10-20T155159Z.json) · [Express image + HTTP](kimi-code/evidence/image-http-2026-10-22T111230Z.json) · [OpenSandbox image + HTTP](kimi-code/evidence/opensandbox-2026-10-22T111821Z.json) |
| [apply-patch](./apply-patch/README.md) | Official Codex patch dialect with bounded native execution and relative workspace paths. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./apply-patch/evidence/verification-steps-2026-10-20T154625Z.json) · [Express image + HTTP](apply-patch/evidence/image-http-2026-10-22T104212Z.json) · [OpenSandbox image + HTTP](apply-patch/evidence/opensandbox-2026-10-22T110058Z.json) |
| [goose](./goose/README.md) | Official Goose1.54.0 with private compatible-provider config and explicit developer tools. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./goose/evidence/verification-steps-2026-10-20T135350Z.json) · [Express image + HTTP](goose/evidence/image-http-2026-10-20T073500Z.json) · [OpenSandbox image + HTTP](goose/evidence/opensandbox-2026-10-22T111529Z.json) |
| [code-server](./code-server/README.md) | Pinned authenticated browser IDE with private configuration and owned process lifecycle. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./code-server/evidence/verification-steps-2026-10-20T135352Z.json) · [Express image + HTTP](code-server/evidence/image-http-2026-10-20T091440Z.json) · [OpenSandbox image + HTTP](code-server/evidence/opensandbox-2026-10-22T110651Z.json) |
| [dev-services](./dev-services/README.md) | Pinned non-root PostgreSQL17.11 and Redis8.0.2 with owned lifecycle. | experimental | [alicloud-express 1.1.0; steps/runtime + HTTP](./dev-services/evidence/full-http-steps-2026-10-20T130648Z.json) · [Express image + HTTP](dev-services/evidence/image-http-2026-10-20T101159Z.json) · [OpenSandbox image + HTTP](dev-services/evidence/opensandbox-2026-10-22T111605Z.json) |
| [next-app](./next-app/README.md) | Pinned Next.js16.4.2 and Vite8.3.4 frontend scaffold and owned preview lifecycle. | experimental | [alicloud-express 1.1.0; steps/runtime + HTTP](./next-app/evidence/full-http-steps-2026-10-20T130712Z.json) · [Express image + HTTP](next-app/evidence/image-http-2026-10-20T102030Z.json) · [OpenSandbox image + HTTP](next-app/evidence/opensandbox-2026-10-22T112003Z.json) |
| [crush](./crush/README.md) | Official Crush0.98.1 with private compatible-provider turns and explicit tools. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./crush/evidence/verification-steps-2026-10-20T131749Z.json) · [Express image + HTTP](crush/evidence/image-http-2026-10-20T111012Z.json) · [OpenSandbox image + HTTP](crush/evidence/opensandbox-2026-10-22T111021Z.json) |
| [stagehand](./stagehand/README.md) | Native Stagehand4.3.0 local Chromium act/extract with explicit compatible model transport. | experimental | [alicloud-express 1.1.1; steps/runtime + HTTP](./stagehand/evidence/verification-steps-2026-10-20T190109Z.json) · [Express image + HTTP](stagehand/evidence/image-http-2026-10-22T114531Z.json) · [OpenSandbox image + HTTP](stagehand/evidence/opensandbox-2026-10-22T113725Z.json) |
| [grok](./grok/README.md) | Official xAI Grok Build1.0.62 native CLI with explicit compatible model and isolated bounded coding. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./grok/evidence/verification-steps-2026-10-20T201501Z.json) · [Express image + HTTP](grok/evidence/image-http-2026-10-22T111201Z.json) · [OpenSandbox image + HTTP](grok/evidence/opensandbox-2026-10-22T111604Z.json) |
| [cline](./cline/README.md) | Pinned genuine Cline3.0.73 CLI, private compatible provider and bounded headless coding. | experimental | [alicloud-express 1.0.2; steps/runtime + HTTP](./cline/evidence/verification-steps-2026-10-20T201959Z.json) · [Express image + HTTP](cline/evidence/image-http-2026-10-22T105009Z.json) · [OpenSandbox image + HTTP](cline/evidence/opensandbox-2026-10-22T110504Z.json) |
| [tau2-bench](./tau2-bench/README.md) | Original Tau2 text retail runner with native agent/user models and strict trajectory replay. | experimental | [alicloud-express 1.0.4; steps/runtime + HTTP](./tau2-bench/evidence/verification-steps-2026-10-20T212600Z.json) · [Express image + HTTP](tau2-bench/evidence/image-http-2026-10-22T114617Z.json) · [OpenSandbox image + HTTP](tau2-bench/evidence/opensandbox-2026-10-22T113509Z.json) |
| [chrome](./chrome/README.md) | Pinned headed Chrome145 with native CDP and authenticated visible noVNC desktop | experimental | [alicloud-express 1.0.5; steps/runtime + HTTP](./chrome/evidence/verification-steps-2026-10-20T230349Z.json) · [Express image + HTTP](chrome/evidence/image-http-2026-10-22T101624Z.json) · [OpenSandbox image + HTTP](chrome/evidence/opensandbox-2026-10-22T110912Z.json) |
| [prime-agent](./prime-agent/README.md) | Original stable Prime Agent0.10.0 native CLI and fixed CPython REPL with explicit compatible provider. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./prime-agent/evidence/verification-steps-2026-10-21T000126Z.json) · [Express image + HTTP](prime-agent/evidence/image-http-2026-10-22T112500Z.json) · [OpenSandbox image + HTTP](prime-agent/evidence/opensandbox-2026-10-22T112738Z.json) |
| [appworld](./appworld/README.md) | Original AppWorld engine/evaluator with private encrypted bundles and an explicit compatible-model API bridge | experimental | [alicloud-express 1.0.6; steps/runtime + HTTP](./appworld/evidence/verification-steps-2026-10-21T000253Z.json) · [Express image + HTTP](appworld/evidence/image-http-2026-10-22T100518Z.json) · [OpenSandbox image + HTTP](appworld/evidence/opensandbox-2026-10-22T110058Z.json) |
| [qm-sandbox](./qm-sandbox/README.md) | Original QM tool context backed by the actual Agent Sandbox Node HTTP SDK. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./qm-sandbox/evidence/verification-steps-2026-10-21T021037Z.json) · [Express image + HTTP](qm-sandbox/evidence/image-http-2026-10-22T113846Z.json) · [OpenSandbox image + HTTP](qm-sandbox/evidence/opensandbox-2026-10-22T113106Z.json) |
| [qm](./qm/README.md) | Original QM Pi harness and tools with an actual SDK backend and explicit compatible model. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./qm/evidence/verification-steps-2026-10-21T021039Z.json) · [Express image + HTTP](qm/evidence/image-http-2026-10-22T113747Z.json) · [OpenSandbox image + HTTP](qm/evidence/opensandbox-2026-10-22T113030Z.json) |
| [muse](./muse/README.md) | Original native Meta Muse Code with explicit compatible Responses and an owned catalogue/credential relay. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./muse/evidence/verification-steps-2026-10-21T031347Z.json) · [Express image + HTTP](muse/evidence/image-http-2026-10-22T111344Z.json) · [OpenSandbox image + HTTP](muse/evidence/opensandbox-2026-10-22T111929Z.json) |
| [cursor-agent](./cursor-agent/README.md) | Pinned original Cursor Agent CLI with explicit owned-sandbox native tools. | experimental | [alicloud-express 1.0.0; steps/runtime + HTTP](./cursor-agent/evidence/verification-steps-2026-10-21T110917Z.json) · [Express image + HTTP](cursor-agent/evidence/image-http-2026-10-22T105311Z.json) · [OpenSandbox image + HTTP](cursor-agent/evidence/opensandbox-2026-10-22T111132Z.json) |
| [devin](./devin/README.md) | Pinned original Devin CLI with private original account-file integration and explicit tools. | experimental | [alicloud-express 1.0.1; steps/runtime + HTTP](./devin/evidence/verification-steps-2026-10-21T124114Z.json) · [Express image + HTTP](devin/evidence/image-http-2026-10-22T110118Z.json) · [OpenSandbox image + HTTP](devin/evidence/opensandbox-2026-10-22T111239Z.json) |

Provider-managed images belong to their own backend; they are separate from this repository's source Dockerfiles. Express `base`/`code-interpreter-v1` and the original OpenSandbox interpreter are documented in the [managed runtime catalog](#provider-managed-runtime-catalog).

For automatic source preparation supported by the installed provider on a provider-capable CLI host, use `abx --provider <provider> template launch Alibaba-Agent-Sandbox/awesome-templates//<name> --yes`. The provider owns its native base/image build, registration and launch reference; selected workflow operations and provider configuration remain required. See the [CLI preparation/launch guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/c8e8ad784323b8903505442cbc77d433a0d0367a/docs/en/guide/template-launch.md). An existing ID or source directory never converts between providers. OpenSandbox keepalive entrypoint configuration is explicit; selected exec startup belongs to the workflow.

Catalog provider values are preparation prerequisites, not verification. See
[provider-owned source preparation](docs/provider-preparation.md) ([中文](docs/provider-preparation.zh-CN.md));
missing operations block only their selected workflow and provider IDs never convert across clouds.

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

See the [current workflow contract](docs/workflows.md) ([中文](docs/workflows.zh-CN.md)). Source manifests use specification4; historical evidence below does not certify new consumer paths. Unresolved base placeholders fail preflight, and retained preparation artifacts require explicit recovery.

Use a CLI build that includes `template launch` and configure the selected provider once. The adapter builds or registers the source and passes its returned ID, name or image directly to sandbox creation:

```sh
abx --provider e2b template launch alibaba-agent-sandbox/awesome-templates//python-hello --yes
```

Third-party providers remain Beta. Explicit manifest workflows replace handwritten provider hints. Only the selected workflow is checked before building; an application HTTP path does not require unified code interpretation. Native base images, registry access and cluster requirements belong to each provider. See the [provider preparation guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/template-launch.md). Existing provider/template evidence remains authoritative; no Verified-on claim changes here.

## 在其他提供方上自动准备

使用包含 `template launch` 的 CLI，并完成一次提供方配置。适配器构建或登记本目录，把返回的 ID、名称或镜像直接传给沙箱创建，无需手动查找 ID：

```sh
abx --provider e2b template launch alibaba-agent-sandbox/awesome-templates//python-hello --yes
```

第三方提供方继续为 Beta。清单的显式工作流取代手写提供方提示。构建前仅检查选中路径；应用 HTTP 不依赖统一解释器。原生基础镜像、镜像仓库和集群条件由各提供方维护。见[自动准备指南](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/template-launch.md)。已有验收证据仍为准，本次不修改 Verified-on 声明。

[Next.js/Vite preview template](next-app/README.md) · experimental; [alicloud-express1.1.0 SDK image and independent forwarded HTTP](next-app/evidence/express-2026-10-20.json).
Browser IDE: [code-server](code-server/README.md) (experimental; [alicloud-express1.0.0 SDK image and sdk-local browser](code-server/evidence/express-2026-10-20.json)).
Pinned Go/Rust/Java runtime: [polyglot-toolchain](polyglot-toolchain/README.md) (experimental; verification gates recorded separately).
Model-free file tool: [apply-patch](apply-patch/README.md) (experimental).

Native local DeepAgents: [deepagents](deepagents/README.md) (experimental; [alicloud-express1.0.0 SDK image and model17](deepagents/evidence/express-2026-10-20.json)).

Official terminal agent: [goose](goose/README.md) (experimental; [alicloud-express1.0.0 SDK image + model17](goose/evidence/express-2026-10-20.json)).

## Provider-managed runtime catalog

| ID | Provider | Documentation | Verified scope |
| --- | --- | --- | --- |
| base | alicloud-express | [English](docs/managed/base/README.md) · [中文](docs/managed/base/README.zh-CN.md) | shell, files, historical SDK shell-fallback code (removed), CLI exec; owned cleanup |
| code-interpreter-v1 | alicloud-express | [English](docs/managed/code-interpreter-v1/README.md) · [中文](docs/managed/code-interpreter-v1/README.zh-CN.md) | shell, files, historical SDK shell-fallback code (removed), CLI exec; owned cleanup |
| desktop | e2b | [English](docs/managed/desktop/README.md) · [中文](docs/managed/desktop/README.zh-CN.md) | NOT_VERIFIED; no independent account key; actual SDK/protocol tests only |
| opensandbox-code-interpreter | opensandbox | [English](docs/managed/opensandbox-code-interpreter/README.md) · [中文](docs/managed/opensandbox-code-interpreter/README.zh-CN.md) | Original Docker server + SDK shell/files + native interpreter/context/error checks24PASS; independent cleanup; project unified interpreter is not adapted |

These provider-managed IDs are listed separately from buildable source templates.
For the two Express entries, native interpreter service was HTTP404 in their recorded tests.
The two external entries remain NOT_VERIFIED; no native interpreter or other-provider certification is claimed.

Official native Crush: [crush](crush/README.md) (experimental; [alicloud-express1.0.0 SDK image and model17](crush/evidence/express-2026-10-20.json)).
[Development database template](dev-services/README.md) · experimental; [alicloud-express1.1.0 SDK image and HTTP6](dev-services/evidence/express-2026-10-20.json).

[Devin original native CLI](devin/README.md): experimental1.0.1; native Express SDK/full HTTP passed; authenticated model NOT_RUN.

## Current API / 当前接口

Development changes remove retired project compatibility paths. Provider project preparation uses `templates.build`; the shared feature list no longer advertises the standalone image factory.
开发变更直接删除旧项目兼容路径。提供方项目准备使用 `templates.build`，共享能力表移除独立镜像工厂。
