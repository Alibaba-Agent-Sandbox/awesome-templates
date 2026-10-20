# claude-code

## Purpose

Run Anthropic Claude Code in an isolated project workspace through the same named
command from the CLI, Python SDK, and HTTP. The template owns the CLI wrapper;
the SDK owns sandbox lifecycle, files, processes, and terminal transport.

## Capabilities

Pinned headless Claude Code, workspace-scoped file editing, explicit tool
permissions, optional session resume, and artifact retrieval using the files API.
`claude_version` does not need a model key. A live coding task needs an Anthropic
credential; an OpenAI-compatible credential does not establish that capability.

## Exposed API

`GET /commands` provides the live argument schema. `POST /commands/claude_version`
accepts `{}` and returns a version string in `result`. `POST /commands/claude`
requires `prompt` (string). Optional arguments are `model` (string, `sonnet`),
`cwd` (string, empty, an existing directory within `WORKSPACE`), `allowed_tools`
(string, `Read,Edit,Write`), `resume` (string, empty), and `command_timeout`
(integer, 300, range 1–900 seconds). See the README for CLI and SDK equivalents.

The wrapper invokes `claude -p <prompt> --model <model> --output-format json
--permission-mode dontAsk --allowedTools <rules>` with an argv list and adds
`--resume` when requested. The result is the upstream JSON encoded as a string;
the server wraps it in `{"result": ...}`. A reported upstream error is an error
response. The client request timeout must exceed the CLI deadline.

## How to build

Template1.1.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../claude-code/Dockerfile) uses the Alibaba runtime base and pins
`@anthropic-ai/claude-code@2.0.76`, compatible with the base's Node 20. The server
uses a wheel injected by the CLI or the pinned python-sdk archive. Generation 2
starts `agent-sandbox-server serve --port 9000 --commands
/home/user/app/commands.py` and probes `agent-sandbox-server healthcheck --port
9000`. Runtime user is `user`; no Dockerfile CMD or ENTRYPOINT replaces the
platform startup. Command source is copied after dependency installs.

## Express feasibility

Feasible: yes

Limiting factor: none

The headless CLI needs no KVM, nested Docker, extra capabilities, or display.
The complete product fits the stated Express runtime. A model credential and
network access are execution prerequisites and must be checked before L3.

## Risks

`cwd` must remain inside `WORKSPACE`, including after symlink resolution.
Tool rules default to file operations; shell execution requires explicit rules.
Never place credentials in Dockerfiles, template metadata, test output, or
evidence. Nonzero exits and timeouts use bounded diagnostics. PTY tests delete
only the sessions whose ids they received when creating them. A successful
health/version check says nothing about a model's ability to modify code.

## Test plan

L0 starts the local server and exercises HTTP argument validation, command
listing, file operations, shell execution, and owned PTY cleanup. Regression
tests simulate external CLI behavior and verify workspace and error boundaries.
L1 builds the image and checks the pinned CLI version. L2 deploys a unique
template alias, creates an owned Express sandbox, invokes `claude_version`
through CLI and SDK, and cleans up both resources. L3 seeds a buggy calculator
with failing tests, asks the real agent to fix it and create a new artifact,
then independently verifies files and reruns the tests; matching a response
marker alone is insufficient. No provider is listed as verified before its
corresponding evidence exists. Other providers need their own L4 run.
