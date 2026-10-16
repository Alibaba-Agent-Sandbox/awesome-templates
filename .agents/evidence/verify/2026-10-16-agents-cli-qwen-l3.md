# Agents CLI independent Qwen coding acceptance

Result: PARTIAL

Refs [Issue25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25).
Isolated branch starts from a361f490555ead0ff67081ffb4874abf292a1b2f.
Product commands.py, Dockerfile, template.yaml and policy remain byte-identical.
The independent SDK controller is host-side acceptance code, not copied into the
image. Existing historical evidence is preserved.

## Local checks

- PASS: first targeted run `python -m pytest --import-mode=importlib -q
  agents-cli/test_sdk_verifier.py`, 25 passed. Real local Python subprocesses
  compile project source and run complete unittest modules/held-out controls.
  HTTP/cleanup controls are synthetic and make no model/provider claim.
- PASS: `python scripts/check_template.py agents-cli`, conformant.
- PASS: final combined `python -m pytest --import-mode=importlib -q
  agents-cli/test_protocol.py agents-cli/test_sdk_verifier.py`, 40 passed in5.13s.
  Includes a real HTTP subprocess with explicit synthetic fixture CLI PATH:
  default smoke skips models; required-model smoke exits1 and directs callers
  to the owned SDK verifier. These are protocol tests, not product/model proof.
- PASS: `python scripts/test_spec_tools.py`, 22 tests; simulated deploy/cleanup
  failures are expected no-network negative controls, not cloud attempts.
- PASS: `python scripts/check_template.py --all`, all18 directories conformant.
- PASS: `git diff --check`.
- PASS: final combined40 regressions rerun after explicit stream closure,5.04s.
- PASS: subsequent41 combined regressions,4.88s, after persisting a permission
  denial marker so an external recovery controller cannot retry that403 path.
- PASS: all13 relative Markdown links in both READMEs/design/new records exist;
  both bilingual Python examples parse with ast.parse.
- Pending: normal remote CI.
- PASS: final image-evidence/docs update:22 relative links,2 bilingual Python
  examples,2 JSON parses and a scan against11 private owned identifiers/values;
  no owner identifier appears in the proposed public files. The first local
  audit script assumed every discovery JSON was a dict and stopped on an empty
  list; its type guard was corrected before this successful read-only rerun.

Root review of the controller accepted its API/state/evaluator/cleanup design
and requested accurate -B wording (only explicit source compilation avoids
reading pyc), plus larger1800/1500-second sandbox/server budgets with the same
turn≤600 deadline and immediate cleanup. These changes are included. Readiness
requests are individually5 seconds and private state probes10 seconds. Inspected
the actual turn polling code: its session-status200 assertion is not duplicated.

## Image and model scope

At the initial local checkpoint these gates were not run; the following actual
owned image attempt now supplies independent evidence. No historical failure was
rewritten. The root17-image earlier attempts/evidence remain their own history.

- PASS: original official artifact12026073735, workflow38853293050, checkout
  adbf760b80ce551bfea210bf9a473ea74001efa8, sourcea361f490555ead0ff67081ffb4874abf292a1b2f.
  Workflow actual remote state SUCCESS; checkout parent and artifact head match.
  Original archive SHA256
  f5d0da999e973ff3354113c3e6bc814d19a1b8d39334e607261962dd4b4d7164
  was verified inside the owned cloud helper. No host bulk archive download.
- PASS: serialized /tmp/abx-acr-push.lock, freshly issued official temporary ACR
  auth inside the lock, cloud push and registry digest readback, official gen2
  Agents CLI template registration and READY. No arbitrary root/batch resource
  was reused or deleted; one new unpredictable owned repo/template/helper.
- PASS: host verifier frozen1f975ff99957dbec9927d0ca9b1b1c35a841c416 itself calls
  Sandbox.create, proves exact initial test_sevenFAIL/test_zeroPASS, starts original
  installed commands/policy on new9010, checks actual pinned versions and closed
  HTTP files/shell/process routes, and runs a genuine qwen-code/qwen3.8-flash
  session/event/reconnect/items turn. Its own state diagnostic confirmed completed.
- PASS: changed existing source; exact original test bytes preserved; exact JSON
  artifact and nonempty report; complete original and agent-written unittest
  modules; six independently executed held-out cases. Each verifier compiles
  source in isolated Python and requires a new post-agent random ACK. No marker,
  fixture CLI, caller receipt or model-written test result can establish this pass.
- PASS: SDK-owned sandbox kill and paginated ID/nonce absence. Outer lifecycle
  report records8 cleanup flags alltrue: helper kill/absence, model kill/absence,
  template delete/exact-name absence, ACR tag/repository delete+GET404.
- PASS: separate newly executed read-only controller verifies5 post-run states:
  helper/model ID and nonce absent, exact owned template name absent, ACR tag404,
  ACR repository404. Private intents retained mode0600 for independent owner review.
- No actual permission403, model failure, resource cleanup failure or source
  overlay occurred during this attempt. Synthetic403 tests remain negative controls.

[Actual image SDK result](../../../agents-cli/evidence/qwen-image-sdk-2026-10-16.json)
and [independent strict readbacks](../../../agents-cli/evidence/qwen-image-sdk-strict-readback-2026-10-16.json).
Commands/policy SHA values are in that result; Dockerfile/template.yaml are also
byte-identical to a361. The host controller1f975 and imagea361 provenance remain
distinct. The new CI image from1f975 was built successfully but was not the image
used in this actual run. Server source pin remains e2cb27e24fde0a67112f82b8d44af463445a5d1a.

Local orchestration source hashes (workspace audit artifacts, not shipped runtime):

- agents_cli_image_acceptance.py:
  a57d9a7a09144f68dfcfe630485ff34274562f7d968ff530aef20fa8a76c8524
- agents_cli_strict_readback.py:
  4f99c46c27e720c2f0c3973a2d715d044425dbd387f750c66e4c37028a3b3d9b

Root independently reviewed frozen1f975 and reran41 tests PASS16.82s before cloud.
All4 normal checks on that exact head were API-confirmed SUCCESS: actual image
build, plan, push and PR full local-e2e. This actual-image/model slice does not
complete the full canonical local abx deploy wrapper, Codex coding, hosted Agents,
other providers, merge or formal provider metadata. Result remains PARTIAL for
the full Issue25; [PR101](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/101)
is draft, Issue25 stays open, tested_on remains empty.

## Review boundaries

Existing sessions/get exposes idle rather
than final turn success; original policy disables SSE/turn routes. The fixed
server's own private persisted state supplies only additional completed-turn
observation. Independent source/tests/artifacts and random ACK are the coding
authority. The session runs full_access and the entire owned disposable sandbox
is the resource boundary. No hostile same-user-code isolation is asserted.
