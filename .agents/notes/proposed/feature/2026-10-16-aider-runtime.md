# Decision: Pin Aider in a compatible runtime with explicit selected-file writes

Status: proposed

## Problem

Market Issue 50 has no template. A marker or substitute HTTP model client would not
prove Aider works. Current official PyPI 0.86.2 rejects the base Python 3.13, while
its default home/project configuration search can import caller state despite
explicit config flags. Default editing and unowned child processes would make an
unattended endpoint unsafe and difficult to clean up.

## Decision

Create spec2 experimental `aider/` on Alibaba base with a separate SHA256-pinned
Python 3.12.12 venv and exact aider-chat 0.86.2. Keep server wheel source fixed and
base Python/Node unchanged. Run actual CLI argv with a private message file and
explicit compatible-model settings. Require existing git cwd, explicit relative
file selection, read-only ask by default and allow_write for whole-file edits.
Stage only selected files, reject symlinks/config paths, recheck original bytes
and atomically replace selected outputs after successful CLI completion.
Disable upstream automatic confirmation explicitly: selected stage files already
exist, while unselected file creation/edit requests must be declined before touch.
Config false alone leaves the pinned store_true state unset and EOF means Yes;
an owned continuous No input feeder supplies refusals until exit, then joins
after process-group cleanup.
Prefix message-file text so slash/bang input cannot dispatch upstream commands.

Never replace HOME or alter shared profiles. Refuse native default home config,
model metadata/settings and OAuth keys before launch; disable dotenv loading.
The verified upstream has no official home/config-dir isolation switch; explicit
--config/--env-file append rather than disable defaults. Actual CLI/model runs
therefore use a fresh owned sandbox with its unmodified native home. Upstream
cache/state remains only within that disposable resource. The Linux owned-process
runner reuses the established WNOWAIT design; timeout, leader exit and cancellation
clean its group without reaping the PID/PGID too early. No new shared dependency.

## API Design

`aider_version() -> str`, `aider_setup_check() -> dict` and
`aider(prompt: str, cwd: str="", files: str="[]", allow_write: bool=False,
command_timeout: int=600) -> dict`. Complete types, limits, output and errors are
in both template READMEs and `docs/design/aider.md`. Command and client HTTP
timeouts are distinct; an HTTP disconnect does not itself cancel the process.

Create-time envd settings do not update a prewarmed named-command server. Start
an owned process from the installed image commands with explicit SDK
commands.start(env=...) on port 9010, consume its stream, and use that port in
CLI/SDK/HTTP. Confirm target setup before calling a model; do not copy source
over the deployed image or rely on host-only credential visibility.

## Alternatives considered

- Install into base Python 3.13: incompatible with official package metadata.
- Set HOME to an ephemeral profile: rejected by the current session constraint.
- Trust --config/--env-file to disable home search: contradicted by pinned source
  and required actual hostile-default negative control.
- Run a direct OpenAI request instead: would not exercise the upstream product.
- Copy the whole repo: unnecessarily imports private/configuration files.
- Count a response marker as coding: independent tests and target artifacts are
  required, with false-acceptance negative controls.

## Dependencies

Existing server wheel contract and existing owned-process design from Pi; official
Aider 0.86.2 and standalone Python 3.12.12. [Issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50).
This PR stacks on [Pi PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86),
without editing its product or shared workflow implementation.

## Test Strategy

Unit guards, actual subprocess cancellation/descendant cleanup, stale-original/
symlink rejection, redaction, ephemeral message cleanup, typed server L0 and
controller negative controls for marker-only, modified tests and held-out failures.
Actual owned Express install/help and home-config negative control precede real
Qwen-compatible ask/coding. L3 requires existing source change, new report/exact
artifact, preserved tests, remote retrieval and independent held-out execution.
The new context receives actual image CI. All failed/unrun tiers remain explicit.

## Acceptance criteria

- Static/catalog/spec gates, scoped regressions and local HTTP smoke execute.
- Official pinned CLI/help and real source coding pass with owned cleanup.
- Latest-head actual image build/non-root smoke passes before L1 is claimed.
- Full image deployment/READY L2 stays unclaimed until actually verified; status
  remains experimental and Issue 50 stays open for incomplete acceptance.
- Bilingual full API/contribution docs, design, local records and an independent
  draft PR carry exact source and environment boundaries.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-aider-runtime.md).
