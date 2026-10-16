# Configure the process that serves named commands

[中文](runtime-environment.zh-CN.md)

Model and gateway settings must be present in the **named-command server process** before it imports the template. `template.yaml` declares names; it does not provide secret values. A create-time environment mapping cannot change an already running process.

In an actual Express image review, `Sandbox.create(envs=...)` did not make all required Aider settings visible to the prewarmed server on port 9000. The model command refused to run. Starting the same image's unchanged `commands.py` on port 9010 with explicit `commands.start(env=...)` made all three configuration flags true through SDK, CLI and HTTP. Its real coding suite then passed 21 checks. This is an observed provider/startup boundary, not a claim that every create-time variable is ignored on every provider.

## Existing quick starts

Create-time key examples in template READMEs apply when the provider starts the command server with that environment. Inspect that template's read-only setup command before calling a model. If settings are missing on a prewarmed server, use an explicitly configured new server as below. Sending a key only to the local HTTP test controller does not configure the remote server.

## Explicit server process

This example uses the installed Qwen template's configuration names and read-only diagnostic. It illustrates the process API; the image-backed verification described above used Aider. Choose the names documented by your template. The matching client/server source installation is described in [Python client installation](python-client-installation.md).

```python
import asyncio
import os

import httpx
from agent_sandbox import Sandbox


async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900)
    stream = None
    drain = None
    try:
        settings = {name: os.environ[name] for name in
                    ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")}
        settings["ABX_SERVER_BASE_DIR"] = "/home/user/app"
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 "
            "--commands /home/user/app/commands.py",
            env=settings, timeout=900)
        started = asyncio.Event()

        async def discard_output():
            async for chunk in stream:
                if chunk.pid:
                    started.set()
                # Do not print or retain the server's raw output.

        drain = asyncio.create_task(discard_output())
        await asyncio.wait_for(started.wait(), timeout=120)
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(30):
                try:
                    response = await client.get(sb.network.get_url(9010) + "/health")
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("configured server did not become ready")
        print(await sb.run("qwen_setup_check", server_port=9010))
        # After inspecting the setup flags, use server_port=9010 for the task.
    finally:
        try:
            await sb.kill()  # Owns the new server and its child processes.
        finally:
            if drain is not None:
                drain.cancel()
                await asyncio.gather(drain, return_exceptions=True)
            if stream is not None:
                await stream.cancel()


asyncio.run(main())
```

This starts a new process from the installed image; it does not replace source, adopt another process or change `HOME`. Consume the process stream as shown. A missing CLI, startup error or failed setup remains a failure. The lifetime is bounded by the process timeout and the owned sandbox's final destruction. For a long task, choose sufficient process/sandbox deadlines and check the template's cancellation contract.

All callers must select the same new server:

```bash
abx run <sandbox-id> qwen_setup_check --server-port 9010
```

For direct HTTP, use `sb.network.get_url(9010)` and `POST /commands/qwen_setup_check` with `{}`. Preserve any provider-required gateway authentication. Do not put model keys in command arguments, request prompts, image layers or logs.

## Server authentication is separate

`ABX_SERVER_TOKEN` is read when a server starts. A later create call or a new server does not add authentication to the old port-9000 process. If a new server starts with a bearer token, send that token to that server, for example `sb.server_at(9010, token=server_token).commands.run(...)`. The current server exempts `/health` from server-token authentication; the provider gateway may still require its own credential. Health alone does not prove authentication or model configuration. This token is separate from the provider gateway credential and the upstream model key.

The example above leaves server-token configuration at its existing default. Starting a configured server on a second port does not secure or stop the default service. If all services must require authentication, establish the provider-supported startup configuration before they start and verify each exposed service; do not infer it from a successful `Sandbox.create` request.

## Verification boundaries

The Aider image review used its original image commands, a new explicitly configured server, real model coding, independent tests and verified owned cleanup. It does not establish canonical `abx template deploy` acceptance, other providers' environment behavior, or every template's model support. The [Aider review](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88) records those separate outcomes. Keep `tested_on` and provider evidence unchanged until their own required gates pass.
