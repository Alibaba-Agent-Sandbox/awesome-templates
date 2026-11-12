# Verification: bounded observation of existing HMR origin diagnostics

Date: 2026-11-12. Before revision:dfb9e413c0797b4279456426839272e145198200.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

FAIL preserved: actual Actions local-e2e
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/43293813726/job/131446657105
first fails in next-app/test_commands.py:100 after17 passes in the first process-regression
group. Both actual websocket origin assertions pass; the immediate dev_logs snapshot lacks
the warning/host. This run stops before SWE/agents-cli and cannot certify their remote result.
The previous6f7 Actions log remains separately retained and is not overwritten.

Verified source facts: Next16.4.2's package-lock-resolved tarball passes its complete SRI check;
its blockRequest calls warnOnce before res.end. The template independently drains child stdout
on a reader thread using read1, and dev_logs returns its current buffer. No barrier joins those
operations. An immediate assertion is therefore inconsistent with that asynchronous API. The
exact collection/CI scheduling sequence for the original failure remains an inference, not an
independently reproduced cause.

PASS: only the existing test's log observation gains a5-second monotonic deadline and short
conditional polling. Its final original warning AND exact-host assertion remains unchanged.
Both real websocket calls and their original TEXT/deny assertions remain unchanged; no network
operation is retried. Production commands, lifecycle, Next/SDK/image pins and CI are unchanged.

PASS: a complete scratch Next template context installs the exact repository lockfile with
package scripts disabled; installed versions are Next16.4.2, React/React-DOM19.3.1, Vite8.3.4.
The copied test and lock are byte-identical to the owner source. Actual command/test-controller
files together run18 cases:18 pass, zero skips,14.68s, with real Next/Vite processes and owned
listener cleanup through the original fixtures. Environment: Node22.22.2, Python3.13.13,
published client/server0.4.0a7 and hash-locked preview dependencies. No editable candidate SDK
is used. The initial host npm12 install rejected remote lockfile tarball URLs before running
tests (EALLOWREMOTE); an explicit task-local locked-remote installation with --ignore-scripts
passed, without changing global config or the lockfile.

PASS: pip check, scoped Ruff --select F,238-document local link check, local record links/JSON
and git diff --check. The [typed receipt](2026-11-12-next-hmr-buffered-observation.json)
retains actual failed job/log hash, toolchain/lock identity and local outcome. No artificial
log delay, new image, model or cloud resource was used. Runtime cleanup assertions remain in
the original fixture. Scratch sources/dependencies are isolated from the repository.

Command: `E2E_RUN_LLM=0 python -m pytest -q <scratch-next-app>/test_commands.py
<scratch-next-app>/test_forwarded_controller.py` after exact-lock npm ci and installation of
scripts/requirements-preview.txt. Latest-head full remote CI remains the acceptance gate;
this local18-case pass does not establish subsequent workflow groups or cloud E2E.
