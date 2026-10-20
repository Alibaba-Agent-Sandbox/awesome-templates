# hermes-agent

## Purpose

Run the actual upstream Hermes Agent CLI with its local terminal and file toolsets. This template exposes the coding slice; messaging gateways, browser/desktop integrations and external terminal backends are not provisioned.

## Capabilities

Typed named commands on port 9000. `WORKSPACE=/home/user/app`; `HERMES_HOME=/home/user/.hermes`; `HERMES_PROVIDER=openrouter`. Supply `HERMES_MODEL` or the model argument. OpenRouter requires `OPENROUTER_API_KEY`; openai-api/custom require `OPENAI_API_KEY`. Custom also requires `OPENAI_BASE_URL`. The command uses `-Q --yolo`, terminal/file toolsets and the local terminal backend. It ignores user config and rules, does not run interactive setup, and kills the owned process group on timeout. Hermes may persist session/memory state under HERMES_HOME.

## Exposed API

`hermes` returns a buffered string. Parameters:

- `prompt` (string, required): Task text; nonempty.
- `model` (string, ""): Required argument or HERMES_MODEL; no implicit model choice.
- `provider` (string, ""): Argument or HERMES_PROVIDER=openrouter; openrouter / openai-api / custom.
- `cwd` (string, ""): Existing directory; relative to WORKSPACE.
- `max_turns` (integer, 20): Maximum tool rounds, 1–100.
- `command_timeout` (integer, 600): CLI process deadline, 1–1800 seconds; accepted gateway turns can continue.

Upstream call: `hermes chat -Q --yolo -q PROMPT --provider PROVIDER --model MODEL --toolsets terminal,file --max-turns N --ignore-user-config --ignore-rules [--base-url URL]`.

- `hermes_version` (none): Installed upstream version and provenance.
- `hermes_setup_check` (none): Read-only CLI/version/provider-key diagnostic.
- `run` (script: string = main.py): Local Python stdout (compatibility).

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../hermes-agent/Dockerfile) uses the Alibaba generation-2 base, non-root user,
2048 MB and `/home/user/app`. NousResearch Hermes Agent v0.22.1, commit `297552a9d646119871391d202509822cd86330df`; private Python 3.14.6; `uv==0.12.3`; upstream frozen `uv.lock`; platform Agent Sandbox server.
The server archive is pinned to python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505`;
local wheel injection can override it for review.
`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`.
`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`.
No CMD or ENTRYPOINT.

Hermes runs through its private Python 3.14 shebang. The image exposes only its `hermes` launcher on the platform PATH; `python3` and `agent-sandbox-server` continue to use the server environment. For local direct `python3 commands.py` development, select the environment with agent-sandbox-server installed; placing the entire Hermes venv first on PATH would select a different interpreter.

## Express feasibility

Feasible: slice

Limiting factor: only local terminal and file tools are provisioned; optional gateways/browser/desktop backends require separate setup

The selected coding workload needs no Docker, KVM, root or extra capabilities inside the sandbox.
Image builds, rootfs fit and cloud acceptance require their own checks; local CLI installation does not prove them.

## Risks

Upstream v0.22.1 `hermes chat` submits accepted work to a detached canonical gateway and
separate managed-worker process groups. `command_timeout` terminates only the CLI and
its owned process group, not accepted authority work. A client HTTP timeout also does not
cancel it. Destroy the sandbox to stop the whole workload. This template does not expose
or claim verified per-session gateway interruption. The gateway auto-starts with upstream
idle-exit behavior; the default idle window is 600 seconds and excludes active work.
Messaging adapters are not provisioned, but the internal gateway is necessary for this CLI.
Sources: [transport lifecycle](https://github.com/NousResearch/hermes-agent/blob/297552a9d646119871391d202509822cd86330df/hermes_cli/gateway_client.py),
[idle exit](https://github.com/NousResearch/hermes-agent/blob/297552a9d646119871391d202509822cd86330df/gateway/run_idle_exit.py),
[managed workers](https://github.com/NousResearch/hermes-agent/blob/297552a9d646119871391d202509822cd86330df/gateway/session_managed_worker.py).

--yolo automatically approves tool actions, including shell execution. Run only in a dedicated sandbox. The pinned source retains its MIT license. Its Python 3.14 environment is separate from the server Python. Runtime plugin/tool downloads remain upstream behavior, and optional tools are excluded from the selected toolsets.
Secrets are declared with empty values. Error/output paths redact known secret environment values.

## Test plan

- L0: `python3 scripts/check_template.py hermes-agent`; `python3 -m pytest -q hermes-agent/test_commands.py`; local HTTP `e2e_test.py`, model disabled.
- L1: image build and pinned upstream version/dependency output; Docker is required.
- L2: `python3 scripts/express_e2e.py hermes-agent` invokes declared no-key smoke through external CLI and SDK. Only passing runs become provider evidence.
- L3: target diagnostics must report compatible credentials. Repair seeded `calculator.py`, preserve the seeded test, create REPORT.md and acceptance.txt with an exact ABX_E2E_OK marker, retrieve via remote files API, execute independent unittest and held-out tests. Required mode fails on missing credentials.
- L4: no provider claim until a real run.

Primary protocol/source reference: [Hermes Agent](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df).


### Premature-exit acceptance guard

The current coding controller imports trusted standard-library code under `python3 -I`, compiles the actual calculator and original-test source bytes, and requires exactly all three original tests to succeed without skips, expected failures or unexpected successes. Each test/held-out process must return a fresh completion acknowledgment generated after the model response; it is never included in the model prompt. Premature `SystemExit`, `os._exit(0)`, a static `INDEPENDENT_OK` string and stale bytecode cannot supply that acknowledgment. This protects ordinary acceptance against premature exits; it is not a security boundary against hostile Python with the same OS authority. Historical model runs retain their original controller hashes and do not prove this new gate; record a separate actual model run at the new controller revision on the reviewed image. Canonical deployment/provider qualification remains a separate required gate.

Current-version acceptance on 2026-10-20: version 1.1.1 genuine image READY/CLI/SDK and 17 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion. Independently verified sandbox/template/registry cleanup. Historical pending statements describe earlier checkpoints; see the current [Verified table](../../hermes-agent/README.md#verified).
