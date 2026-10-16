# OSWorld browser slice verification — 2026-10-16

Status: PARTIAL. Native source verification is separate from actual image/cloud acceptance. The original [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) remains open.

## Scope and source

Independent branch based on Pi commit a361f490555ead0ff67081ffb4874abf292a1b2f. New `osworld/` runtime, original fixed upstream files/license, bilingual usage/design, experimental catalog/backlog, engineering records and one local CI regression entry. The shared image workflow and selector remain unchanged; the new runtime context is the only image selected relative to this stacked base.

OSWorld upstream is https://github.com/xlang-ai/OSWorld at b138d348256078fa634fc3b73567a7337c793e6b, Apache-2.0. Original screenshot/AT-SPI handlers, selected actual getter and metric definitions are retained with file SHA256 provenance. The internal Flask test client exposes no arbitrary-code HTTP listener. The optional absent-Office compatibility adapter represents an unknown version without inventing an executable/version. Full framework setup/registry modules are not imported and no historical credentials/configuration were read.

## Executed checks

- PASS: actual native non-root desktop on Debian 13; reused installed Google Chrome 150.0.7871.114, isolated Xvfb/Openbox/GI dependencies, no nested VM, Docker daemon or privileged operation. No LibreOffice or new browser was installed on the host.
- PASS on the final source: canonical authenticated HTTP check, 18 assertions, with original HOME preserved. The internal smoke also requires exact independent DOM readback of 4096 Unicode characters including emoji. Internal GUI task and external controller-uploaded OSWorld task both require real observations, baseline metric 0, native keyboard/mouse actions, metric 1, changed PNG bytes and owned cleanup. These are source-runtime observations, not a changed-image or benchmark pass.
- PASS: scoped process/task/HTTP regressions, 41 distinct cases; together with 29 existing selector regressions, `python -m pytest -q osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py scripts/test_select_image_templates.py` passed 70 cases. Tests use real Linux groups/redirected descendants for stop, timeout, leader exit and cancellation; fixture workers are explicitly synthetic and do not count as desktop acceptance. Auth/typed-contract tests cover canonical and direct startup. Selected evaluators execute actual unchanged upstream function definitions.
- PASS: `python scripts/test_spec_tools.py`, 22 cases, after correcting missing owner names in both usage documents. Its synthetic deployment tests are not cloud runs.
- PASS: `python scripts/check_template.py --all --strict`, all 19 directories (18 products plus skeleton), after the same documentation correction.
- PASS: targeted `run_local_e2e._run_one(osworld, ...)`: 6 HTTP checks and explicit GUI SKIP. An initial invocation selected system python3 without the installed SDK; corrected by selecting the shared SDK environment. That invocation failure is not a product acceptance pass.
- PASS: actual native private-clipboard paste of all 4096 ASCII characters and, separately, all 4096 Unicode characters (`雪🙂` repeated 2048), independently read back from browser DOM. Earlier xclip experiments predate native-focus restoration; the final image smoke repeats the complete Unicode boundary on the current source. Clipboard readiness, owned process wait and released X selection ownership are required before success.
- PASS: local document links, workflow YAML, cumulative selection of only `osworld`, and standalone Docker COPY inputs. Scoped staged secret/diff checks pass with the vendored-file exception below. Exact source hashes appear below.

## Failures preserved

Initial native setup exposed missing Tk support, X11 session declaration and the isolated scrot loader path. The upstream Linux accessibility route also unconditionally probes LibreOffice; this browser-only adapter handles its absence explicitly. A private accessibility bus/registry, X root bus address and Chromium `ACCESSIBILITY_ENABLED=1` were necessary to obtain actual browser nodes; an empty tree was never accepted.

The first owned-descendant regression caught return before the asynchronous SIGKILL had taken effect. Cleanup now waits for no live owned group members while keeping the leader unreaped, then reaps it and removes state. It never signals a foreign group or adopts a PID file.

Earlier internal fast overwrite-input checks intermittently lost tail characters; no failed check was counted as a pass. The internal task now exercises one actual input followed by Tab/Enter submission; an independent external HTTP task also exercises Ctrl+A and overwrite input. Continuous per-key 4096-character typing independently exposed lost characters despite a successful dispatcher response. Generic GLib and key-hold experiments did not fix it; none is claimed as a successful input fix. The delivered command uses foreground xclip stdin and actual Ctrl+V, then reaps its helper and checks selection release. It supports native Unicode paste, not a per-character physical-key guarantee. The AT-SPI registry event loop services the live observation client; it is not presented as the typing fix.

A separate actual failure showed X input focus on a transient native window while DOM activeElement remained the page field. Restoring native focus only to the main window whose _NET_WM_PID matches the exact launched browser process made the final ASCII and CJK tasks pass. The code does not set DOM values, forge XML, match arbitrary window names or adopt a PID file. Astral emoji task observations were not consistently reliable and are not counted as accepted metric coverage; complete emoji paste is independently verified in DOM. The accepted task scores use ASCII and CJK.

Review also corrected an earlier private-HOME variant: HOME is now preserved and private XDG paths, Xauthority and browser user-data isolate the session. Old variant checks are historical only. The typing deadline is an explicit 60 seconds; final native paste takes approximately 1.23 seconds, including clipboard cleanup. The earlier 30-second per-key design was inadequate and is not shipped. `_running` holds the session lock.

## Unmet gates

- Actual standalone Docker image L1 build and non-root/network-disabled functional smoke: pending remote CI; this host has no Docker daemon.
- Actual changed-image Express SDK/HTTP/CLI acceptance and cleanup: pending an L1 archive and provider verification. Source-runtime checks cannot substitute for it.
- Full OSWorld VM snapshots, Office, arbitrary task/config/evaluator coverage, model agent/leaderboard benchmark: not implemented or verified.
- Draft PR, remote latest-head checks/review and normal merge: pending.

`tested_on` remains empty and status remains experimental. No version string, response marker, local fixture, queued CI or untested dispatch path is counted as L1/L2/L3.

## Final source fingerprints

Runtime/HTTP files were exercised as above; the Dockerfile was checked statically, not built locally.

| File | SHA256 |
|---|---|
| `osworld/commands.py` | `cfc9492afbe64aa05d61cb6f9b81a6f018d753b835f2b0c4dff25517e239ee41` |
| `osworld/runtime.py` | `7a618518884bede17cf2dbe5d50f2242aeb1eaa17122d17473179a8ffa3607ee` |
| `osworld/e2e_test.py` | `cf56d904ada180b4da9f32830e29e6491c4be18a9142b4713aefcb44be6682ab` |
| `osworld/Dockerfile` | `923a02dd79e584cc27b7fcd701b60fcf2bab09f815106b9fca06d5ee24fe0b5e` |
| `osworld/requirements.txt` | `fd84ae81836222430641fbfb510b5678476cb61ade21c8cd064f8fc185e435eb` |

## Vendored whitespace

The fixed official Python files contain trailing whitespace. `osworld/upstream/.gitattributes` tolerates only blank-at-EOL in those original `*.py` files, preserving their byte-for-byte SHA256 and full license. Own code and every other path retain the full diff check; no CI, checker, acceptance rule or repository-wide scanning rule is relaxed.
