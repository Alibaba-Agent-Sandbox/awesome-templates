# apply-patch

## What it does

Runs the actual official Codex *** Begin Patch dialect: add, update, move and delete. Patch bytes enter native stdin through a private temporary file, without a shell or patch text in argv.

## Stack

Alibaba FC base v0.0.49, generation2, non-root user. `npm ci --ignore-scripts` installs official @openai/codex0.162.1/native architecture packages using [lockfile integrity](package-lock.json). The validated native binary is dispatched by apply_patch argv0. The corresponding official release tag points to [092d3acd](https://github.com/openai/codex/tree/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d). This uses official prebuilt packages; it does not claim a local rebuild from that source commit.

## Problem solved

Supplies the real Codex file tool without a model account, Rust compiler, Docker or KVM. Linux x86_64/aarch64 only.

## Quick start (CLI)

Native CLI syntax; see [entry compatibility](../docs/using-templates.md#client-entry-compatibility) for the standard entry.

```bash
abx template deploy ./apply-patch -y
abx create --template <template-id> --timeout 300 -y
abx run <sandbox-id> apply_patch_smoke
abx run <sandbox-id> apply_patch --arg 'patch_text=*** Begin Patch
*** Add File: hello.txt
+hello
*** End Patch'
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## Quick start (Python SDK)

Install the paired [`agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        patch = "*** Begin Patch\n*** Add File: hello.txt\n+hello\n*** End Patch\n"
        result = await sb.run("apply_patch", patch_text=patch)
        assert result["exit_code"] == 0
        assert await sb.files.read("/home/user/app/hello.txt") == "hello\n"
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' \
  -d '{"patch_text":"*** Begin Patch\n*** Add File: hello.txt\n+hello\n*** End Patch\n"}' \
  '<sandbox-port-9000-url>/commands/apply_patch'
```

Response envelope: `{"result":{"stdout":"...","stderr":"","exit_code":0}}`.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| apply_patch | patch_text: str required, nonempty UTF-8 up to256KiB; cwd: str optional empty=WORKSPACE, existing subdirectory | {stdout: str, stderr: str, exit_code: int} from actual native parser |
| apply_patch_version | none | actual native `codex-cli 0.162.1` |
| apply_patch_smoke | none | APPLY_PATCH_OK only after real add/update/move/delete/literal bytes and owned cleanup |

Upstream failures retain nonzero exit_code; HTTP200 means the invocation completed, not that patching succeeded. Missing/undeclared arguments return400 and unknown command404. The SDK coerces scalar JSON values to declared strings; malformed patches still fail in the native parser. File and move paths must be relative to cwd; absolute paths, .., backslashes and existing symlinks are rejected before executing any part. An upstream failure may leave partial in-workspace edits; patching is not transactional.

## Configuration

No model key. WORKSPACE defaults to /home/user/app. Inject the optional ABX_SERVER_TOKEN in the server process; see [runtime environment](../docs/runtime-environment.md). Native patch subprocesses receive only PATH and LANG, without model/cloud credentials.

## Resources

2vCPU,2048MB,port9000. Each patch has a30-second deadline and256KiB per-output-stream limit. Owned process groups are stopped before reaping the original leader. Temporary patch files close automatically; caller modifications persist. Path preflight is not an OS isolation boundary against concurrent same-user rename/symlink races.

## Verified

No provider has a passing run recorded for this template.

## Secondary development

Prepare [platform steps](../docs/platform-steps.md): `python scripts/prepare_steps.py apply-patch --output /tmp/patch-steps`; real acceptance: `python scripts/run_steps_e2e.py apply-patch`. For local runs use `npm ci --prefix apply-patch --ignore-scripts`, run install_alias.py into a separate bin directory, and put it on PATH before tests. Update lockfile, native version, release source and notices together; retain historical evidence.

## Contributing

Follow [CONTRIBUTING.md](../CONTRIBUTING.md), [spec](../docs/template-spec.md) and [design](../docs/design/apply-patch.md).

## Issues

[Template Issue60](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/60); CLI defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template and Codex: Apache-2.0. Retain pinned-source [upstream-LICENSE](upstream-LICENSE) and official native npm metadata/notices.
