# OSWorld Linux browser slice

## What it does

A real private Xvfb/Openbox/Chromium desktop with [OSWorld](https://github.com/xlang-ai/OSWorld) screenshots, Linux AT-SPI, native mouse/keyboard actions and private-clipboard Unicode paste and selected task evaluators. This is an independent Alibaba template. Full OSWorld benchmark execution, VM snapshots, Office and a model agent are outside this browser slice; [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) tracks delivery of this slice.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a3`, installed directly by the Dockerfile.

OSWorld source `b138d348256078fa634fc3b73567a7337c793e6b` (Apache-2.0); Playwright 1.58.0 with its Chromium revision; PyAutoGUI 0.9.54; Pillow 11.3.0; Flask 3.1.2; NumPy 2.3.3; lxml 6.0.1; requests 2.32.5. The complete Python dependency graph is [hash locked](requirements.txt). Debian 13 x86_64 critical desktop packages have exact pins; transitive OS dependencies remain repository-resolved. See [Dockerfile](Dockerfile), [source attribution](upstream/source.json) and [design](../docs/design/osworld.md).

## Problem solved

Use real browser desktop observations and actions on Express without KVM, a Docker daemon or elevated runtime privileges. Failed or unsupported tasks are errors, rather than fabricated benchmark scores.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./osworld --yes
abx run <sandbox-id> osworld_desktop_smoke --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('osworld_desktop_smoke'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/osworld_desktop_smoke`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "desktop screenshot/click/type/hotkey/AT-SPI/evaluation OK"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

## Command reference

| Command | Parameters | Result |
|---|---|---|
| osworld_setup_check | none | Source commit, dependency booleans, running state, explicit slice. |
| desktop_start | none | Start/reuse one owned session; running, screen size and numeric browser geometry. |
| desktop_stop | none | Stop the owned group, remove private state; `stopped`. |
| screenshot | none | Real PNG base64, MIME, SHA256, width=1024, height=768. |
| click | x: int required, y: int required, button: str = left | Real click; coordinates inside 1024x768, left/middle/right. |
| type | text: str required | Private X11 clipboard paste with real Ctrl+V, 1..4096 Unicode characters, no NUL. |
| hotkey | keys: str required | 1..4 comma-separated PyAutoGUI key names. |
| a11y_tree | none | Real upstream AT-SPI XML, at most 2 MiB. |
| run_task_config | task_path: str required | Apply validated supported setup, return applied-step count and current browser geometry. |
| evaluate | task_path: str required | Upstream metric score over actual accessibility state. |
| osworld_desktop_smoke | none | Real offline task and cleanup; no existing session permitted. |

## Configuration

Start a session before observations/actions/tasks. Operations serialize on one lock. Ordinary operations have a 30-second deadline; typing, startup and disposable smoke have 60 seconds. Typing uses native clipboard paste, rather than a long per-key stream; its 60-second bound includes clipboard readiness and cleanup. A deadline, worker failure, Python cancellation or unsupported task stops the owned session; restart explicitly. An HTTP disconnect does not cancel execution. Requests are bounded to 32 KiB and responses to 8 MiB. Children deliberately creating a new session escape the Linux process-group boundary.

HOME is preserved. The worker uses private XDG config/cache/runtime directories, disables Python user-site loading, and owns a private Xauthority cookie, DBus/AT-SPI services and Chromium user-data directory. No user browser profile, inherited display or cloud/model credentials are passed to it. No VNC or upstream arbitrary-code HTTP server listens. Chromium uses `--no-sandbox` inside the outer sandbox. API shell/files remain available; the outer sandbox is the isolation boundary. Set `ABX_SERVER_TOKEN` to restrict callers. Screenshots/trees intentionally reveal the pages you open; browser URLs can use network egress.

`type` overwrites the clipboard on this private display and sends actual Ctrl+V to the focused application. It supports Unicode paste, rather than promising one physical key event per character. Text enters foreground `xclip` 0.13-4 through stdin. After paste, the worker stops and reaps its xclip process and verifies that its clipboard ownership was released. The pasted text remains in the destination application as requested. Typing/hotkeys restore real X input focus only to the main Chrome window whose PID matches the browser launched by this worker; no host/other-session window is targeted. No shared host clipboard is used. Applications that refuse clipboard paste are unsupported by this command.

Upload an OSWorld-shaped JSON task file inside `WORKSPACE` (default `/home/user/app`), at most 64 KiB. Symlinks resolving outside that directory are refused. The supported subset is:

```json
{
  "snapshot": "chrome",
  "config": [{"type":"chrome_open_tabs","parameters":{"urls_to_open":["https://example.com"]}}],
  "evaluator": {
    "func": "check_include_exclude",
    "result": {"type":"accessibility_tree"},
    "expected": {"type":"rule","rules":{"include":["Example Domain"],"exclude":[]}}
  }
}
```

Call `run_task_config` then `evaluate` with that file's `task_path`. Setup accepts only 1..4 HTTP(S) or workspace file URLs and `sleep` 0..5 seconds, with at most 8 steps. Evaluators accept only `check_include_exclude` (nonempty include list) or `exact_match`, the actual `accessibility_tree` getter and a `rule` expectation. Unknown fields/steps, launch/shell/VM/Office/proxy tasks, postconfig and unsupported metrics fail before setup; no skipped step receives credit. Selected unchanged upstream definitions execute without importing cloud/proxy/Office registries. Upstream accessibility's absent LibreOffice version is represented as unknown; no Office binary or version is fabricated. Complete Unicode paste is checked independently in the browser DOM. Astral emoji accessibility observations were not reliable in native task trials; accepted task fixtures use ASCII and CJK. The wrapper returns the actual upstream XML and does not fabricate missing characters or scores.

## Resources

2 vCPU / 2048 MB, generation 2, non-root `user`, port 9000. No KVM, GPU, Docker daemon or extra capabilities. The image includes the browser/system libraries; no runtime GUI download occurs. Its `/home/user/app` directory is explicitly owned by the runtime user for task uploads and disposable fixture writes. The worker explicitly preserves the image's `PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser` when locating the installed browser. Use a disposable sandbox for untrusted pages.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Secondary development

```bash
python scripts/check_template.py osworld
python -m pytest -q osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py
E2E_BASE_URL=http://127.0.0.1:9000 E2E_REQUIRE_DESKTOP=1 E2E_RUN_DESKTOP=1 python osworld/e2e_test.py
```

The required GUI mode fails on missing dependencies. Default local HTTP checks report GUI SKIP without claiming desktop acceptance. The actual image smoke verifies PNG/tree, baseline score 0, native actions, independent browser state, final score 1, changed pixels and cleanup; a marker does not contribute to scoring. The image smoke also pastes 4096 Unicode characters including emoji and independently reads the entire DOM value; task scores use ASCII/CJK, with emoji accessibility representation unverified.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py osworld` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md) and the [template spec](../docs/template-spec.md). Keep the source pin/license, translations, supported subset and acceptance records accurate.

## Issues

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) tracks this slice and remaining full-runtime work. Template defects belong here; SDK/server defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI defects to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Apache-2.0. The original OSWorld files, full [upstream license](upstream/LICENSE) and source SHA256 manifest are retained. PyAutoGUI and dependencies retain their installed distribution licenses; Chromium and Debian packages retain their installed notices.

