# Amp, Droid and Gemini owned-process completion cleanup

Date: 2026-10-16
Result: PARTIAL

## Scope and reproduced defect

Base HEAD: `2acb53481739e9585803076dd4c05ce5c2048219`, plus scoped uncommitted
`amp/`, `droid/`, `gemini/` commands/tests, bilingual README/design updates and
existing feature-note follow-ups. Earlier completion-review evidence remains
unchanged and refers to its previous source hashes. This follow-up changes the
subprocess implementation; earlier cloud source-runtime checks do not establish
these new source hashes.

Before the fix, an actual Python leader launched a child with stdin/stdout/stderr
redirected to DEVNULL, printed its result and exited0. Each old wrapper returned
success without cleaning its group. After a delay the child wrote its marker:
reproduced independently for all three templates. This is an observable resource
leak, not a hypothetical model assertion. The old communicate timeout path could
also reap the leader before group cleanup, losing the PID identity anchor.

## Decision and implementation

Copied the independently reviewed standalone runner from Qoder into each image's
commands.py; no cross-template imports were added. Linux waitid(WNOWAIT) observes
the leader without reaping it. Concurrent readers drain both pipes. Normal and
nonzero completion kill the owned group before reaping; timeout first sends TERM
with a bounded grace then KILL, still retaining the leader identity. Each public
wrapper keeps its existing API, upstream error/redaction rules, environment and
template-specific timeout message. Only groups created by this invocation are
signalled. Descendants that deliberately detach outside that group remain outside
this cancellation contract.

## Environment and actual validation

Linux x86_64, Python3.13.13, source-built agent-sandbox-server0.3.0,
pytest9.1.1/httpx0.28.1/PyYAML6.0.3. Real pinned Amp/Droid/Gemini CLIs remained on
temporary PATH for keyless diagnostics. Temporary test projects use synthetic
markers and child programs only; model credentials are not injected.

- PASS of reproduction: a temporary local driver ran the old public process
  wrappers with actual redirected children, exit0, and observed surviving child
  markers for all three templates before editing the runner.
- PASS: `python -m pytest --import-mode=importlib -q amp/test_commands.py droid/test_commands.py gemini/test_commands.py`,
  exit0,45passed. Includes12new actual-process scenarios: exit0/7 leaders with
  ready-synchronized redirected descendants, deadline leader exiting on TERM with
  a TERM-ignoring descendant, and200KB each stdout/stderr without deadlock.
  Existing secret redaction and private-argv timeout regressions still pass.
- PASS: each template's `scripts/run_local_e2e.py::_run_one` with ordinary
  credential-sanitized environment and real pinned CLIs: all three `pass` and
  driver exit0. Amp7PASS/1modelSKIP, Droid9PASS/L3NOT RUN, Gemini9PASS/modelSKIP.
- PASS: `python scripts/check_template.py amp`, `droid`, `gemini` (separate
  invocations): each conformant/exit0. agents-cli checker also remained conformant.
- PASS: scoped `git diff --check` and relative document-link validation, exit0.
- PASS: combined regression suite across these templates, OpenClaw and agents-cli,
  `python -m pytest --import-mode=importlib -q amp/test_commands.py amp/test_e2e_protocol.py droid/test_commands.py droid/test_e2e_protocol.py gemini/test_commands.py gemini/test_e2e_protocol.py openclaw/test_commands.py agents-cli/test_protocol.py`: exit0,111passed at this checkpoint. The later OpenClaw probe cleanup has its own evidence and rerun.

## Required acceptance still open

These are host subprocess and local HTTP checks. No Docker executable/engine
was available for L1, no current-image L2 provider deployment was performed,
and no real-model coding L3 was run. No provider evidence or tested_on entry was
added. Earlier Express source-runtime checks cover their recorded hashes only.
The integration owner must rerun any required source-runtime/CI checks against
the new source and complete Issue/PR/review/merge gates. Overall result remains
PARTIAL, not product/image/cloud/model completion.

All task-owned local HTTP servers were stopped/reaped; owned process groups were
cleaned by the runner. No cloud resource was created. Existing records remain
proposed and no commit/push/remote publication is claimed by this scoped work.

## Tested source hashes

| File | SHA256 |
|---|---|
| `amp/commands.py` | `908a900eb48d44120692d934c4a7e0b31c3b5acac73dd84827a10a9c6ec24122` |
| `amp/test_commands.py` | `4c658ff2af208d6edc80f9c12f1c0265569c605f6b31ee378e95993e0ef86175` |
| `droid/commands.py` | `b67e5b8ba50f1e2be6b3d094f806a112b4900999278e50535fb748aee0b66419` |
| `droid/test_commands.py` | `86f0e368ba900882db05d633258210cd8298cd724a00acc6210c070163eb4871` |
| `gemini/commands.py` | `f18cdf7d9e5409c6fbcb5e5a50fe0de168388d6542f906013940a407c4d9c228` |
| `gemini/test_commands.py` | `60360f38642cddedc5bd1af908ee2b4fb7a0f9785f40382c1d54a56c86695506` |
