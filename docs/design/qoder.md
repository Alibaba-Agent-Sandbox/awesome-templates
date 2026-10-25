# qoder

## Purpose

Run the real Qoder coding assistant headlessly against files in a sandbox. The existing `qoder_run` Python script command remains available.

## Capabilities

Typed named commands on port 9000. `WORKSPACE=/home/user/app`. `QODER_PERSONAL_ACCESS_TOKEN` is required for model execution; browser/OAuth login is never started. `accept_edits` auto-approves file edits; upstream rejects shell confirmations. Sessions are not persisted and automatic updates are disabled.

## Exposed API

`qoder` returns a buffered string. Parameters:

- `prompt` (string, required): Task text; nonempty.
- `cwd` (string, ""): Existing directory; relative paths resolve under WORKSPACE.
- `command_timeout` (integer, 600): Execution deadline, 1–1800 seconds.

Upstream call: `qodercli --print PROMPT --output-format json --permission-mode accept_edits --no-session-persistence --settings '{"general":{"enableAutoUpdate":false}}'`.

- `qoder_version` (none): Installed CLI version.
- `qoder_setup_check` (none): Read-only installed/version/PAT-presence diagnostic.
- `qoder_run` (script: string = main.py): Local Python stdout; does not call Qoder.

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../qoder/Dockerfile) uses the Alibaba generation-2 base, non-root user,
2048 MB and `/home/user/app`. Qoder CLI `@qoder-ai/qodercli@1.1.72`; platform Python 3.13 / Node.js 20; Agent Sandbox server.
The Dockerfile installs published `agent-sandbox-server==0.4.0a4` directly.
`start_cmd`: `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`.
`ready_cmd`: `agent-sandbox-server healthcheck --port 9000`.
No CMD or ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: none

The selected coding workload needs no Docker, KVM, root or extra capabilities inside the sandbox.
Image builds, rootfs fit and cloud acceptance require their own checks; local CLI installation does not prove them.

## Risks

Qoder may edit workspace files. Shell confirmations are denied. A Qoder PAT is provider-specific; an OpenAI-compatible API key cannot replace it.
Secrets are declared with empty values. Error/output paths redact known secret environment values.

## Test plan

- L0: `python3 scripts/check_template.py qoder`; `python3 -m pytest -q qoder/test_commands.py`; local HTTP `e2e_test.py`, model disabled.
- L1: image build and pinned upstream version/dependency output; Docker is required.
- L2: `python3 scripts/express_e2e.py qoder` invokes declared no-key smoke through external CLI and SDK. Only passing runs become provider evidence.
- L3: target diagnostics must report compatible credentials. Repair seeded `calculator.py`, preserve the seeded test, create REPORT.md and acceptance.txt with an exact ABX_E2E_OK marker, retrieve via remote files API, execute independent unittest and held-out tests. Required mode fails on missing credentials.
- L4: no provider claim until a real run.

Primary protocol/source reference: [Qoder](https://docs.qoder.com/cli/run-in-scripts).