The 1024×768 PNG/Xvfb screen and the browser page viewport are separate measurements. Browser initialization requires a visible, nonzero viewport; it does not resize/emulate a page to force screen equality. `desktop_start` and `run_task_config` return `browser_geometry` with numeric screen, outer-window, viewport and content-offset fields. The disposable smoke prints only these numeric fields for image diagnostics. Native click coordinates remain screen coordinates. The smoke uses the actual content offset and DOM rectangle, and still requires real input, upstream score 0→1, changed PNG pixels and complete 4096-character destination readback. See the [viewport follow-up](../.agents/evidence/verify/2026-10-16-osworld-viewport.md).

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).

### Current platform-step acceptance

[Current-version genuine steps](evidence/express-2026-10-20.json) and [basic external HTTP result](evidence/verification-steps-2026-10-20T151021Z.json): official READY, actual Python SDK creation, CLI/SDK smoke and 6 PASS / 0 FAIL / 1 GUI SKIP; 346.984 seconds. Independent owned sandbox/template and private asset-cache cleanup passed. Earlier failed step attempts remain historical failures; this receipt is model-free and does not extend prior image/model scope.

The skipped case was the external desktop tier, not a model case. The internal named desktop smoke passed separately. Full external desktop acceptance requires both desktop opt-ins and all18 checks without skips; the following genuine SDK-created run completes that tier.

[Current required external desktop result](evidence/verification-steps-2026-10-20T171144Z.json) and [canonical CLI/SDK receipt](evidence/express-2026-10-20T171144Z.json):18 PASS/0 FAIL/0 SKIP in274.783seconds, actual SDK-created native steps. The original external controller verified real PNG/input/Unicode/hotkey/AT-SPI/upstream score0→1 and changed pixels, followed by desktop/task cleanup and independent sandbox/template/private-cache absence. Both required desktop flags are recorded. This completes the external browser-slice tier; no full benchmark/model/VM-reset capability is inferred.
