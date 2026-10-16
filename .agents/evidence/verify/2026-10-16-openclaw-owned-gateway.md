# OpenClaw owned gateway verification

Date: 2026-10-16
Result: PARTIAL

## Scope and environment

Base revision: `2acb53481739e9585803076dd4c05ce5c2048219` plus scoped working-tree
changes in `openclaw/`, `docs/design/openclaw.md`, `docs/usage-openclaw.md` and this
record/note. Linux x86_64, Python3.11 virtual environment with source SDK/server,
Node24.16.0 and npm10 in a separate temporary prefix. Installed upstream binary:
`OpenClaw 2026.10.4 (383c124)`.

## Commands and results

- `npm view openclaw version engines --json`: PASS, version2026.10.4 and engines
  `>=24.16.0 <25 || >=26.1.0`. A first npm `node@24.16.0` installation failed in
  this managed runtime's nested npm; direct platform package `node-linux-x64@24.16.0`
  installed successfully in the temporary prefix. No platform permissions changed.
- `npm install --prefix <temporary-prefix> openclaw@2026.10.4 --no-audit --no-fund`
  with pinned Node24 on PATH: exit0, real upstream CLI installed.
- `openclaw --version`, `openclaw gateway health --help`: exit0, version and actual
  gateway health argv/options confirmed.
- `python -m pytest openclaw/test_commands.py -q`: exit0, 15passed. Includes owned
  subprocess termination, stale PID does not kill unrelated child, living PID
  cannot pass authenticated health, and timeout cleanup.
- `python scripts/check_template.py openclaw`: exit0, conformant.
- Local temporary Python driver invoking `gateway_start(port=<ephemeral>, command_timeout=90)`,
  `gateway_health`, `gateway_status`, `gateway_stop` with real CLI: exit0. First
  authenticated startup took approximately11seconds. Gateway remained running
  after start returned and was stopped/reaped. Synthetic random token generated
  in process; no model key required or read.
- Local HTTP driver launched `python openclaw/commands.py` on an ephemeral port,
  injected independent random server/gateway tokens, then ran
  `python openclaw/e2e_test.py` with `E2E_BASE_URL` and an unused gateway port:
  exit0, 11PASS, model/coding SKIP. `/commands` rejected an anonymous request401;
  `/health` is public by current SDK contract. Tests asserted precise errors,
  actual authenticated readiness/health, continued background process, cleanup,
  failed health after stop and server shell.
- Initial HTTP harness assertions expected authentication on `/health` and
  ValueError on invalid integer coercion; both failed. Source inspection showed
  `/health` is intentionally public and coercion raises TypeError. The test was
  corrected to the real business-route401 and HTTP400/TypeError contracts and
  rerun successfully; no product gate was relaxed.
- `git diff --check -- openclaw docs/design/openclaw.md docs/usage-openclaw.md`:
  exit0 at the scoped review point.

## Outstanding gates

- L1 BLOCKED: Docker executable is unavailable in this environment. Local npm
  installation is not a Docker image build, non-root container or layer-size test.
- L2 BLOCKED by the image-build prerequisite; no Express template/image or provider
  was created by this task. `tested_on` remains empty and no provider pass is claimed.
- L3 NOT RUN: this gateway command set does not perform a model/coding task. No key
  was read from root `.env` and no model acceptance is inferred from gateway health.
- L4 NOT RUN: no additional provider acceptance.
- Full repository local suite and CI are coordinated by the parent task; this
  scoped test does not claim unrelated templates passed.
- Cross-review, Issue20 update, PR and merge are pending parent workflow.

## Cleanup and privacy

Drivers generated fresh synthetic tokens in memory, used unique localhost ports,
called owned gateway_stop in finally, terminated/reaped their HTTP server, and
removed private temporary state. No credential values, raw upstream logs or
root environment contents are retained. Dependency installation is confined to
temporary runtime directories.

## Cross-review fixes and final rerun

Independent Gemini reviewer found two real defects in the first implementation:
SDK `Sandbox.run` reserves `timeout`, and waiting only for the leader left a
TERM-ignoring same-group descendant alive. Public command parameters now use
`command_timeout`. Shutdown retains the unreaped leader as the group identity
anchor, scans Linux procfs for live group members, performs final group KILL
before reaping, then clears state. The regression suite now has 15passes,
including the real ignoring-descendant scenario. The reviewer independently
reran all14tests (before the additional leader-exit regression) and the original survivor reproduction: no descendant marker
was written after the corrected stop.

After both fixes, the real HTTP suite was rerun with the official SHA-verified
Node24.16.0 tarball on PATH: exit0,11PASS,model/codingSKIP. The Dockerfile Node
download/hash-check/extract logic itself was run under a temporary directory and
`node --version` returned v24.16.0; this remains a host installation verification,
not L1 image acceptance. Expected archive SHA256 values came directly from
https://nodejs.org/dist/v24.16.0/SHASUMS256.txt and are embedded in Dockerfile.

A separate real CLI gateway run with lan bind passed authenticated readiness,
rejected a deliberately mismatched fresh token, passed after token restoration,
accepted an idempotent repeated start and cleaned its owned process/state.
No model request occurred. CLI token values were generated only in process.

The final state observer uses Linux waitid(WNOWAIT) instead of Popen.poll: even
an unexpectedly exited gateway leader stays unreaped until owned group cleanup.
A further real-child regression verifies a leader that has already exited,
TERM-ignoring descendant and intervening status call cannot leave the descendant
alive. This closes the same ownership race before stop starts; no PID from disk
is ever adopted. The final suite now contains15tests.
