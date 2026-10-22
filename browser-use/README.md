# Browser-use

[中文](README.zh-CN.md).

## What it does

Runs the actual browser-use0.13.11 agent on a private local Chromium browser. It reads text DOM, performs browser interactions and returns a real PNG plus final URL/result. This complements model-free Playwright primitives; it does not use Browser Use Cloud or a remote browser.

## Stack

FC base v0.0.49/generation2/non-root Linux x86_64/Python3.13. [requirements.lock](requirements.lock) pins browser-use0.13.11 and every transitive version/SHA256; [requirements.in](requirements.in) is compiled by uv0.11.28. The package uses CDP-use, not a Python Playwright dependency. An explicitly pinned Playwright1.58.0 installer selects Chromium1208/Google Chrome for Testing145.0.7632.6; --no-shell avoids another headless-shell copy. Server source is fixede2cb27e or injected matching wheel.

## Problem solved

Give a real model a local browser inside an owned sandbox, with independent artifact retrieval and process cleanup. Text-DOM use_vision=false needs no vision-capable model. Cloud browser billing/accounts, browser extensions and arbitrary local files/shell are outside this profile.

## Quick start (CLI)

```bash
abx template deploy ./browser-use -y
abx create --template <template-id> --timeout 900 -y
abx run <sandbox-id> browser_use_version
abx run <sandbox-id> browser_use_setup_check
abx run <sandbox-id> browser_use_self_test
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Deploy/create return the template/sandbox IDs above. Native version/setup/self-test require no model key; expected self-test result is BROWSER_USE_NATIVE_OK. See [entry compatibility and provider setup](../docs/using-templates.md#client-entry-compatibility). Create-time environment does not reconfigure a prewarmed server. Use the explicit SDK process-start example for real model settings.

## Quick start (Python SDK)

Install agent-sandbox-client using the [pinned client source instructions](../docs/python-client-installation.md). The same native self-test is followed by an optional real model turn. Set the three BROWSER_USE model variables in the operator environment first; remove the optional turn for a keyless test.

```python
import asyncio
import os
from pathlib import Path
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900)
    clients = []
    try:
        native = sb.server_at(9000)
        clients.append(native)
        print(await native.commands.run("browser_use_self_test", timeout=90))
        # Optional real model turn; these three variables hold model settings.
        model = await sb.start_server(
            port=9010, commands="/home/user/app/commands.py", timeout=60,
            token=secrets.token_urlsafe(32),
            env={"BROWSER_USE_API_KEY": os.environ["BROWSER_USE_API_KEY"],
                 "BROWSER_USE_BASE_URL": os.environ["BROWSER_USE_BASE_URL"],
                 "BROWSER_USE_MODEL": os.environ["BROWSER_USE_MODEL"]})
        clients.append(model)
        result = await model.commands.run(
            "browser_use", task="Read the heading and summarize it briefly.",
            url="https://example.com/", max_steps=8,
            command_timeout=300, timeout=360)
        if not result["done"] or not result["success"]:
            raise RuntimeError("Native browser agent did not complete the task")
        png = await sb.files.read_bytes(result["screenshot_path"], max_bytes=16*1024**2)
        output = Path("browser-use-" + secrets.token_hex(8) + ".png")
        with output.open("xb") as file:
            file.write(png)
        print(result["result"], output)
    finally:
        await asyncio.gather(*(client.aclose() for client in clients), return_exceptions=True)
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

The example owns this sandbox, exports its PNG before deletion, and closes HTTP clients before destroying the sandbox. ServerClient.aclose only closes HTTP resources; sb.kill supplies final remote process cleanup here. This example is source/syntax checked; provider/model claims require executed receipts.

## Quick start (HTTP POST)

Set ABX_SERVER_URL to the SDK network.get_url(9000) of a running template and ABX_SERVER_TOKEN to its process token if configured.

```bash
curl --fail-with-body --max-time 90 -X POST "$ABX_SERVER_URL/commands/browser_use_self_test" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{}'
```

