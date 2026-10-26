# base

[中文](README.zh-CN.md)

## What it does

Alibaba Express manages the `base` template and its image. Create an instance directly; no image build is needed.

## Stack

The managed image supplies Python 3.13 and Node.js 20. The provider can update this image; query installed versions when your application needs specific dependencies.

## Problem solved

Run shell commands and work with files without preparing an image.

## Quick start (CLI)

Before either CLI launch or Python creation, set the following in your local terminal. Obtain all three values for the **same region** from the Alibaba Express console; the API key must have access to the managed template.

```bash
export ABX_SANDBOX_API_KEY='<sandbox-api-key>'
export ABX_SANDBOX_BASE_URL='<sandbox-api-url>'
export ABX_SANDBOX_DOMAIN='<sandbox-domain>'
```

Replace the three placeholders with your Sandbox API key, API URL and sandbox domain; the domain is a hostname, not a URL. These are platform credentials, not an LLM API key. This managed-image example needs no model, model endpoint, model key, application token or interactive login. Creating this existing image does not require Docker, an ACR namespace or image-build AccessKeys. Use the [provider setup guide](../../using-templates.md) if your account settings differ.

Use CLI 0.5.6 or later and the current managed catalog; see [installation and provider setup](../../using-templates.md).

Install [CLI and provider configuration](../../using-templates.md), then replace `<sandbox-id>` with the ID returned by launch.

```bash
abx --provider alicloud-express template launch base --sandbox-timeout 180 --yes
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx --provider alicloud-express exec "$ABX_SANDBOX_ID" -- python3 -c 'print(6*7)'
abx --provider alicloud-express kill "$ABX_SANDBOX_ID"
```

## Quick start (Python SDK)

Install the [Python client](../../python-client-installation.md) and configure the same Express account. This example prints `42`, writes and reads a file, then deletes its sandbox.

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="alicloud-express", template="base", timeout=180)
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

This managed image does not supply the project `/commands/*` application server. Use the process and file APIs above. For custom HTTP commands, create a [source template](../../../_skeleton/README.md).

## Command reference

`ProviderSandbox.create(provider=..., template=..., timeout=...)` creates an instance; `commands.run` returns `exit_code`, `stdout` and `stderr`; `files.write/read/remove` operate on sandbox paths. `kill` deletes the instance and `close` releases local connections.

The current Express provider does not implement `ProviderSandbox.run_code` (`E8004`). Use `commands.run` for Python processes as above. A persistent kernel or interpreter session requires its own supported interface.

## Configuration

Use the Express account settings in the [usage guide](../../using-templates.md). No model credential is needed for this example. For prewarmed processes, see [runtime environment](../../runtime-environment.md).

## Resources

Choose a finite timeout in seconds and delete instances when finished. CPU, memory and image updates are managed by the provider.

## Contributing

Follow [CONTRIBUTING](../../../CONTRIBUTING.md). Keep both languages aligned and add a new dated record for a new runtime test.

## Issues

[Report a template issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).

## License

Documentation and verification scripts: Apache-2.0. The provider-managed image and its bundled software retain their own licenses.
