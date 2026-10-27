# OSWorld browser slice

## Purpose

Run a real non-privileged Linux browser desktop and a declared subset of OSWorld task observations/evaluation through named Agent Sandbox commands. This is an independent Alibaba template, with no dependency on an E2B template ID.

## Capabilities

One private 1024x768 Xvfb display, Openbox, session/accessibility DBus, AT-SPI registry and Chromium profile. Capture actual PNG screenshots; send real mouse/keyboard input; read the real browser accessibility tree. Apply supported OSWorld browser setup and evaluate selected upstream metrics against the actual tree. No VNC listener, VM snapshots, Office apps, benchmark runner or model agent is included.

## Exposed API

| Command | Parameters | Result / actual implementation |
|---|---|---|
| osworld_setup_check | none | Pinned source, available executables, running boolean and explicit slice; no GUI startup. |
| desktop_start | none | Running/screen/browser-geometry object; start owned runtime Python worker, Xvfb, Openbox, private DBus/registry and Chromium. Existing owned session is reused. |
| desktop_stop | none | `stopped`; group cleanup and private profile removal, idempotent. |
| screenshot | none | PNG base64, SHA256, MIME, width/height; pinned OSWorld `/screenshot` handler through an internal test client. |
| click | x: int required; y: int required; button: str = left | `clicked`; PyAutoGUI click inside 1024x768, left/middle/right. |
| type | text: str required | `typed`; Private X11 clipboard plus actual PyAutoGUI Ctrl+V, 1..4096 Unicode characters (NUL refused), stdin rather than argv; release owned clipboard after paste. |
| hotkey | keys: str required | `pressed`; 1..4 comma-separated actual PyAutoGUI key names. |
| a11y_tree | none | XML string, at most 2 MiB; pinned upstream AT-SPI handler. |
| run_task_config | task_path: str required | Applied-step count and browser geometry; complete validation before setup. |
| evaluate | task_path: str required | Actual float score, metric, getter, source commit. Never accepts a submitted score. |
| osworld_desktop_smoke | none | Real GUI/evaluator check then cleanup; refuses to replace an existing session. |

The task file must exist within `WORKSPACE`, including after symlink resolution, and be at most 64 KiB. Supported setup is exactly `chrome_open_tabs` with 1..4 HTTP(S) URLs or workspace file URLs, and `sleep` of 0..5 seconds (at most 8 steps). Supported evaluator is exactly `func: check_include_exclude | exact_match`, `result: {type: accessibility_tree}`, `expected: {type: rule, rules: ...}`. No postconfig/options or implicit fallback. `check_include_exclude` requires a nonempty include list. Original getters and metrics execute from the committed upstream source.

## How to build

[Dockerfile](../../osworld/Dockerfile) starts from the required Alibaba placeholder (production cn-hangzhou/v0.0.49), installs exact critical Debian 13 x86_64 package versions, creates a system-Python GI-compatible virtualenv, installs the [hash-locked Python graph](../../osworld/requirements.txt), and installs Playwright 1.58.0's Chromium revision. Transitive OS packages remain resolved by Debian's repositories. The worker explicitly retains PLAYWRIGHT_BROWSERS_PATH from the image environment. No GUI packages install at runtime and no extra capability is needed. System Python handles GI; the separate platform Python runs the SDK server.

