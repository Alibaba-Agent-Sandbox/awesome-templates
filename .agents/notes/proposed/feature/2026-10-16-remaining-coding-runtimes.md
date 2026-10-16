# Decision: Complete Qoder, DeepSeek and Hermes coding runtimes

Status: proposed

## Problem

The Qoder migration stopped before documentation and acceptance coverage were complete.
DeepSeek performed one text completion without executing tool calls. Hermes advertised an
agent while invoking only a model API, with no upstream agent installed. All three retained
legacy template anatomy or stale public installation examples.

## Decision

- Complete Qoder with the actual npm CLI `@qoder-ai/qodercli@1.1.72`, PAT-only headless
  execution, `accept_edits`, disabled session persistence/updates, process-group cancellation,
  output redaction and a read-only setup check. Preserve `qoder_run` as local Python compatibility.
- Implement a repository-owned DeepSeek Chat Completions tool loop using `httpx==0.28.1`.
  Provide read/write/list/shell tools, structured assistant/tool messages, bounded turns and
  a worker execution deadline that terminates its process group. File tools reject traversal
  and symlink escapes. Shell tools execute with sandbox-user authority and a credential-filtered
  environment; they are not a security boundary against arbitrary sandbox file access.
- Install actual NousResearch Hermes Agent v0.22.1, immutable commit
  `297552a9d646119871391d202509822cd86330df`, using a separate Python 3.14.6 environment,
  pinned uv 0.12.3 and upstream frozen uv.lock. Use the upstream install-stamp writer for
  provenance. Expose its local `terminal,file` slice through `hermes chat -Q --yolo -q`.
  Keep optional messaging, browser and desktop systems outside this slice.
- Bring all three directories to spec_version 2 on the Alibaba base, generation 2, non-root
  user, 2 vCPU/2048 MB and explicit start/readiness commands. Add bilingual READMEs and
  design analyses. Provider verification lists remain empty until real provider evidence exists.

## API Design

Existing command names remain: `qoder_run(script)`, `deepseek(prompt, model)`, `hermes(prompt,
model)` and the DeepSeek/Hermes `run(script)` compatibility commands. New commands expose
CLI versions, read-only setup diagnostics and DeepSeek tool names.

Qoder adds `qoder(prompt, cwd="", command_timeout=600)`. DeepSeek and Hermes add cwd,
`max_turns=20` (1..100), `command_timeout=600` (1..1800), and Hermes provider selection.
`model=""` selects environment configuration. DeepSeek's obsolete `deepseek-coder` default
is replaced with the current documented `deepseek-flash` default. Hermes requires an explicit
model or HERMES_MODEL and returns upstream CLI output instead of a fabricated model wrapper.
Missing credentials fail before interactive login or model requests. Hermes v0.22.1 delegates accepted turns to a detached authority and separate managed-worker groups: its timeout only bounds the CLI and its owned group, not accepted gateway work. Whole-workload termination requires destroying the sandbox; this template does not provide verified per-session gateway interruption.

All named commands return buffered strings/dictionaries through the existing result envelope;
HTTP waiting time and command execution deadlines have distinct parameter names. Model acceptance uses E2E_COMMAND_TIMEOUT (default 600, range 1..1800) and a client wait budget 30 seconds longer. Failure reports expose only fixed deadline/provider-request/execution categories.

## Alternatives considered

Keeping the text-only completions would leave advertised coding behavior unimplemented.
A floating Hermes installer or native Qoder installer would undermine version reproducibility.
The full upstream Hermes image provisions unrelated privileged/services/browser functionality;
using its locked CLI source on the required base keeps the scoped coding slice explicit.

## Dependencies

- [Qoder scripting protocol](https://docs.qoder.com/cli/run-in-scripts) and
  [PAT authentication](https://docs.qoder.com/cli/authentication).
- [DeepSeek tool-call protocol](https://api-docs.deepseek.com/guides/tool_calls/).
- [Pinned Hermes source](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df),
  particularly pyproject.toml, uv.lock, hermes_cli/_parser.py and scripts/write_install_stamp.py.
- The pinned python-sdk server archive or an explicitly injected review wheel.
- Shared catalog/CI integration is coordinated separately in the same repository change.

## Test Strategy

Command regressions execute real local scripts/file tools, inspect argument vectors,
check missing-key/read-only behavior and secret redaction, simulate tool-call HTTP rounds,
and verify worker/process-group cleanup on success, nonzero exit and timeout. Leaders remain unreaped via Linux waitid(WNOWAIT) until owned-group cleanup, preventing PID/PGID reuse during cancellation. DeepSeek worker cancellation unwinds active shell groups before bounded forced shutdown. Acceptance-protocol regressions execute
real isolated Python verification commands while faking only transport/model actions. They
reject response-only markers, modified tests, held-out failures and startup/stdlib shadows.

L0 uses the owning local runner. Real model acceptance seeds failing source/tests, retrieves
changed source and new artifacts through the target HTTP files API, preserves original tests,
and independently executes unittest plus held-out inputs. Native provider and compatible
model acceptance are recorded separately. Image and cloud checks remain independent gates.

## Acceptance criteria

- All three scoped spec checkers, command/protocol regressions and L0 suites pass.
- Real Qoder and Hermes CLI versions match pinned upstream releases.
- DeepSeek tools complete a real compatible-model coding task; Hermes executes its actual
  upstream CLI against a real compatible model, including independent artifact/tests checks.
- Qoder product L3 requires a Qoder PAT; native DeepSeek L3 requires a native provider key.
- Hermes gateway work cancellation is not delivered by the CLI-group deadline and remains an explicit limitation/follow-up.
- Image/L1, Express/L2 and required remote review/merge gates remain outstanding when blocked;
  no local result is represented as cloud deployment or merged completion.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-remaining-coding-runtimes.md).
