# polyglot-toolchain

[中文](README.zh-CN.md)

## What it does

Runs Go 1.25.14, Rust/Cargo 1.90.0 and Eclipse Temurin JDK 21.0.12.1+1 in one non-root sandbox. `toolchain_smoke` compiles and executes a separate program with each language, then removes its owned sources, binaries and Go cache.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49, generation 2, 2 vCPU / 2048 MB, agent-sandbox-server on port 9000. Official upstream archives and SHA256 for x86_64/aarch64 are pinned in [toolchains.json](toolchains.json). No rustup, version manager or runtime automatic Go toolchain download. Rustc, the target standard library and Cargo are installed as individual official components. GCC supplies the system linker. The installer rejects actual rootfs use above 8 GiB.

## Problem solved

Coding agents can build Go, Rust and Java projects without installing compilers during a model turn. No API key is required; compilation smoke is entirely local. Dependency downloads for user projects remain caller-controlled.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//polyglot-toolchain --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" toolchain_smoke --json-args '{}'
```

Compiles and runs Go, Rust and Java examples; returns `go: GO_OK`, `rust: RUST_OK`, `java: JAVA_OK` and `cleanup_verified: true`.

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
            result = await client.commands.run('toolchain_smoke')
            print(result)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/toolchain_smoke`

```json
{}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| toolchain_versions | none | version/disk/non_root object |
| toolchain_smoke | none | go/rust/java/cleanup_verified object |

Both commands take no parameters. `toolchain_versions() -> dict` returns actual version lines, used/free rootfs bytes and non-root state; absent local compilers return null. `toolchain_smoke() -> dict` requires all compilers, invokes `go build`, `rustc`, `javac` and the resulting programs, and requires `{go: GO_OK, rust: RUST_OK, java: JAVA_OK, cleanup_verified: true}`. Each trusted subprocess has a 90-second deadline and owned process-group cleanup. No caller-provided program or shell string is accepted by these inspection commands.

## Configuration

No model key. Export `ABX_SERVER_TOKEN` before application launch; the manifest declares its name with an empty value. `JAVA_HOME=/opt/toolchains/java`, `GOTOOLCHAIN=local`; image PATH selects only the pinned toolchains. The smoke owns its Go build cache and removes it.

Native children use a filtered runtime environment with a 90-second deadline and owned-process cleanup.

The legacy `rootfs_used_bytes` and `rootfs_free_bytes` response keys are visible-filesystem statvfs counters, which may include shared backing storage. They are capacity diagnostics, not image-layer size or acceptance of the8GiB image budget; the installer separately uses `du -sx` for that budget.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2 vCPU, 2048 MB, port 9000. Installer rejects actual used rootfs above 8 GiB. Non-root runtime; no KVM, Docker or additional capabilities. Each tool subprocess deadline is 90 seconds. Temporary source/binary/cache artifacts are deleted before a successful response.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/polyglot-toolchain.md).

## Issues

CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

Report template defects at [awesome-templates Issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Delivery is tracked in [Issue 62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62). SDK defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template: Apache-2.0. Go: BSD-3-Clause plus bundled notices. Rust: MIT OR Apache-2.0 and third-party notices. Eclipse Temurin/OpenJDK: GPL-2.0 WITH Classpath-exception-2.0 and upstream legal notices. Original LICENSE/COPYRIGHT/legal files remain in the installed distributions; see [Go](https://go.dev/LICENSE), [Rust](https://github.com/rust-lang/rust/tree/1.90.0), and [Temurin](https://github.com/adoptium/temurin21-binaries/releases).
