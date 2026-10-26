# Pi

## Purpose

Run the official Pi coding CLI as a typed, bounded task inside an Alibaba sandbox. The existing Issue 41 is the owner. An E2B template ID is not needed to install the official CLI on Alibaba's base.

## Capabilities

The delivered slice is ephemeral print mode with an OpenAI-compatible chat-completions endpoint. Version and setup diagnostics need no key. Model execution defaults to read/grep/find/ls; explicit `allow_tools=true` also enables edit/write/bash. Shell/files/code/ports capabilities describe the server surface. Interactive TUI, RPC sessions and extension installation are outside the wrapper.

## Exposed API

- `pi_version()` → installed version string; argv `pi --version`.
- `pi_tools_check()` → `read/find/grep/ls OK` after actually executing all four official tool implementations on disposable files with offline mode; no model call.
- `pi_setup_check()` → installed/version/pinned-version, boolean key/endpoint/model availability and workspace; no config mutation or secret/endpoint values.
- `pi(prompt: str, cwd: str = "", allow_tools: bool = False, command_timeout: int = 600)` → buffered, redacted text. Nonempty prompt and an existing directory are required. Timeout range 1–1800. Actual argv is `pi --print --mode text --no-session --offline --no-approve --no-extensions --no-mcp --no-skills --no-prompt-templates --no-themes --no-context-files --provider abx --model <PI_MODEL> --tools <allowlist>`; the prompt is stdin.

Each call owns a temporary config directory with `models.json`, using `api: openai-completions`, configured base/model and the literal `$PI_API_KEY` reference. No caller-supplied flags, command-valued configuration or prior auth/session settings are reused. Upstream 1.3.0 `cli/args.js` maps `--no-approve` to `projectTrustOverride=false`; `main.js` forwards `parsed.tools` as the selected tool set. The actual pinned CLI protocol regression confirms both allowlists and ignored project extensions.

## How to build

Template1.0.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../pi/Dockerfile) uses the Alibaba base placeholder, SHA256-verified official Node 24.16.0 archives for x64/arm64, and exact `@earendil-works/pi-coding-agent@1.3.0` with upstream-recommended `--ignore-scripts`. The committed package-lock freezes the complete 118-package dependency tree and npm ci installs it with ignore-scripts/omit-dev. Official fd 10.5.0 and ripgrep 15.2.0 musl archives for x64/arm64 use fixed GitHub-published SHA256 digests. Complete extracted directories retain fd LICENSE-MIT/LICENSE-APACHE and rg LICENSE-MIT/UNLICENSE/COPYING, plus README/other distribution files, under /opt/pi-tools. Direct fd/rg executable links avoid Debian fdfind naming ambiguity. The server uses the published package pin declared in the Dockerfile. No cloud/model key is a build input.

Generation 2 starts `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`; readiness uses `agent-sandbox-server healthcheck --port 9000`. The image runs as `user` and does not replace the platform entrypoint.

## Express feasibility

Feasible: slice

Limiting factor: no identified platform blocker for print mode; actual Pi image build/deployment is pending.

Non-root execution, 2 vCPU, no Docker/KVM/extra capabilities and outbound HTTPS support this slice. This is the official CLI installed in Alibaba's image, without claiming E2B's Pi template was registered or verified.

## Risks

Writable tools authorize the model to execute code and access this sandbox user's files and environment. Tool selection is a wrapper boundary; `--no-approve` is project trust control. cwd is not path containment. The model endpoint receives prompts/files selected by the tools. Config secrets are referenced through environment variables and redacted from returned text, including JSON-escaped values; arbitrary secret transformations cannot be guaranteed.

The Linux owned runner drains both pipes, keeps the leader unreaped using WNOWAIT, and kills its group before reaping after success/error/deadline/Python cancellation. Deliberate setsid escapes are outside that ownership. HTTP disconnect is not cancellation. The temporary config is cleaned on every exit path; model responses remain buffered in memory.

## Test plan

L0: checker, command/process/privacy regressions, verifier false-acceptance regressions, actual Pi against a local OpenAI protocol fixture, and local HTTP smoke. The fixture is protocol evidence only. L1: selected image CI checks non-root runtime, Node v24.16.0, Pi 1.3.0, fd 10.5.0 and rg 15.2.0, plus pi_version and actual offline pi_tools_check smoke. L2: actual changed image deployment, SDK create/named command/cleanup; pending until run. L3: target model diagnostic, seeded failing source/tests, real writable Pi turn, retrieved changed source/new report/exact ABX_E2E_OK artifact/original tests, isolated target unittest and direct-source held-out inputs. A marker is insufficient. Local source/model evidence is separate from image/provider acceptance. L4: not planned for this slice.

Official references: [tagged CLI](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/docs/cli.md), [tagged model configuration](https://github.com/earendil-works/pi/blob/v1.3.0/packages/coding-agent/docs/models.md), [npm version](https://registry.npmjs.org/@earendil-works/pi-coding-agent/1.3.0), [Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41).


### Premature-exit acceptance guard

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

Current-version acceptance on 2026-10-20: version 1.0.1 genuine image READY/CLI/SDK and 18 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion. Independently verified sandbox/template/registry cleanup. Historical pending statements describe earlier checkpoints; see the dated [2026-10-20 receipt](../../pi/evidence/express-2026-10-20.json).
