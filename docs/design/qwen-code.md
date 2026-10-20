# qwen-code

## Purpose

Provide a pinned Qwen Code CLI for developers running autonomous coding jobs with an OpenAI-compatible endpoint inside an isolated sandbox. Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26.

## Capabilities

The complete headless CLI can edit source, run tests and produce files. Named diagnostics inspect real CLI installation and configuration presence without writing user settings. The server exposes file/process APIs and port 9000; named command output is buffered.

## Exposed API

- `qwen(prompt: str required, max_turns: int=100, model: str="", cwd: str="", command_timeout: int=600, yolo: bool=false) -> str`: `qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`, optionally `--model MODEL` and `--yolo`. Turns 1–1000, deadline 1–1800 seconds, existing working directory. CLI `--max-turns` was invalid and is replaced internally without changing the public `max_turns` parameter.
- `qwen_version() -> str`: real `qwen --version`, no model key.
- `qwen_setup_check() -> dict`: installation, actual version, pin, key/model/base URL presence, and settings existence/JSON validity. No arbitrary settings values returned or files created.
- `run(script: str="main.py") -> str`: compatibility Python script invocation, deadline 120 seconds.

## How to build

Template2.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../qwen-code/Dockerfile) keeps the Alibaba FC base, `@qwen-code/qwen-code@0.23.0`, the existing approved pinned server source commit, `/home/user/app` and `USER user`. A task-built wheel takes precedence. Generation 2 uses `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py` and `agent-sandbox-server healthcheck --port 9000`. No image CMD or ENTRYPOINT. Removes unused unpinned Python libraries and root-only settings/skills from the legacy image.

## Express feasibility

Feasible: yes

Limiting factor: none

The non-root CLI needs outbound model access and fits 2 vCPU/4096 MB. No KVM, Docker-in-Docker or extra capabilities. A local image-build daemon remains a deployment prerequisite and was unavailable during this run; feasibility does not claim verified Express execution.

## Risks

Model calls incur cost and depend on endpoint/tool-call compatibility. `OPENAI_API_KEY` has precedence over `DASHSCOPE_API_KEY`; fallback mapping exists only in the child environment. Missing key fails before CLI startup. `yolo` defaults false and requires explicit approval of all tool actions. The process group is terminated on a command deadline; a client HTTP timeout alone does not cancel work. Captured errors and success output redact known secret environment values, including JSON-escaped values. Diagnostic settings reads are non-mutating; the upstream coding agent can create its runtime cache.

## Test plan

L0: static checker, subprocess/configuration/privacy regressions, HTTP command signatures, 400/404 behavior, setup inspection, missing-key guard and explicit CLI missing/pin behavior. `E2E_REQUIRE_CLI=1` prohibits a missing CLI skip. L1: image build must log `0.23.0`. L2: CLI and SDK invoke `qwen_version` from outside an Express sandbox and compare `0.23.0`; record only a complete passing provider run. L3: `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1` with a real compatible endpoint modifies an existing calculator module, preserves original tests, retrieves REPORT.md and an exact `ABX_E2E_OK` artifact via target files APIs, and independently runs unittest plus held-out calculations through the target shell API. Missing key or forced skip under require mode fails. L4: no additional provider is claimed or scheduled by this scoped change.


### Premature-exit acceptance guard

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.
