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

Template1.0.1 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../aider/Dockerfile) retains the Alibaba FC base, non-root user,
port 9000 and generation 2 server commands. Official PyPI metadata for
[aider-chat 0.86.2](https://pypi.org/project/aider-chat/0.86.2/) requires Python
`>=3.10,<3.13`, while base Python is3.13. A separate official
[python-build-standalone 20260211](https://github.com/astral-sh/python-build-standalone/releases/tag/20260211)
3.12.12 archive is pinned by architecture-specific API asset SHA256 and extracted
with safe tar handling. Aider installs in its own venv; server continues on base
Python 3.13 using published server package 0.4.0a6. Node20 is unchanged
because Aider has no Node requirement. Installed licenses are preserved.

Metadata-only Python 3.11 resolution found 108 distributions, all compatible wheels,
118 MiB compressed total (scipy35.9, tree-sitter-language-pack19.0, numpy17.4,
litellm13.8 MiB). Python x86-64 archive is32.3 MiB compressed. These are not measured
installed or image sizes. No full dependency download is made on the constrained
shared host; a fresh owned Express runtime handles the real install.

## Express feasibility

Feasible: yes

Limiting factor: upstream Python compatibility requires the separate3.12 runtime.
2 vCPU/2 GiB, native user, no Docker/KVM/extra capabilities and egress suffice for the
selected-file CLI workflow. A model credential and compatible endpoint are
required. Source-runtime verification does not establish a deployed template image.
Current source-launch acceptance requires its own exact-input L2 receipt. Server package version is fixed independently of Aider's environment.

## Risks

Official Aider 0.86.2 `main.py` always appends native `Path.home()` defaults;
configargparse 1.7.1 opens default files before user `--config`. `--env-file` also
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
The message file starts with a fixed literal-text prefix, preventing upstream
slash/bang commands from interpreting user prompts as shell or file-add commands.
Explicit `yes-always: false` removes automatic Yes, but official configargparse
store_true maps false to no argv and leaves yes=None; Aider treats EOF as the
default Yes. Therefore the owned stdin feeder continually supplies No until CLI
exit, then joins after group cleanup. This refuses create/edit requests for
unselected absolute or parent-relative paths before touch/write. All selected
paths are precreated in stage. These controls require actual installed-CLI loopback negative
controls in addition to unit argv assertions. Artifact state, successful model
invocation and the positive selected edit are the authority; outside paths may
be rejected earlier by upstream git checks without a particular refusal message.
Do not infer that every external-path test reached the No confirmation feeder.
Reject symlinks/traversal/config paths and detected stale originals before writeback.
Per-file atomic replacement preserves old mode; a multi-file change is not a
transaction. Uncooperative external writers are outside the concurrency guarantee.

Linux WNOWAIT holds the owned session leader unreaped until group cleanup,
preventing PID/PGID reuse before kill. Deadline, leader exit and Python cancellation
kill only that group; profile cleanup is in the surrounding context manager.
HTTP client disconnect does not itself cancel a named command. Never delete an
unrelated provider resource or shared home state during cleanup.

The Express named-command server may already be running before create-time envd
settings apply. `Sandbox.create(envs=...)` does not retroactively configure that
process. Start a new owned instance of the already installed server on port 9010
with public `commands.start(env=...)`, consume its stream, and use actual SDK
`server_port=9010`, CLI `--server-port 9010` and the 9010 HTTP URL. Confirm the
target setup booleans through all three clients before model acceptance. Do not
replace commands.py or change HOME. Kill the owned sandbox and close the stream.

Actual configured-image evidence now records official READY, exact command and
56-module server provenance, SDK/HTTP/CLI configuration, real upstream guards,
and qwen3.8-flash coding: 21 PASS / 0 FAIL / 0 SKIP with independent target tests
and retrieved artifacts. See [the immutable run](../../aider/evidence/image-runtime-2026-10-16-configured.json).
The first failed image run is retained. Those dated image/model results do not substitute for current source-launch verification.

## Test plan

L0: actual server HTTP registry/types/400/404/missing-configuration smoke and
unit positive/negative guards. CLI absence is explicit SKIP, not acceptance.
L1: actual Docker image CI must install fixed Python/Aider, non-root server package,
and execute real `aider_version`. L2: deployment READY plus SDK/CLI smoke is required
before listing a verified provider. L3: qwen3.8-flash compatible route in a fresh
owned source runtime; baseline three independent tests fail, real Aider changes
calculator.py and creates REPORT.md plus an exact ABX_E2E_OK artifact, original
test bytes stay unchanged, remote file retrieval and three tests plus six held-out
calculations pass. Marker-only/modified-tests/held-out failures must be rejected.
No source-runtime pass is reported as an image deployment. L4 other providers
remain unverified. Every owned resource is destroyed even on failure.

## Independent verifier completion

The first controller's static held-out marker could be printed by target source
before sys.exit(0), bypassing the assertions while leaving the original three
tests passing. Isolated source-compiling verifier processes now require the exact
three-test successful result without skips/expected failures, plus fresh separate
post-agent completion acknowledgements. Actual source bytes bypass stale caches;
trusted stdlib loads before adding the project. This is completion verification,
not a hostile same-authority isolation claim. Runtime/CLI policy is unchanged.

The hardened host controller `f76687e` subsequently ran against the same immutable
`ecbabaf` image: 21 genuine qwen3.8-flash checks passed, with zero failures/skips;
all seven owned-resource cleanup flags and an independent strict official
exact-template absence check passed. See the separate
[recheck evidence](../../aider/evidence/image-runtime-hardened-2026-10-16.json).
This does not rerun or replace historical evidence and does not satisfy canonical
L2 deployment. Runtime commands, template configuration and HOME were unchanged.

Current-version acceptance on 2026-10-20: version 1.0.1 genuine image READY/CLI/SDK and 21 strict real-model assertions (qwen3.8-flash, OpenAI-compatible), source edit/new artifact/unchanged original tests/independent held-out completion. Independently verified sandbox/template/registry cleanup. Historical pending statements describe earlier checkpoints; see the dated [2026-10-20 receipt](../../aider/evidence/express-2026-10-20.json).