Response: {"result":"BROWSER_USE_NATIVE_OK"}. For the SDK-started configured9010 server, use its URL/token and POST /commands/browser_use with {"task":"Read the heading","url":"https://example.com/","max_steps":8,"command_timeout":300}. HTTP200 wraps the structured output in result; done/success describe the native outcome and must both be true for successful completion. Parameters missing/undeclared/mistyped400, bearer mismatch401, unknown command404; invalid limits/config/path/pins/busy/deadline/native execution500 with error/type. Buffered response; client timeout/disconnection does not guarantee cancellation.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| browser_use_version | none | actual installed0.13.11 string |
| browser_use_setup_check | none | installed/version/browser_installed and api_key_set/base_url_set/model_set flags |
| browser_use_self_test | none | BROWSER_USE_NATIVE_OK only after native CDP navigation/title/PNG and cleanup; no model |
| browser_use | task:str required, nonempty/no NUL/max256KiB UTF-8; url:str="", HTTP(S)/no userinfo/max8192 UTF-8 bytes; max_steps:int=8,1..20; command_timeout:int=300,1..900seconds | {result:str,final_url:str,screenshot_path:str,bytes:int,steps:int,done:bool,success:bool} |

The native worker uses explicit Agent/BrowserSession/BrowserProfile/ChatOpenAI, no automatic cloud selection. Compatible text JSON is parsed by native browser-use; add_schema_to_system_prompt=true and dont_force_structured_output=true avoid requiring a provider-specific strict response-format API.

Exactly15 native actions are enabled: done/navigate/click/input/scroll/wait/go_back/switch/close/find_text/find_elements/search_page/select_dropdown/dropdown_options/send_keys. The registry is checked before and after Agent construction. Filesystem/shell/evaluate/extract/upload/PDF/search and screenshot-as-agent-action are excluded. The wrapper takes its own actual screenshot at completion. New random artifact names are never caller-specified or overwritten. PNG16MiB is a post-render limit. The URL is read from the actual current target; a model statement alone is not verification.

## Configuration

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| BROWSER_USE_API_KEY | model turns | empty | explicitly supplied compatible-model credential, not Browser Use Cloud |
| BROWSER_USE_BASE_URL | model turns | empty | HTTP(S) model API; no userinfo/query/fragment |
| BROWSER_USE_MODEL | model turns | empty | explicit compatible chat model ID |
| BROWSER_USE_PYTHON | no | /opt/browser-use/bin/python | hash-locked native environment; actual0.13.11 checked |
| PLAYWRIGHT_BROWSERS_PATH | no | /opt/playwright | installed Chromium1208 cache |
| BROWSER_USE_BROWSER_BINARY | diagnostics | Chromium1208/chrome-linux64/chrome | executable override; actual145.0.7632.6 still required |
| WORKSPACE | no | /home/user/app | owned root for new browser-use-artifacts PNGs |
| ABX_SERVER_TOKEN | no | empty | command-server process bearer token |

Model settings enter private file stdin only; they are not inherited into Chromium. Every call has fresh HOME/XDG/profile/native file-system state. Disable native telemetry/cloud sync/default extensions and use_cloud; no caller profile or saved browser account is imported. CDP launch requests loopback binding and only command9000 is advertised. This container-only profile explicitly sets chromium_sandbox=false instead of relying on Docker detection; the owned sandbox supplies OS isolation. The browser and model still have sandbox-user authority and network access; these action restrictions are not another OS isolation boundary. Returned result/PNG can contain private webpage information; exact configured model key/base values are redacted from result strings.

## Resources

2vCPU/2048MB, named-command9000, optional explicit model server9010; the separate SDK verification fixture uses9011. --disable-dev-shm-usage avoids relying on a large /dev/shm. One browser operation per server; concurrent heavy calls fail busy500. max_steps1..20; max3 actions/step; model90seconds/0retry/4096tokens; native action30/step120/LLM100second guards; outer command1..900seconds plus bounded cleanup. Each captured stream256KiB. Private browser/config/files/processes removed on ordinary success/failure/deadline; the PNG remains caller-owned. Sandbox deletion is the final boundary after abrupt server loss or hostile same-user code. Image rootfs has an8GiB build gate.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.0; regular image, actual CLI/SDK, complete HTTP 11 PASS / 0 FAIL / 1 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T144122Z.json) |
| opensandbox | 1.0.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 11 PASS / 0 FAIL / 1 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T110655Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

