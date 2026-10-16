# aider

## Purpose

A dedicated sandbox for real Aider code review and explicit selected-file editing.
Issue: [50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
The survey's old 0.86.0 assumption is replaced by verified official PyPI 0.86.2.

## Capabilities

Read-only ask is the default. The caller supplies an existing git working tree
and a JSON-encoded explicit file list. Only those files enter a disposable git
stage; project configuration, `.env` and Git metadata are not copied. Explicit
`allow_write=true` enables Aider whole-file editing and selected-file writeback
after original-byte and path revalidation. It creates real files, not a marker
response. No interactive terminal, automatic commit, arbitrary shell, browser or
full-repository agent session is exposed by the named command.

## Exposed API

- `aider_version() -> str`: real `aider --version`, expected `aider 0.86.2`.
- `aider_setup_check() -> dict`: installed/pinned/configured/home-blocked booleans
  and workspace. Never returns credentials or endpoint contents.
- `aider(prompt: str, cwd: str="", files: str="[]", allow_write: bool=False,
  command_timeout: int=600) -> dict`: stdout/stderr, zero exit_code and
  changed_files. Prompt length 1..100000, deadline 1..1800 seconds, at most 32
  files of 1 MiB each. Uses actual CLI `--message-file`, `--chat-mode ask|whole`,
  explicit model/settings/base/files and disabled commits/lint/test/browser/
  URL/shell suggestions/analytics/update flags. Nonzero upstream exit raises
  a generic exception without echoing private output. Named responses buffer;
  client HTTP timeout and transport disconnect do not imply process cancellation.

## How to build

[Dockerfile](../../aider/Dockerfile) retains the Alibaba FC base, non-root user,
port9000 and generation2 server commands. Official PyPI metadata for
[aider-chat0.86.2](https://pypi.org/project/aider-chat/0.86.2/) requires Python
`>=3.10,<3.13`, while base Python is3.13. A separate official
[python-build-standalone20260211](https://github.com/astral-sh/python-build-standalone/releases/tag/20260211)
3.12.12 archive is pinned by architecture-specific API asset SHA256 and extracted
with safe tar handling. Aider installs in its own venv; server continues on base
Python3.13 using source-built wheel or fixed SDK archivee2cb27e. Node20 is unchanged
because Aider has no Node requirement. Installed licenses are preserved.

Metadata-only Python3.11 resolution found108 distributions, all compatible wheels,
118MiB compressed total (scipy35.9, tree-sitter-language-pack19.0, numpy17.4,
litellm13.8MiB). Python x86-64 archive is32.3MiB compressed. These are not measured
installed or image sizes. No full dependency download is made on the constrained
shared host; a fresh owned Express runtime handles the real install.

## Express feasibility

Feasible: yes

Limiting factor: upstream Python compatibility requires the separate3.12 runtime.
2vCPU/2GiB, native user, no Docker/KVM/extra capabilities and egress suffice for the
selected-file CLI workflow. A model credential and compatible endpoint are
required. Source-runtime verification does not establish a deployed template image.
Catalog stays experimental and tested_on remains empty until actual named-template
L2 acceptance. Server wheel source is fixed independently of Aider's environment.

## Risks

Official Aider0.86.2 `main.py` always appends native `Path.home()` defaults;
configargparse1.7.1 opens default files before user `--config`. `--env-file` also
appends to dotenv search; neither flag disables that search. There is no official
AIDER_HOME/config-directory replacement. The wrapper never changes HOME and refuses
native `.aider.conf.yml`, `.env`, model-settings/metadata and OAuth-key defaults.
A source inspection and actual malicious-home-config negative control must prove
this boundary. Real local shared-home CLI/model calls are deliberately not run.
A fresh owned sandbox uses its unchanged native home; upstream cache/install and
analytics-disabled state may remain there until whole-instance destruction.

The child gets a small environment allowlist and only the selected model key;
PYTHON_DOTENV_DISABLED prevents dotenv refilling. Credentials are never serialized
into stage files or argv. Selected code and prompts still go to the configured
model endpoint. Staging is a workflow boundary, not a hostile-code security sandbox.
Reject symlinks/traversal/config paths and detected stale originals before writeback.
Per-file atomic replacement preserves old mode; a multi-file change is not a
transaction. Uncooperative external writers are outside the concurrency guarantee.

Linux WNOWAIT holds the owned session leader unreaped until group cleanup,
preventing PID/PGID reuse before kill. Deadline, leader exit and Python cancellation
kill only that group; profile cleanup is in the surrounding context manager.
HTTP client disconnect does not itself cancel a named command. Never delete an
unrelated provider resource or shared home state during cleanup.

## Test plan

L0: actual server HTTP registry/types/400/404/missing-configuration smoke and
unit positive/negative guards. CLI absence is explicit SKIP, not acceptance.
L1: actual Docker image CI must install fixed Python/Aider, non-root server wheel,
and execute real `aider_version`. L2: deployment READY plus SDK/CLI smoke is required
before listing a verified provider. L3: qwen3.8-flash compatible route in a fresh
owned source runtime; baseline three independent tests fail, real Aider changes
calculator.py and creates REPORT.md plus an exact ABX_E2E_OK artifact, original
test bytes stay unchanged, remote file retrieval and three tests plus six held-out
calculations pass. Marker-only/modified-tests/held-out failures must be rejected.
No source-runtime pass is reported as an image deployment. L4 other providers
remain unverified. Every owned resource is destroyed even on failure.
