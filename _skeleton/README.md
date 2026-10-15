# _skeleton

Scaffold for a new Agent Sandbox template. Copy this directory, then replace the command and the metadata. It is not a catalog entry.

## What it does

Registers one named command, `hello`, on `agent-sandbox-server` at port 9000. The command returns `Hello, <name>!`.

## Stack

- Base image `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`. `abx template deploy` replaces `<region>` with `ALIBABA_CLOUD_REGION_ID` or `cn-hangzhou`, and `<tag>` with `ABX_BASE_IMAGE_TAG` or `v0.0.49`.
- `agent-sandbox-server` from python-sdk commit `35da216a300f1e2e84254a1cf4b4a7ea98681505` when the build context has no wheel: `pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40-hex>.tar.gz#subdirectory=server-sdk"`. A wheel injected by `abx template deploy` wins. `agent-sandbox-server==X.Y.Z` is the other allowed pin once that release exists on PyPI. `0.3.0` was not on PyPI on 2026-10-15.
- Work directory `/home/user/app`. Runtime user `user`.
- Python 3.13 and Node.js 20 come from the base image.
- The platform starts the process with `start_cmd`. The Dockerfile stops after `USER` and `EXPOSE`.

## Problem solved

Gives a new template one directory that already satisfies [docs/template-spec.md](../docs/template-spec.md), so the layout, the server contract, and the README sections are not reinvented.

## Quick start (CLI)

From a checkout of this repository, with Express credentials in the environment (listed in the spec):

```bash
abx template deploy ./_skeleton -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> hello --arg name=Ada
```

`template.yaml` already stores `generation`, `start_cmd`, and `ready_cmd`. Current `abx` reads those keys. The flags above repeat them so the command stands alone.

Remove the sandbox and the template when you are done:

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py _skeleton` does the same deploy, runs `hello`, writes evidence only after a pass, and deletes the sandbox and the template.

## Quick start (Python SDK)

Install the client from PyPI as `agent-sandbox-client` (`python3 -m pip install agent-sandbox-client`). The import is `agent_sandbox`. `pip install agent-sandbox` is an unrelated project.

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`await sb.run("hello", name="Ada")` returns the string `Hello, Ada!`. `sb.commands.run` runs a shell command. It is not this named command. `sb.network.get_url(9000)` is the server's port URL. `Sandbox.create_sync` raises `TypeError` on python-sdk 0.3.0 ([python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22)); use `await Sandbox.create`.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| hello | `name`: string, optional, default `World` | string | Say hello. |

`POST /commands/hello` with body `{"name":"Ada"}` returns `{"result":"Hello, Ada!"}`. A missing required argument is HTTP 400. An exception inside the function is HTTP 500 with `{"error","type"}`.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | no | empty | When set inside the sandbox, clients send `Authorization: Bearer`. The value in `template.yaml` is empty. |
| `ABX_SERVER_PORT` | no | `9000` | Port `start()` binds for a local `python3 commands.py`. |

Set secret values on `abx create --env` or `Sandbox.create(envs=...)`. Do not write them into the image, the Dockerfile, or a log.

## Resources

| Resource | Value |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| port | 9000 |
| disk | platform rootfs, about 10G on Express |

## Verified

No provider has a passing run recorded for this template.

## Secondary development

Copy `_skeleton` to a kebab-case directory whose name matches `^[a-z0-9][a-z0-9-]*$`. Set `template.yaml` `name` to that directory name. Replace `hello` with commands that call the upstream program, and pin every installed version in the Dockerfile. Fill `docs/design/<name>.md` from [docs/design/_TEMPLATE.md](../docs/design/_TEMPLATE.md). Add one `awesome-templates.yaml` entry. Run `python3 scripts/check_template.py <dir>`.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md) and [docs/template-spec.md](../docs/template-spec.md).

## Issues

| Topic | Repository |
|---|---|
| This template, the spec, the checker | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK or `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues), title prefix `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues), title prefix `[templates]` |

## License

Apache-2.0, the same license as this repository. See [LICENSE](../LICENSE).
