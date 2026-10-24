# opensandbox-code-interpreter

[中文](README.zh-CN.md)

## What it does

Use the upstream OpenSandbox Code Interpreter image on an OpenSandbox server.

## Stack

Image `opensandbox/code-interpreter:v1.1.0`; its [upstream example](https://github.com/opensandbox-group/OpenSandbox/blob/30348cbdfe4b9cfd49e0963617aed357a8f1ac4c/docs/examples/code-interpreter.md) describes the native runtime. The provider maintains this external image.

## Problem solved

Use shell and files through Agent Sandbox, or native interpreter contexts through the upstream SDK.

## Quick start (CLI)

Install the [CLI](../../using-templates.md) and Node.js 22+, configure your provider below, and replace `<sandbox-id>` with the ID returned by create.

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//opensandbox --allow-unpinned --yes
abx provider doctor opensandbox
abx --provider opensandbox create --template opensandbox/code-interpreter:v1.1.0 --timeout 180 -y
abx --provider opensandbox exec <sandbox-id> -- python3 -c 'print(6*7)'
abx --provider opensandbox kill <sandbox-id> -y
```

## Quick start (Python SDK)

Install the [Python client](../../python-client-installation.md) and the same provider plugin; keep Node.js on PATH for the provider engine.

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="opensandbox", template="opensandbox/code-interpreter:v1.1.0", timeout=180)
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

### Use the native interpreter SDK

Persistent Python contexts use the upstream OpenSandbox SDK. Install its pinned native SDK dependencies with the commands and lockfiles in the [reproduction workflow](../../../.github/workflows/managed-opensandbox.yml), alongside the [public Python client](../../python-client-installation.md). This example explicitly starts the image's native interpreter service and connects the upstream SDK to the same instance.

```python
import asyncio, os, uuid
from urllib.parse import urlsplit
from opensandbox import Sandbox as NativeSandbox
from opensandbox.config import ConnectionConfig
from code_interpreter import CodeInterpreter, SupportedLanguage
from agent_sandbox import ProviderSandbox

async def main():
    provider = "opensandbox"
    sb = await ProviderSandbox.create(provider=provider, template="opensandbox/code-interpreter:v1.1.0", timeout=600, cpu=2, memory=3072,
        provider_options={"entrypoint": "/opt/code-interpreter/code-interpreter.sh"},
        envs={"PYTHON_VERSION": "3.11", "JAVA_VERSION": "17", "NODE_VERSION": "20", "GO_VERSION": "1.24"},
        metadata={"verification": "managed-example-" + uuid.uuid4().hex})
    sid = sb.id
    try:
        result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
        assert result.exit_code == 0 and result.stdout.strip() == "42"
        path = "/tmp/owned-example-" + uuid.uuid4().hex + ".txt"
        await sb.files.write(path, "owned-example\n")
        assert await sb.files.read(path) == "owned-example\n"
        await sb.files.remove(path)
        assert not await sb.files.exists(path)
        url = urlsplit(os.environ.get("ABX_OPENSANDBOX_BASE_URL", "http://127.0.0.1:8080"))
        config = ConnectionConfig(domain=url.netloc, protocol=url.scheme,
            api_key=os.environ.get("ABX_OPENSANDBOX_API_KEY") or os.environ.get("OPEN_SANDBOX_API_KEY"),
            use_server_proxy=True)
        native = await NativeSandbox.connect(sid, connection_config=config)
        try:
            interpreter = await CodeInterpreter.create(sandbox=native)
            try:
                context = await interpreter.codes.create_context(SupportedLanguage.PYTHON)
                first = await interpreter.codes.run("owned_value = 37\nowned_value", context=context)
                assert first.error is None and first.result[0].text.strip() == "37"
                second = await interpreter.codes.run("owned_value + 5", context=context)
                assert second.error is None and second.result[0].text.strip() == "42"
                await interpreter.codes.delete_context(context.id)
            finally:
                await interpreter.aclose()
        finally:
            await native.close()
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

The project `ProviderSandbox.run_code` adapter for OpenSandbox remains unimplemented (`E8004`). Use `interpreter.codes` above for native sessions.

## Quick start (HTTP POST)

This image does not contain the project `/commands/*` application server. Use the provider SDK for lifecycle and process/file operations, and the upstream interpreter SDK for native code sessions.

## Command reference

`ProviderSandbox.create` creates an instance; `commands.run` returns `exit_code/stdout/stderr`; `files.write/read/remove` operate on files. `kill` deletes the instance; `close` releases local connections.

## Configuration

Set `ABX_OPENSANDBOX_BASE_URL` to your OpenSandbox server root and `ABX_OPENSANDBOX_API_KEY` when the server requires a key. The default process keeps the instance alive for exec/files. To start the native interpreter service, pass `provider_options={"entrypoint": "/opt/code-interpreter/code-interpreter.sh"}` as below; for CLI create, set `ABX_OPENSANDBOX_ENTRYPOINT` to that script path.

## Resources

The timeout is in seconds. CPU, memory and image availability depend on your deployment. Delete instances after use.

## Verified

[2026-10-21 native Docker record](../evidence/verification-opensandbox-code-interpreter-2026-10-21-native-docker.json): SDK create/shell/files, upstream Python execution and persistent/isolated contexts, and confirmed cleanup. It records its original dependency revisions. Current default-start and explicit-entrypoint checks are tracked in [Issue 206](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/206).

## Secondary development

Customize the upstream image or use a [source template](../../../_skeleton/README.md) for a project command service. Keep the native interpreter service entrypoint explicit.

## Contributing

Follow [CONTRIBUTING](../../../CONTRIBUTING.md). Keep both languages aligned and preserve dated test records.

## Issues

[Report a template issue](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Provider integration belongs to [awesome-providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues).

## License

Authored documentation/tests: Apache-2.0. The upstream image, SDKs and bundled applications retain their own licenses and terms.

