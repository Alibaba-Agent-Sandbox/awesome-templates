# polyglot-toolchain

## What it does

Runs Go 1.25.14, Rust/Cargo 1.90.0 and Eclipse Temurin JDK 21.0.12.1+1 in one non-root sandbox. `toolchain_smoke` compiles and executes a separate program with each language, then removes its owned sources, binaries and Go cache.

## Stack

Alibaba FC base v0.0.49, generation 2, 2 vCPU / 2048 MB, agent-sandbox-server on port 9000. Official upstream archives and SHA256 for x86_64/aarch64 are pinned in [toolchains.json](toolchains.json). No rustup, version manager or runtime automatic Go toolchain download. Rustc, the target standard library and Cargo are installed as individual official components. GCC supplies the system linker. The installer rejects actual rootfs use above 8 GiB.

## Problem solved

Coding agents can build Go, Rust and Java projects without installing compilers during a model turn. No API key is required; compilation smoke is entirely local. Dependency downloads for user projects remain caller-controlled.

## Quick start (CLI)

Use the native CLI syntax (`abx create --help` lists `--template`):

```bash
abx template deploy ./polyglot-toolchain -y
abx create --template <template-id> --timeout 300 -y
abx run <sandbox-id> toolchain_versions
abx run <sandbox-id> toolchain_smoke
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

For the standard CLI entry and paired client installation, see [using templates](../docs/using-templates.md).

## Quick start (Python SDK)

Install the [paired `agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("toolchain_versions"))
        print(await sb.run("toolchain_smoke"))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

Response: `{"result":{"go":"GO_OK","rust":"RUST_OK","java":"JAVA_OK","cleanup_verified":true}}`.

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' \
  -d '{}' '<sandbox-port-9000-url>/commands/toolchain_smoke'
```

The server token is set in the named-command server process. See [runtime environment](../docs/runtime-environment.md).

HTTP 200 wraps the result in `result`; invalid arguments return 400, missing/invalid server authentication 401, and execution errors 500. Output is buffered; allow a client deadline above the complete multi-compiler workflow. These CLI/SDK/HTTP snippets describe the public operations; the executed cloud scope is recorded in Verified.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| toolchain_versions | none | version/disk/non_root object |
| toolchain_smoke | none | go/rust/java/cleanup_verified object |

Both commands take no parameters. `toolchain_versions() -> dict` returns actual version lines, used/free rootfs bytes and non-root state; absent local compilers return null. `toolchain_smoke() -> dict` requires all compilers, invokes `go build`, `rustc`, `javac` and the resulting programs, and requires `{go: GO_OK, rust: RUST_OK, java: JAVA_OK, cleanup_verified: true}`. Each trusted subprocess has a 90-second deadline and owned process-group cleanup. No caller-provided program or shell string is accepted by these inspection commands.

## Configuration

No model key. `ABX_SERVER_TOKEN` is an optional empty manifest placeholder; inject the value into the server process. `JAVA_HOME=/opt/toolchains/java`, `GOTOOLCHAIN=local`; image PATH selects only the pinned toolchains. The smoke owns its Go build cache and removes it.

Version1.0.1 explicitly owns the runtime workspace. Native children inherit only PATH/HOME/JAVA_HOME/TMPDIR plus fixed locale and GOTOOLCHAIN=local; cloud/model/server credentials and injected compiler/loader options are excluded. Output is drained concurrently with a256KiB limit per stream, a90-second deadline and owned group cleanup. Earlier1.0.0 attempts do not qualify this changed profile.

The legacy `rootfs_used_bytes` and `rootfs_free_bytes` response keys are visible-filesystem statvfs counters, which may include shared backing storage. They are capacity diagnostics, not image-layer size or acceptance of the8GiB image budget; the installer separately uses `du -sx` for that budget.

## Resources

2 vCPU, 2048 MB, port 9000. Installer rejects actual used rootfs above 8 GiB. Non-root runtime; no KVM, Docker or additional capabilities. Each tool subprocess deadline is 90 seconds. Temporary source/binary/cache artifacts are deleted before a successful response.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.1; regular image, actual CLI/SDK, complete HTTP 1 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T070826Z.json) |
| opensandbox | 1.0.1; original Docker backend, every CLI/SDK named smoke, complete HTTP 1 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T112736Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

| Provider | Scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.0.1 actual exact-source CI image, native registration/official READY, CLI and SDK; pinned Go/Rust/Java compilation, execution and owned cleanup through external HTTP; no skips | [canonical receipt](evidence/express-2026-10-20.json), [complete HTTP](evidence/image-http-2026-10-20T070826Z.json) |

Sandbox/template/registry cleanup and registry digest after runtime were independently read back. This is actual image acceptance, not platform-step success. The earlier 1.0.0 archive failure and step attempt remain history. Status is experimental; other providers remain unverified.

</details>

## Secondary development

Change the official archive/version/hash together and retain upstream licenses. Use [platform steps](../docs/platform-steps.md) with `python scripts/prepare_steps.py polyglot-toolchain --output /tmp/toolchain-steps`. That prepares files only. Real Express acceptance: `python scripts/run_steps_e2e.py polyglot-toolchain --timeout 1800`; Dockerfile acceptance remains `python scripts/express_e2e.py polyglot-toolchain`. Run L0 with `python scripts/run_local_e2e.py`; a host lacking the exact tools reports a skip. Images must compile all three, and local absence cannot certify them.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), the [spec](../docs/template-spec.md) and [design](../docs/design/polyglot-toolchain.md). Keep both README languages and immutable receipts current.

## Issues

CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

Report template defects at [awesome-templates Issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Delivery is tracked in [Issue 62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62). SDK defects belong to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template: Apache-2.0. Go: BSD-3-Clause plus bundled notices. Rust: MIT OR Apache-2.0 and third-party notices. Eclipse Temurin/OpenJDK: GPL-2.0 WITH Classpath-exception-2.0 and upstream legal notices. Original LICENSE/COPYRIGHT/legal files remain in the installed distributions; see [Go](https://go.dev/LICENSE), [Rust](https://github.com/rust-lang/rust/tree/1.90.0), and [Temurin](https://github.com/adoptium/temurin21-binaries/releases).

### Additional current-version platform-step acceptance

[Actual steps](evidence/express-2026-10-20T135358Z.json) and [external HTTP attempt](evidence/verification-steps-2026-10-20T135358Z.json): official READY, Python SDK creation, CLI/SDK smoke and 1 HTTP PASS / 0 FAIL / 0 SKIP. Model calls remain NOT_RUN in this receipt. Independent sandbox/template and private same-account asset-cache object/bucket cleanup passed before publication. Earlier image/model receipts retain their own scope.
