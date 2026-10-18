# claude-code

[中文](README.zh-CN.md)

## What it does

Runs the pinned Anthropic Claude Code CLI through the named `claude` command.
The agent can edit a project and produce files in its workspace. A completed
text response alone does not prove that a coding task succeeded; download the
files and run project tests independently.

## Stack

Alibaba runtime base (Python 3.13 and Node 20), Claude Code **2.0.76**, and
`agent-sandbox-server` pinned to python-sdk commit
`35da216a300f1e2e84254a1cf4b4a7ea98681505` unless the deploy CLI injects a wheel.
Claude Code 2.0.76 supports Node >=18. No extra Node installation is needed.
`commands.py` is copied after the install layers so edits can reuse those layers.

## Problem solved

Provides a reproducible headless coding environment with one command contract
across the CLI, Python SDK, and HTTP. Generated artifacts remain accessible via
the files API, while process and terminal routes are provided by the server.

## Quick start (CLI)

```bash
abx template install alibaba-agent-sandbox/awesome-templates//claude-code
# Use the template id returned by installation. Inject the existing key at creation.
abx create --template <template-id> --env ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
abx run <sandbox-id> claude_version
abx run <sandbox-id> claude --arg prompt='Create hello.py that prints hello'
abx run <sandbox-id> claude --json-args '{"prompt":"Fix calculator.py and run its tests","cwd":"project","allowed_tools":"Read,Edit,Write,Bash(python3:*)","command_timeout":300}'
```

Create `project` first with the files or shell API. Keep shell tracing disabled
when injecting credentials. Use the environment's secret injection mechanism
where available; command-line arguments may be visible to local processes.

## Quick start (Python SDK)

The client distribution is `agent-sandbox-client` (import `agent_sandbox`). Until the matching release is available, use the [paired, pinned source installation](../docs/python-client-installation.md).

```python
import asyncio
import json
import os
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=600,
        envs={"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]},
    )
    try:
        result = await sb.run("claude", prompt="Create hello.py that prints hello", timeout=420)
        print(json.loads(result)["result"])
        print(await sb.files.read("/home/user/app/hello.py"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` returns the command's result value, a JSON **string** for `claude`.
`sb.run(timeout=...)` controls the HTTP timeout; `command_timeout` controls the CLI deadline. It is a buffered response; use the process streaming API for live CLI stdout.

## Quick start (HTTP POST)

```bash
curl --request POST "$SANDBOX_SERVER_URL/commands/claude" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --max-time 420 \
  --data '{"prompt":"Create hello.py that prints hello","command_timeout":300}'
```

Set `SANDBOX_SERVER_URL` to the sandbox's port 9000 URL. Omit the Authorization
header when server authentication is unset. HTTP 200 is `{"result":"<upstream JSON>"}`;
400 means invalid arguments, 401 authentication failed, and 500 command failure.
The 300-second CLI deadline is independent of the 420-second HTTP deadline.
A client timeout does not prove that the upstream process stopped.

## Command reference

| Command/parameter | Type/default | Behavior |
|---|---|---|
| `claude_version()` | no arguments | Installed CLI version; no key or model call. |
| `claude.prompt` | required string | Prompt passed as a separate argv element. |
| `claude.model` | string, `sonnet` | Upstream model name or alias. |
| `claude.cwd` | string, empty | Existing directory inside `WORKSPACE`; relative or absolute. Symlink escapes rejected. |
| `claude.allowed_tools` | string, `Read,Edit,Write` | Claude tool permission rules; shell commands require explicit permission. |
| `claude.resume` | string, empty | Optional upstream session id. |
| `claude.command_timeout` | integer, `300` | 1–900 seconds; set the client request timeout higher. |

Equivalent raw HTTP request to the sandbox's port 9000 URL:

```http
POST /commands/claude
Content-Type: application/json

{"prompt":"Create hello.py that prints hello","model":"sonnet","cwd":"","allowed_tools":"Read,Edit,Write","command_timeout":300}
```

HTTP 200 wraps the string as `{"result":"<upstream JSON>"}`. Missing or mistyped
parameters return HTTP 400. Non-zero CLI exit, timeout, invalid JSON, and an
upstream `is_error` result return HTTP 500 with sanitized diagnostics. The
command never returns a non-zero exit as success. `GET /commands` describes the
live parameter schema. This endpoint is buffered, not SSE.

## Configuration

| Environment name | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Required inside the sandbox for model calls; inject at creation. |
| `WORKSPACE` | Command working directory root; default `/home/user/app`. |
| `ABX_SERVER_TOKEN` | Optional named-command server authentication, injected at creation. |
| `E2E_RUN_LLM` | `0` skips the real agent case; `1` requires its host-side key check. |
| `E2E_REQUIRE_LLM` | `1` fails on missing key or a forced skip. |
| `E2E_MODEL` | Optional model override for acceptance. |

`--permission-mode dontAsk` denies tools requiring approval unless permitted by
`allowed_tools` or upstream settings. The wrapper never enables blanket
permission bypass. These rules and `cwd` validation are not OS isolation: the
agent runs as sandbox `user`, and allowed Bash can access that user's files,
network and injected credentials. Use disposable sandboxes and only necessary
credentials; do not mount host secrets or run untrusted prompts alongside them.
Do not log model output indiscriminately: it can contain workspace data. The
wrapper suppresses upstream stderr and exception payloads, and redacts known
secret environment values from successful JSON output.

With `ABX_SERVER_TOKEN`, raw HTTP needs `Authorization: Bearer <token>` or
`X-Access-Token: <token>`. For the SDK use
`await sb.server_at(9000, token=os.environ["ABX_SERVER_TOKEN"]).commands.run("claude", prompt="...", timeout=420)`.
The sandbox gateway token and this server token are separate credentials.

## Resources

2 vCPU, 2048 MB; no GPU, Docker, KVM, or privileged capabilities. Model calls
require outbound access to Anthropic and consume the account's model budget.
See [upstream CLI reference](https://code.claude.com/docs/en/cli-reference)
and [headless usage](https://code.claude.com/docs/en/headless) for tool rules.

## Verified

No provider has a passing run recorded for this template.

## Secondary development

Change `commands.py` and keep prompts as argv. Change the exact npm version in
both the Dockerfile and smoke expectation when upgrading. Do not bake secrets
into layers. Local checks from the repository root:

```bash
python3 scripts/check_template.py claude-code
python3 -m unittest discover -s claude-code/tests -v
python3 scripts/run_local_e2e.py
```

L0 skips model calls. L1 requires an actual image build; L2 requires deployment
and external CLI/SDK smoke calls. For L3, run `e2e_test.py` against the created
sandbox with `E2E_REQUIRE_LLM=1`, `E2E_RUN_LLM=1`, and its URL/token plus the
host-side key configured without printing it. The suite seeds a broken project,
requires a real agent edit and new artifact/report files, preserves test sources,
and independently runs two unit tests. It cleans up only its own unique files,
processes and PTY sessions. Missing credentials are a failure in required mode.
Only record provider evidence after the corresponding real run passes.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md) and the [template spec](../docs/template-spec.md).

## Issues

Report template problems to [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).
SDK/server problems go to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)
and CLI problems to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues),
with the `[templates]` prefix. Search existing issues and redact credentials.

## License

Apache-2.0 for this template. Claude Code has its own upstream terms.
