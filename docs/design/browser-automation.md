# browser-automation

## Purpose

Agents use a reproducible headless browser for navigation, screenshots, page text,
links and form filling. The user receives real browser artifacts through the
sandbox files API, without requiring a desktop or a model credential.

## Capabilities

Named `browse`, `scrape`, `fill_form` and `run` commands; shell, files, code and
port 9000. For the original Python browser commands, one browser per request avoids cross-thread Playwright handles
and leaking cookies or form state to another invocation. Optional SDK BROWSER
routes are not enabled. Express runs the entire headless slice, not desktop/VNC.

## Exposed API

| Name | Parameters (type, required/default) | Return | Upstream execution |
|---|---|---|---|
| `browse` | `url`: str required; `action`: str=`screenshot`, screenshot/extract/links/full; `timeout_s`: int=30, 1–120 | action/title plus PNG path, text, links/count, or screenshot/text_preview | Playwright 1.58.0 `chromium.launch`, `page.goto`, screenshot/DOM APIs |
| `scrape` | `url`: str required; `selector`: nonempty str required; `timeout_s`: int=30, 1–120 | count/texts | Playwright `locator.all_inner_texts` |
| `fill_form` | `url`: str required; `fields_json`: str required, 1–100 exact selector/value string objects; `timeout_s`: int=30, 1–120 | fields_filled only | Playwright `locator.fill`, verifies with `input_value` |
| `run` | `script`: str=`main.py`, existing resolved file inside workspace; `timeout_s`: int=120, 1–120 | buffered successful stdout | argv `[sys.executable, resolved_script]`, no shell |

Browser timeout applies to individual operations, not the total request. Client
HTTP timeout does not cancel a command. No secrets, selectors, page URL/title/DOM
are returned by fill_form. Pages may copy entered secrets into those fields.
URLs accept http/https and inline data:text/html,; no file: or embedded credentials.

## How to build

Template2.0.2 explicitly owns /home/user/app as user:user before runtime USER. This repairs actual non-root workspace mkdir/write failures. Earlier provider receipts retain their original source-version scope; this changed profile requires new acceptance.

[Dockerfile](../../browser-automation/Dockerfile) uses Alibaba base placeholders
(default `v0.0.49`), Playwright `==1.58.0` and Chromium revision selected by that
pin. Separate `pip install`, `playwright install-deps chromium`, and `playwright install chromium`
RUN steps execute during build before USER user. Version2.0.2 splits the build to
isolate installation phases after a stream deadline failure; runtime APIs and
the full Chromium profile are unchanged.
The browser path is `/opt/playwright`. The Dockerfile installs published `agent-sandbox-server==0.4.0a4` directly.
Generation 2 uses `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`
and readiness `agent-sandbox-server healthcheck --port 9000`. No CMD/ENTRYPOINT.

## Express feasibility

Feasible: yes

Limiting factor: 64 MB shared memory; Chromium launches with --disable-dev-shm-usage.

The headless workflow fits non-root user, 2 vCPU/2 GB and no KVM, Docker or extra
capabilities. Chromium uses /tmp and concurrency can exhaust memory. Feasibility
is architectural; it is not evidence of a passing provider run.

## Risks

Browser URLs and subresources can access network services; use platform egress
policy for network restrictions. The template does not enforce an SSRF allowlist.
Form values are validated but never logged or returned; all Playwright error
strings are replaced because call logs can contain input values. No shared browser
state. Extraction/screenshots/user-script stdout may contain page secrets and
must be handled privately. Scripts are trusted sandbox code with process access.
User-provided scripts do not escape the sandbox but are not a security boundary.
Screenshot files accumulate until deleted. The image is larger because Chromium
and its system libraries are included; inspect real build layers before L1.

## Test plan

L0: `python3 scripts/run_local_e2e.py` with pinned Playwright and matching browser
installed. Browser e2e must return 0 with real page title/text, links, CSS matches,
PNG signature verified after HTTP files download, actual filled value checks,
sensitive success/error redaction, required/mistyped args, unknown command and
parallel request isolation. Missing Chromium must exit 1, never SKIP/PASS.
L1: actual image build, logs confirm Playwright 1.58.0 and its Chromium revision.
L2: `python scripts/public_launch_e2e.py browser-automation --provider alicloud-express --application-controller --source ./browser-automation --output browser-automation-attempt-1.json`, outside CLI and SDK must
assert smoke browse result action=extract, title/text=ABX_E2E_OK. Also download and
validate screenshots through remote files APIs; no host file shortcut.
L3: no model key required; browser product behavior is tested by actual navigation
and artifacts, not a model marker alone. L4 only after an actual additional provider
run. No provider evidence files until the corresponding complete run passes.

Follow-up real build-network execution exceeded300seconds, so the earlier stream deadline is not a universal per-RUN cap. Stage separation is retained; slow large-asset transport remains unresolved.

Current-version acceptance on 2026-10-20: version 2.0.2 genuine image READY/CLI/SDK and complete Chromium screenshot/PDF/independent artifact HTTP 24 PASS / 0 FAIL / 0 SKIP. Independently verified sandbox/template/registry cleanup. Historical pending statements describe earlier checkpoints; see the current [Verified table](../../browser-automation/README.md#verified).

## Native MCP extension2.1.0

Official npm0.0.83 and exact lockfile driver1.64.0-alpha-1790635538000 reuse Chromium1208; no second browser. New mcp_start/status/call/stop/self_test commands use native session negotiation and tools. Standard in-sandbox HTTP MCP on127.0.0.1:8931; external named transport retains shared-server auth and buffered4MiB limits. Real fixture counter and PNG, private profile/environment, reserved process-group leader plus unique-marker/pidfd detached worker cleanup are required. Old2.0.2 receipts remain historical; new runtime version resets tested_on. Actual pinned native local7 cases passed; new image/Express/full API required before qualification.

## PDF and owned script processes2.2.0

Add actual A4 PDF with typed landscape/background flags and1–120second owned-child execution deadline plus bounded cleanup,256KiB URL/no NUL, post-render16MiB artifact cap and independent remote PDF MediaBox orientation checks. PDF stdin is private JSON; its HOME/profile are temporary. Generic workspace run uses the same reserved leader/marked-worker cleanup and256KiB per-stream bound, preserving caller HOME while filtering credentials/injection variables. Existing ordinary failed scripts could leave a background child; the regression fails before the fix and passes after. A du-based8GiB image-rootfs build gate records actual byte count; this differs from filesystem free capacity. Exact2.1.0 MCP receipts remain historical and2.2.0 provider qualification is reset.

### Actual2.2.0 acceptance

Actual Express native steps source21a6b301d5468f568d8956ea059144ebe7567696 and Python SDK Sandbox.create passed CLI/SDK smoke and full remote HTTP37/0/0, including independent portrait/landscape PDF downloads/geometry and PNGs, owned process/artifact cleanup and sandbox/template absence. See [dated provider receipt](../../browser-automation/evidence/express-2026-10-20T103410Z.json). Latest-head CI and normal merge remain separate gates.
