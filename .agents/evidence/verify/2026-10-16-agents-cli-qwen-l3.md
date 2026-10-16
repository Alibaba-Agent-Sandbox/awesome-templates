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
- PASS: all13 relative Markdown links in both READMEs/design/new records exist;
  both bilingual Python examples parse with ast.parse.
- Pending: normal remote CI.

## Image and model scope

Not run for this new controller yet. A previously built matching image may be
used only after archive and installed-runtime provenance verification. Real Qwen
coding, sandbox/template/registry cleanup and independent readbacks must receive
separate exact evidence. No native model key is required by Qwen's compatible
route; available credentials do not substitute for actually running that gate.
Codex coding, canonical abx deploy and official provider metadata are not claimed.

## Review boundaries

Root review requested before cloud. Existing sessions/get exposes idle rather
than final turn success; original policy disables SSE/turn routes. The fixed
server's own private persisted state supplies only additional completed-turn
observation. Independent source/tests/artifacts and random ACK are the coding
authority. The session runs full_access and the entire owned disposable sandbox
is the resource boundary. No hostile same-user-code isolation is asserted.