Canonical generation-2 startup is `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, readiness is `agent-sandbox-server healthcheck --port 9000`. The Dockerfile installs the exact published server package. Runtime, upstream source, full license and metadata are in the standalone Docker context. The final user is `user`.

## Express feasibility

Feasible: slice

Limiting factor: Express lacks KVM and therefore cannot provide upstream VM snapshot/reset semantics.

Xvfb, Openbox, DBus and browser input require no nested VM, Docker daemon or additional capabilities. Browser sandbox flags use `--no-sandbox` inside the outer sandbox; the outer sandbox is the isolation boundary. Allocate 2 vCPU / 2048 MB and allow up to 60 seconds for startup. Full task coverage, VM reset, app snapshots, Office and leaderboard scores are not delivered. Issue36tracks delivery of this declared slice.

## Risks

The desktop shows data from pages opened by the caller; screenshot/tree returns intentionally contain page content. Restrict callers with `ABX_SERVER_TOKEN`. API shell/files remain enabled as declared capabilities. The private worker receives a small environment allowlist and no cloud/model credentials or inherited display/profile. HOME is preserved; XDG paths and Chromium user-data-dir are private and Python user-site loading is disabled. Browser URLs may use network egress; the keyless smoke uses a disposable local page with no network.

Typing uses foreground xclip 0.13-4, stdin text and real PyAutoGUI Ctrl+V. It overwrites only the private display's clipboard, then stops/reaps the owned xclip process and verifies release of that selection ownership. It does not erase the destination application's requested pasted content or touch a host clipboard. Input/hotkeys restore native X focus only to a main window whose _NET_WM_PID matches the exact browser process launched by the worker; no window is adopted by name or PID file. This supports Unicode paste; applications rejecting paste are outside the command's scope. Continuous per-key streams were empirically unreliable and are not presented as passing input evidence.

The entire Linux process group is stopped before reaping the leader. A child deliberately escaping through setsid is outside that boundary. One lock serializes session operations. Responses are bounded to 8 MiB, requests to 32 KiB, screenshots to 1024x768; the upstream implementation still allocates its observation internally before the return bound. Ordinary operations have a 30-second deadline; typing/startup/smoke have 60 seconds with bounded clipboard readiness and cleanup. Operation deadlines stop the entire session; no HTTP disconnect cancellation or streaming is promised. Unsupported-task errors also stop the session. Never expose the unsafe upstream execution routes.

An absent LibreOffice version is represented as unknown (empty tuple) solely for the upstream browser accessibility handler. No Office executable/version is fabricated. Complete Unicode paste is checked independently in the browser DOM. Astral emoji accessibility observations were not reliable in native task trials; accepted task fixtures use ASCII and CJK. The wrapper returns the actual upstream XML and does not fabricate missing characters or scores. Chrome Linux accessibility is explicitly enabled; a nonempty real browser tree is required for functional acceptance.

## Test plan

L0: `pytest -q osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py`, strict checker and local HTTP e2e. An unrequested desktop test prints SKIP and proves no GUI tier. `E2E_REQUIRE_DESKTOP=1 E2E_RUN_DESKTOP=1` makes a missing or failing GUI a failure.

L1: actual standalone Docker build and `template.yaml` smoke run non-root with networking disabled. Smoke must require a real PNG/tree, baseline score 0, actual click/type/hotkey events, independent browser input/result state, final upstream score 1 and changed screenshot pixels, followed by owned cleanup. It also requires exact independent DOM readback of 4096 Unicode characters after native clipboard paste. Merely checking versions cannot pass.

Current L2 follows the template spec through `python scripts/public_launch_e2e.py osworld --provider alicloud-express --source ./osworld --application-controller --output osworld-attempt-1.json`. Separately, source 9a53b56 passed actual changed-image official registration on Express, SDK/HTTP/CLI full desktop smoke, required-GUI HTTP18 without skips and independent owned cleanup. This dated supplemental image-cloud verification does not certify the current source launch; see [final evidence](../../.agents/evidence/verify/2026-10-16-osworld-changed-image.md). Source-runtime probes remain separate. L3 full upstream benchmark/model acceptance and L4 other providers remain unverified; no response marker or version is a benchmark score.

Screen and viewport are independent: the PNG remains 1024×768, while startup waits for a visible nonzero viewport. Read-only numeric `browser_geometry` accompanies startup/setup; smoke records it and uses actual content offset plus DOM rect for native clicks without CDP viewport emulation. Actual interaction/evaluation and Unicode destination gates remain required. See [viewport evidence](../../.agents/evidence/verify/2026-10-16-osworld-viewport.md).

The Dockerfile explicitly assigns `/home/user/app` itself to the runtime user. File-level `COPY --chown` does not grant write access to a root-created WORKDIR. The real non-root smoke must create and remove its file-backed task there.

Current1.0.0 canonical native steps now pass official READY, actual Python SDK creation, CLI/SDK full native desktop smoke and required external GUI18/0/0 with independent owned sandbox/template/private-asset-cache cleanup. Exact current L1 build39462497032 also passes. [Final current-source verification](../../.agents/evidence/verify/2026-10-20-osworld-sdk-desktop-final.md) keeps historical image/smoke/GUI-skipped scopes distinct.

Template1.0.3 normalizes only a None native Accessible.get_attributes result to an
empty mapping in the owned worker. Actual fresh-observer diagnostics reproduced
the upstream .items AttributeError and omitted web subtree; earlier cache-refresh
hypotheses did not repair it and are removed. Nonempty mappings and native
exceptions retain their original behavior. Vendored upstream bytes remain unchanged;
no synthetic accessibility tree or second command server is used. Fresh provider
core and expense business verification remain required.
