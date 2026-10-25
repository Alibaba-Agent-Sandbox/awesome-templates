# desktop

[中文](README.zh-CN.md)

## What it does

Create an instance of the E2B-managed `desktop` template with an E2B account.

## Stack

The [E2B Desktop source](https://github.com/e2b-dev/desktop/tree/9fe5f55fabe3bd9f0277661a830e1d228b463b44) defines an Ubuntu/Xfce desktop image. The deployed template is managed by E2B.

## Problem solved

Access an existing desktop environment. Shell/files use Agent Sandbox; screenshots and desktop input use the upstream E2B Desktop SDK.

## Quick start (CLI)

Use CLI 0.5.6 or later and the current managed catalog; see [installation and provider setup](../../using-templates.md). The historical verification below covers its recorded create/exec interfaces, not a rerun of this catalog launch command.

Install the [CLI](../../using-templates.md) and Node.js 22+, configure your provider below, and replace `<sandbox-id>` with the ID returned by launch.

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//e2b --allow-unpinned --yes
abx provider doctor e2b
abx --provider e2b template launch desktop --sandbox-timeout 180 --yes
abx --provider e2b exec <sandbox-id> -- python3 -c 'print(6*7)'
abx --provider e2b kill <sandbox-id> -y
```

## Quick start (Python SDK)

Install the [Python client](../../python-client-installation.md) and the same provider plugin; keep Node.js on PATH for the provider engine.

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="e2b", template="desktop", timeout=180)
    try:
        result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
        print(result.stdout)  # 42
        await sb.files.write("/tmp/example.txt", "hello")
        print(await sb.files.read("/tmp/example.txt"))
        await sb.files.remove("/tmp/example.txt")
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

## Quick start (HTTP POST)

This image does not contain the project `/commands/*` application server. Use the provider SDK for lifecycle and process/file operations, and the upstream Desktop SDK for screenshot/input operations.

## Command reference

`ProviderSandbox.create` creates an instance; `commands.run` returns `exit_code/stdout/stderr`; `files.write/read/remove` operate on files. `kill` deletes the instance; `close` releases local connections.

## Configuration

Set `ABX_E2B_API_KEY` to your E2B account credential. Set `ABX_E2B_BASE_URL` and `ABX_E2B_DOMAIN` only for deployments that require them. See the [E2B provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/tree/main/e2b).

## Resources

The timeout is in seconds. CPU, memory and image availability depend on your deployment. Delete instances after use.

## Verified

The CLI/SDK examples have been checked against their interfaces; there is no recorded live E2B desktop run. See the [2026-10-21 review](../evidence/verification-desktop-2026-10-21.json).

## Secondary development

Use the upstream E2B Desktop project for desktop customization. The separate [OSWorld source template](../../../osworld/README.md) is available for an Express-based workflow.

## Contributing

Follow [CONTRIBUTING](../../../CONTRIBUTING.md). Keep both languages aligned and preserve dated test records.

## Issues

[Report a template issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Provider integration belongs to [awesome-providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues).

## License

Authored documentation/tests: Apache-2.0. The upstream image, SDKs and bundled applications retain their own licenses and terms.
