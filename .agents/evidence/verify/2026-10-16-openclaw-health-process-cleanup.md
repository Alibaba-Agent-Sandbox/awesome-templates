# OpenClaw short-lived health-RPC process cleanup

Date: 2026-10-16
Result: PARTIAL

## Scope and decision

Base HEAD: `2acb53481739e9585803076dd4c05ce5c2048219` plus uncommitted
`openclaw/{commands.py,test_commands.py,README.md,README.zh-CN.md}`,
`docs/design/openclaw.md` and the owner note/evidence. Main gateway ownership,
WNOWAIT status observation and long-running lifecycle are unchanged.

Only the short-lived gateway-health probe now uses the independently reviewed
owned-process helper: concurrent stdout/stderr readers, Linux waitid(WNOWAIT)
until final group cleanup, cleanup after success/nonzero exit and timeout, then
leader reap. Its own group is distinct from the gateway's group. RuntimeError
from the bounded probe becomes false health, preserving the existing public
contract. It never signals arbitrary PID files or a process deliberately escaped
outside its group with setsid. The template remains Linux-specific.

## Actual verification

Environment: Linux x86_64, Python3.13.13/source-built server0.3.0,
pytest9.1.1/httpx0.28.1, official SHA256-verified Node24.16.0 and actual pinned
OpenClaw2026.10.4 in temporary installation prefixes. No model credential was
injected. Synthetic gateway/server tokens were generated in process and omitted
from output/evidence.

- PASS: `python -m pytest --import-mode=importlib -q openclaw/test_commands.py`,
  exit0,22passed. Existing15gateway ownership tests still pass. Four new actual
  helper process scenarios cover successful/error leaders with ready-synchronized
  redirected descendants, timeout leader/TERM-ignoring child, and200KB stdout and
  stderr drain. Three direct `_probe` actual-process regressions exercise
  success,nonzero,timeout against a private executable fixture: no descendant
  marker survives and the independently running gateway process remains alive.
  No killpg/waitid mock substitutes for these process behaviors.
- PASS: real HTTP server plus actual OpenClaw CLI with independent fresh server/
  gateway tokens and unique local ports ran `python openclaw/e2e_test.py`:
  exit0,11PASS,model/codingSKIP. Authenticated readiness/RPC health, continued
  gateway after start response, owned stop, absent health after stop, precise
  HTTP errors and server shell all passed after the helper change.
- PASS: `python scripts/check_template.py openclaw`, exit0,conformant.
- PASS: scoped diff whitespace and relative Markdown-link checks,exit0.

## Remaining gates and cleanup

This host CLI/HTTP run is not L1 image or L2 current-image deployment acceptance.
Docker is unavailable, so both remain blocked. Gateway lifecycle does not run a
model and no L3 coding acceptance is claimed. No L4,provider pass file or
tested_on provider was added. Existing local/runtime JSON is historical evidence
for its recorded source, not a new image pass. Full integration CI/L0,owner
Issue/PR/review and verified merge remain coordinating-task work.

The actual gateway was explicitly stopped; its HTTP server was terminated/reaped.
Regression groups were cleaned and temporary fixture gateways were stopped in
finally. No cloud resource was created. No commit/push/publication is claimed.

## Tested source hashes

| File | SHA256 |
|---|---|
| `openclaw/commands.py` | `7dd8aed4b1c1f82b195f110e93a8c361ab2a87e60540f25b1028caa4f913096a` |
| `openclaw/test_commands.py` | `93345364d7e101bc3710cdaad8cc58a0fd6bec8e7412252f7f0d94fdc2e02e76` |