| Provider | Version and executed scope | Evidence |
| --- | --- | --- |
| alicloud-express |1.0.0; actual SDK-created non-root image, CLI/SDK/CDP, real model counter3/submitted nonce/independent PNG and owned cleanup | [image](evidence/express-2026-10-20.json) · [model](evidence/model-image-2026-10-20T144123Z.json) |

The native agent succeeds in8steps; one recovered native JSON-format error remains in its receipt. Basic full HTTP has11PASS/1SKIP with the model explicitly disabled; the separate actual model controller passes. Independent cleanup confirms sandbox/template/registry absence and controller-owned processes/files/9010/9011listeners. The native platform-step build remained building at1200seconds and failed that attempt; owned template deletion was independently confirmed. No passing step build is claimed. Other providers/architectures remain unverified. See [final acceptance](../.agents/evidence/verify/2026-10-20-browser-use-final.md).

</details>

## Secondary development

Restore the locked dependency venv with python -m venv <new-prefix>, then <new-prefix>/bin/python -m pip install --require-hashes -r browser-use/requirements.lock and pip check. Set BROWSER_USE_PYTHON to the venv path without resolving its Python symlink; provide the actual pinned browser cache/path. Run python -m pytest -q browser-use/test_commands.py browser-use/test_model_controller.py. Fixtures are authored responses/programs, never real generated shell on the operator host.

[Platform steps](../docs/platform-steps.md): python scripts/prepare_steps.py browser-use --output /tmp/browser-use-steps prepares; python scripts/run_steps_e2e.py browser-use --timeout 1200 executes. Preparation is not a provider pass. The full HTTP controller is model-off; real model acceptance is a separate SDK command: python browser-use/model_e2e_test.py --sandbox-id <owned-fresh-sandbox-id>. It requires pinned client/httpx/Pillow plus the three BROWSER_USE model variables and free9010/9011, owns only its fixture/server/files, independently checks counter3/submitted nonce/PNG and listener/file absence, and preserves the caller sandbox. Destroy that owned sandbox separately after export.

## Contributing

Follow [CONTRIBUTING](../CONTRIBUTING.md), [spec](../docs/template-spec.md), [design](../docs/design/browser-use.md) and both language API/limit/evidence contracts. Shared strict SHA256-lock support depends on [PR146](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/146) landing first.

## Issues

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51); templates/catalog [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues), client/server [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), CLI [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Wrapper code is [Apache-2.0](../LICENSE). Browser-use is MIT; preserve the [unchanged upstream license](upstream-LICENSE). The unmodified Playwright-distributed Chrome for Testing build retains its bundled license/notices; Playwright is Apache-2.0. Every hash-locked dependency keeps its installed upstream notices; do not relabel the full image as Apache-2.0. No model weights or cloud service account is included.

Failed native steps include at most20 error summaries, each truncated to1024 UTF-8 bytes after exact configured model-key/endpoint redaction. The SDK controller retains safe failure/cleanup facts before asserting acceptance.

### Current platform-step acceptance

[Real1.0.0 steps](evidence/express-2026-10-20T153859Z.json) and [original full HTTP controller](evidence/verification-steps-2026-10-20T153859Z.json): official READY, actual Python SDK creation, every CLI/SDK smoke, native CDP navigation/title/PNG self-test and11 HTTP PASS/0 FAIL/1 model SKIP;224.94s. The executable was the actual freshly website-installed CLI0.4.1 with first-root --native and NODE_PATH unset; no external SDK module injection. Independent sandbox/template and exact private-cache cleanup passed. Python3.13, package/hash locks, pinned Chromium --no-shell, non-root runtime and8GiB rootfs assertions remain unchanged. Earlier failed steps remain historical failures; this receipt does not relabel the separate image/model result.
