# Verification: Original QM harness and SDK backend

- Date:2026-10-21. Result:PASS for the bounded native/runtime/image/Express/HTTP/model slice.
- Runtime/controller source:fff24f25dbe37b1ccc2110b81879e467645e5095, both templates1.0.1.
- Original QM0.1.0 source deef9b8b1e2b85bd4166dd833604bb31bcb8e255; original Node24.16.0 archive/executable SHA checked; original Node SDK0.1.0 source90b5187dca84fca78d75d3045896482540641c72, exact original locks and SDK build.
- Server0.3.0 source34e7e011c5569f77b7f605e65313be7498f6cf02, normally merged in [SDK PR82](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/82) as33f857f5a79fd10326652e9d03f15f3621d6b848 at02:11:20UTC; Issues80/81closed. User model credentials only enter an explicitly configured owned command server. No generated code executes on operator.

## What was verified
Original exported createPiHarness and createToolContext operate unchanged with the authored original-QM-compatible backend implemented using the actual original Node SDK ServerClient, process.shell and files.upload/download. This is one bounded computer, not the full QM core/multiplayer deployment. Real SDK external target downloads, own file absence and fresh post-return ACK establish observable backend behavior.

## Commands and results
| Gate | Result | Evidence |
| --- | --- | --- |
| QM Sandbox immutable native steps | PASS |12871wire bytes, officialREADY, actual Python SDK creation, CLI+SDK native version/importsmokes;[receipt](../../../qm-sandbox/evidence/express-2026-10-21.json) |
| QM Sandbox full HTTP |18PASS/0FAIL/0SKIP | original QM→actual Node SDK write/read/exec/removal, independently downloaded exact fresh bytes, fresh absence ACK;439.985seconds;[source proof](../../../qm-sandbox/evidence/verification-steps-2026-10-21T021037Z.json) |
| QM immutable native steps + full HTTP |PASS/10PASS/0FAIL/0SKIP |12859wire bytes, same canonical SDK creation/native smokes;[receipt](../../../qm/evidence/express-2026-10-21T021039Z.json),[source proof](../../../qm/evidence/verification-steps-2026-10-21T021039Z.json) |
| QM actual native coding |19PASS/0FAIL/0SKIP | qwen3.8-flash, original harness/custom tools and actual SDK; existing source repaired, original3tests unchanged, report/precise nonce independently downloaded, original3and4held-outs/fresh post-return ACK; complete run688.572seconds |
| Keyless original-native model routing |PASS | exact Chat Completions path/model/synthetic Bearer and final reply before real key; fixture files/listeners removed |
| Actual non-root L1 images |PASS |[run39531501100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39531501100), jobs118998273940(qm-sandbox) and118998273928(qm); rootfs2018549760and2018516992bytes,8GiBguard preserved; source/native version/import/workspace checks pass |
| Exact-source asset/wire/server guards |4PASS | pin/tamper/budget cases10.68seconds after explicit server selection |
| Earlier local regressions |PASS |37wrapper/path/process/archive/anonymous/privacy,14native-terminal controls,8actual SDK-over-authored HTTP controls;[research](2026-10-21-qm-native-research.md) |
| Runtime-source remote CI |10PASS/expectedSKIP | complete L0/spec/docs/media/dev-services/local E2E, native images and authorization; final record-only head requires fresh checks |

## Cleanup
Each canonical run independently confirms its own sandbox/template absence and private OSS object/bucket deletion. Native private HOME/cache/request/model-catalog/workspace state and process groups are cleaned. External tests independently confirm owned projects and exact files absent; QM secondary9010listener and native temporary state return to baseline. No other actor's cloud or local resources are removed. All create/download failures retain their ownership journals.

## Failures and corrections retained
Initial15199-byte recipes exceeded unchanged15000wire guard: combined reviewed COPY locks remain byte-compared to original archives, corrected recipes pass. Before bounded SDK request-draining, a real local SDK HTTP close regression failed; fixed eight controls pass without claiming instant remote cancellation.

First actual QM Sandbox attempt:17PASS/1FAIL due to shared server coercing JSON true into integer1 before the template guard. [Immutable failure](2026-10-21-qm-sandbox-initial-steps-failure.json) retains276.626seconds and independently passing cleanup. It is not qualification evidence. The same unchanged HTTP boolean assertion now passes against merged SDK fix; no assertion is weakened. Initial QM1.0.0 native coding PASS remains historical but current1.0.1 is separately rerun against the fixed server. Initial non-root image attempts and every earlier failure remain in research/history.

## Scope and limitations
No Docker image cloud deployment, other provider, Slack/email, full multiplayer/web/Postgres/cron/subscription, background/delegated sessions, peak memory or arbitrary model promise. Original default Docker backend is not falsely qualified. The [current43matrix](2026-10-21-current-native-http43.json) is native/runtime+fullHTTP only, not universal L3/L4 or completion of all64Issues. Final current-head CI/review and normal merge/readback remain required before closing Issues44/45.

## Final local qualification checkpoint
`python scripts/test_spec_tools.py`:57PASS,13.648seconds. `python scripts/check_template.py --all --strict`:0violations. `python scripts/check_docs.py`:195public Markdown documents/0link failures; explicit4engineering-record link checks0failures. `python scripts/step_acceptance.py --require-http --output <new-current43-proof>`:43/43current native/runtime and43/43requiredHTTP PASS, complete=True. No old matrix or merged evidence is overwritten. [Full runtime CI proof](2026-10-21-qm-native-runtime-ci.json) retains exact job links. The initial failed attempt was moved byte-for-byte into the owner engineering evidence directory so only passing template receipts establish qualification.
