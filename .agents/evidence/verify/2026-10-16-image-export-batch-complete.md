# Complete L1 archive batch and end the temporary all-selected mode

Date: 2026-10-16
Result: PARTIAL

## Verified upstream image revision

Source head: a361f490555ead0ff67081ffb4874abf292a1b2f. PR artifact SHA suffix / merge ref: adbf760b80ce551bfea210bf9a473ea74001efa8. [Pi PR 86](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/86) remains unchanged on that head.

[Image run 38853293050](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38853293050): COMPLETED/SUCCESS, plan plus all 17 image jobs. Each image actually built, checked installed pins/non-root user and keyless smoke, then saved and uploaded an archive. The manifest includes only completed-success image jobs with unexpired artifacts, verified via GitHub API. No queued/cancelled result is a pass.

Both actual host local suites passed: [PR run 38853292950](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38853292950) and [push run 38853289192](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38853289192). Those model-disabled host checks do not establish model acceptance.

The actual Pi job log was independently inspected: Node v24.16.0, Pi 1.3.0, fd 10.5.0 and rg 15.2.0 passed, followed by pi_version and pi_tools_check. The latter executed the real official read/find/grep/ls under non-root, network-disabled image diagnostics. Actual image npm ci passed with the frozen tree. This closes Pi L1 for this head, without claiming image/cloud L3.

## Successfully uploaded image archives

Each archive retains one-day artifact retention and compression level 1. The existing files are not deleted or replaced by policy closure. The archive metadata contains source/checkout/run/SDK/base/image identity and SHA256; an upload does not prove local download, registry transfer or cloud registration.

| Template | Artifact ID | API size_in_bytes |
|---|---:|---:|
| agents-cli | 12026073735 | 547831859 |
| amp | 12025633610 | 377337485 |
| browser-automation | 12025879610 | 755684438 |
| claude-code | 12025814586 | 290978703 |
| codex | 12024964846 | 438592376 |
| codex-agent-api | 12026520112 | 438126049 |
| deepseek-harness | 12026231649 | 255863464 |
| droid | 12026152124 | 542400076 |
| gemini | 12025929761 | 291496471 |
| hermes-agent | 12026390919 | 460572736 |
| node-web | 12025874850 | 254483254 |
| openclaw | 12025274751 | 503373690 |
| opencode | 12026252062 | 324442939 |
| pi | 12026356200 | 354700397 |
| python-hello | 12026092357 | 259078735 |
| qoder | 12026182472 | 300097905 |
| qwen-code | 12026715521 | 423441178 |

Total reported artifact bytes: 6818501755.

## Closure scope and verification

The isolated closure branch changes only the public export mode and engineering records. Automatic=default restores the normal Pi/python-hello archive scope; dispatch export_images=false remains effective. No template selection, build, smoke, runtime, pin, archive checksum or existing artifact is modified.

This small PR is stacked on feat/pi-runtime-20261016, so its cumulative base-to-head diff contains no image inputs. The original Pi PR stays on its actually tested a361 head. After that upstream PR lands, retarget this closure PR to main and inspect the latest checks before merging. This avoids an unnecessary 17-image rebuild without using a last-commit diff or bypassing gates.

Local verification: selector/export-policy pytest 29 PASS; spec tools 22 PASS; all 18 template directories strict conformant; actual export-policy command returned false. Affected relative links and git diff check passed. Remote closure-branch CI remains pending until actually observed.

## Remaining gates

Changed-image registry transfer, official Express registration, SDK/HTTP/CLI smoke, cleanup and model acceptance are separate owner work. Their results are not inferred from these archives. No provider verification/catalog promotion is made here. The temporary all-selected mode has a concrete closure commit/PR path; completion requires that closure to merge after its upstream, rather than merely declaring the flag off on an unmerged branch.
