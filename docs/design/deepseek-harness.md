# deepseek-harness

## Purpose

Run a repository-owned coding agent using the official DeepSeek Chat Completions function-call protocol. Each turn executes read_file, write_file, list_files or run_shell and returns tool results to the model until a final answer.

## Capabilities

Typed named commands on port 9000. `DEEPSEEK_BASE_URL=https://api.deepseek.com`; `DEEPSEEK_MODEL=deepseek-flash`; `WORKSPACE=/home/user/app`. `DEEPSEEK_API_KEY` falls back to `OPENAI_API_KEY`. To use a compatible service, supply its base URL and model explicitly. Native DeepSeek and compatible-service acceptance are separate claims. Tool shell processes do not inherit environment credentials. File tools reject traversal/symlink escapes from cwd, read/write at most 128 KiB, and shell results retain the last 64 KiB per stream. Shell execution has sandbox-user authority and is not confined by file-tool path rules.

## Exposed API

`deepseek` returns a buffered string. Parameters:

- `prompt` (string, required): Task text; nonempty.
- `model` (string, ""): Argument, then DEEPSEEK_MODEL, then deepseek-flash.
- `cwd` (string, ""): Existing directory; relative to WORKSPACE.
- `max_turns` (integer, 20): Maximum API rounds, 1–100.
- `command_timeout` (integer, 600): Worker execution deadline, 1–1800 seconds.

Upstream call: `HTTP POST BASE_URL/chat/completions with tools and assistant/tool messages; run_shell executes /bin/sh -c COMMAND`.

- `deepseek_setup_check` (none): Read-only key-presence/model/tool diagnostic.
- `deepseek_tools` (none): Comma-separated registered tool names; no API call.
- `run` (script: string = main.py): Local Python stdout (compatibility).

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../deepseek-harness/Dockerfile) uses the Alibaba generation-2 base, non-root user,
2048 MB and `/home/user/app`. Python 3.13; `httpx==0.28.1`; Agent Sandbox server. No third-party agent CLI.
The Dockerfile installs published `agent-sandbox-server==0.4.0a2` directly.
`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`.
`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`.
No CMD or ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: none

The selected coding workload needs no Docker, KVM, root or extra capabilities inside the sandbox.
Image builds, rootfs fit and cloud acceptance require their own checks; local CLI installation does not prove them.

## Risks

The model can execute shell commands and alter sandbox files. Use an isolated sandbox for trusted tasks. Worker process-group cancellation bounds the whole loop. No shell tool can access model keys through inherited environment variables; filesystem isolation is still the sandbox boundary.
Secrets are declared with empty values. Error/output paths redact known secret environment values.

## Test plan

- L0: `python3 scripts/check_template.py deepseek-harness`; `python3 -m pytest -q deepseek-harness/test_commands.py`; local HTTP `e2e_test.py`, model disabled.
- L1: image build and pinned upstream version/dependency output; Docker is required.
- L2: `python scripts/public_launch_e2e.py deepseek-harness --provider alicloud-express --application-controller` invokes declared no-key smoke through external CLI and SDK. Only passing runs become provider evidence.
- L3: target diagnostics must report compatible credentials. Repair seeded `calculator.py`, preserve the seeded test, create REPORT.md and acceptance.txt with an exact ABX_E2E_OK marker, retrieve via remote files API, execute independent unittest and held-out tests. Required mode fails on missing credentials.
- L4: no provider claim until a real run.

Primary protocol/source reference: [DeepSeek coding harness](https://api-docs.deepseek.com/guides/tool_calls/).


### Premature-exit acceptance guard

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

Release readiness 1.1.2: align default and injected server SDK source to `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; preserve historical receipts and require new image/workflow acceptance.
