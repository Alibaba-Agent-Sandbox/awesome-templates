# browser-automation

## Purpose

Agents use a reproducible headless browser for navigation, screenshots, page text,
links and form filling. The user receives real browser artifacts through the
sandbox files API, without requiring a desktop or a model credential.

## Capabilities

Named `browse`, `scrape`, `fill_form` and `run` commands; shell, files, code and
port 9000. One browser per named request avoids cross-thread Playwright handles
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

[Dockerfile](../../browser-automation/Dockerfile) uses Alibaba base placeholders
(default `v0.0.49`), Playwright `==1.58.0` and Chromium revision selected by that
pin. `playwright install --with-deps chromium` runs during build, before USER user.
The browser path is `/opt/playwright`. The server wheel injected by deploy wins;
fallback is python-sdk archive `35da216a300f1e2e84254a1cf4b4a7ea98681505`.
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
L2: `python3 scripts/express_e2e.py browser-automation`, outside CLI and SDK must
assert smoke browse result action=extract, title/text=ABX_E2E_OK. Also download and
validate screenshots through remote files APIs; no host file shortcut.
L3: no model key required; browser product behavior is tested by actual navigation
and artifacts, not a model marker alone. L4 only after an actual additional provider
run. No provider evidence files until the corresponding complete run passes.
