# OSWorld Linux browser slice

[中文](README.zh-CN.md)

## What it does

A real private Xvfb/Openbox/Chromium desktop with [OSWorld](https://github.com/xlang-ai/OSWorld) screenshots, Linux AT-SPI, native mouse/keyboard actions and private-clipboard Unicode paste and selected task evaluators. This is an independent Alibaba template. Full OSWorld benchmark execution, VM snapshots, Office and a model agent are outside this browser slice; [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) tracks delivery of this slice.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

OSWorld source `b138d348256078fa634fc3b73567a7337c793e6b` (Apache-2.0); Playwright 1.58.0 with its Chromium revision; PyAutoGUI 0.9.54; Pillow 11.3.0; Flask 3.1.2; NumPy 2.3.3; lxml 6.0.1; requests 2.32.5. The complete Python dependency graph is [hash locked](requirements.txt). Debian 13 x86_64 critical desktop packages have exact pins; transitive OS dependencies remain repository-resolved. See [Dockerfile](Dockerfile), [source attribution](upstream/source.json) and [design](../docs/design/osworld.md).

## Problem solved

Use real browser desktop observations and actions on Express without KVM, a Docker daemon or elevated runtime privileges. Failed or unsupported tasks are errors, rather than fabricated benchmark scores.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//osworld --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" desktop_start --json-args '{}'
abx run "$SANDBOX_ID" a11y_tree --json-args '{}'
```

Returns the live desktop accessibility XML. Use `screenshot`, `click`, `type` and `hotkey` against that same session.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            await client.commands.run('desktop_start')
            result = await client.commands.run('a11y_tree')
            print(result)
        finally:
            try:
                await client.commands.run('desktop_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

First call, in order:

- `POST /commands/desktop_start` with `{}`.

`POST /commands/a11y_tree`

```json
{}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

After use, call:

- `POST /commands/desktop_stop` with `{}`.

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

No model account is required. Commands operate a Linux browser-desktop slice, not the full OSWorld VM/Office/arbitrary-task harness or a planning agent. External agents must configure their own model and accounts.

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

Call `run_task_config` then `evaluate` with that file's `task_path`. Setup accepts only 1..4 HTTP(S) or workspace file URLs and `sleep` 0..5 seconds, with at most 8 steps. Evaluators accept only `check_include_exclude` (nonempty include list) or `exact_match`, the actual `accessibility_tree` getter and a `rule` expectation. Unknown fields/steps, launch/shell/VM/Office/proxy tasks, postconfig and unsupported metrics fail before setup; no skipped step receives credit. Selected unchanged upstream definitions execute without importing cloud/proxy/Office registries. Upstream accessibility's absent LibreOffice version is represented as unknown; no Office binary or version is fabricated. Clipboard paste supports Unicode, but the upstream accessibility tree may omit some astral emoji. The wrapper returns the actual upstream XML and does not fabricate missing characters or scores.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx run "$SANDBOX_ID" desktop_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU / 2048 MB, generation 2, non-root `user`, port 9000. No KVM, GPU, Docker daemon or extra capabilities. The image includes the browser/system libraries; no runtime GUI download occurs. Its `/home/user/app` directory is explicitly owned by the runtime user for task uploads and disposable fixture writes. The worker explicitly preserves the image's `PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser` when locating the installed browser. Use a disposable sandbox for untrusted pages.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/osworld.md).

## Issues

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) tracks this slice and remaining full-runtime work. Template defects belong here; SDK/server defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), and CLI defects to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Apache-2.0. The original OSWorld files, full [upstream license](upstream/LICENSE) and source SHA256 manifest are retained. PyAutoGUI and dependencies retain their installed distribution licenses; Chromium and Debian packages retain their installed notices.

The 1024×768 PNG/Xvfb screen and the browser page viewport are separate measurements. Browser initialization requires a visible, nonzero viewport; it does not resize/emulate a page to force screen equality. `desktop_start` and `run_task_config` return `browser_geometry` with numeric screen, outer-window, viewport and content-offset fields. The disposable smoke prints only these numeric fields for image diagnostics. Native click coordinates remain screen coordinates. The smoke uses the actual content offset and DOM rectangle, and still requires real input, upstream score 0→1, changed PNG pixels and complete 4096-character destination readback. See the [viewport follow-up](../.agents/evidence/verify/2026-10-16-osworld-viewport.md).

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).

An empty native AT-SPI attribute hash table is read as an empty mapping so the upstream XML traversal can retain its real child nodes. No accessibility nodes or attributes are fabricated; native errors still propagate and vendored upstream handler/evaluator bytes remain unchanged.
