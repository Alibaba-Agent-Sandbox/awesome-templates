# code-interpreter-v1

[中文](README.zh-CN.md)

## What it does

Alibaba Express manages the `code-interpreter-v1` template and its image. Create an instance directly; no image build is needed.

## Stack

The [2026-10-19 inventory](../evidence/code-interpreter-v1-2026-10-19T154153Z.json) observed Python 3.13 and Node.js 20, with numpy, pandas and matplotlib. The provider can update this image; query installed versions when your application needs specific dependencies.

## Problem solved

Run Python data processing with preinstalled numerical packages.

## Quick start (CLI)

Install [CLI and provider configuration](../../using-templates.md), then replace `<sandbox-id>` with the ID returned by create.

```bash
abx --provider alicloud-express create --template code-interpreter-v1 --timeout 180 -y
abx --provider alicloud-express exec <sandbox-id> -- python3 -c 'print(6*7)'
abx --provider alicloud-express kill <sandbox-id> -y
```

## Quick start (Python SDK)

Install the [Python client](../../python-client-installation.md) and configure the same Express account. This example prints `42`, writes and reads a file, then deletes its sandbox.

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="alicloud-express", template="code-interpreter-v1", timeout=180)
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

`run_code` on Express can execute through a shell fallback. For a persistent kernel or interpreter session, do not treat a successful shell command as that interface.

## Configuration

Use the Express account settings in the [usage guide](../../using-templates.md). No model credential is needed for this example. For prewarmed processes, see [runtime environment](../../runtime-environment.md).

## Resources

Choose a finite timeout in seconds and delete instances when finished. CPU, memory and image updates are managed by the provider.

## Verified

[2026-10-19 record](../evidence/code-interpreter-v1-2026-10-19T154153Z.json): real CLI execution and SDK shell/files, shell fallback for `run_code`, and confirmed instance deletion. The record contains its original versions and call paths.

## Secondary development

For additional dependencies or a custom command service, start from the [source skeleton](../../../_skeleton/README.md); it produces a separate template.

## Contributing

Follow [CONTRIBUTING](../../../CONTRIBUTING.md). Keep both languages aligned and add a new dated record for a new runtime test.

## Issues

[Report a template issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues).

## License

Documentation and verification scripts: Apache-2.0. The provider-managed image and its bundled software retain their own licenses.
