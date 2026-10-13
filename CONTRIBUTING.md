# Contributing to Awesome Templates for Agent Sandbox

Thanks for adding a template. This repository is the catalog for the `abx`
CLI and the `agent-sandbox` SDK.

- [Checklist](#checklist)
- [Template anatomy](#template-anatomy)
- [Named commands](#named-commands)
- [Server policy](#server-policy)
- [The one e2e command](#the-one-e2e-command)

## Checklist

1. Create a top-level directory in kebab-case. Its name, `template.yaml`
   `name`, and the index `path` are the same string.
2. Add `template.yaml`, `Dockerfile`, `commands.py` (when the template
   registers commands or starts the server), `e2e_test.py`, and `README.md`.
3. Add one entry under the right section of
   [`awesome-templates.yaml`](./awesome-templates.yaml): `name`,
   `description`, `repo`, `path`, `tags`, `author`, `capabilities`, `status`.
4. From this repository root, with `agent-sandbox-server` and `httpx`
   installed, run:

   ```bash
   python3 scripts/run_local_e2e.py
   ```

   All 12 templates must pass. Do not commit `__pycache__/`, secrets, or
   API keys. Declare key *names* with empty values in `template.yaml` `env`.

## Template anatomy

```
<template-name>/
├── template.yaml    # metadata, capabilities, optional server policy
├── Dockerfile       # python:3.12-slim, installs agent-sandbox-server
├── commands.py      # agent_sandbox.server process
├── e2e_test.py      # HTTP checks against a running commands.py
└── README.md        # what it is, how to deploy, how to run e2e
```

`template.yaml` fields the client accepts include `name`, `version`,
`description`, `author`, `license`, `tags`, `env`, `ports`, `cpu_count`,
`memory_mb`, `capabilities` (`shell`, `files`, `code`, `terminal`, `ports`),
and `server`. The CLI also reads `resources.cpu` and `resources.memory`
(MB) when it deploys. Named commands are not declared here: they are
registered in `commands.py`.

`capabilities` are template metadata for the client. They do not toggle
HTTP routes. `terminal` and `ports` are off unless the template lists them.

The Dockerfile uses the generic profile:

- `FROM python:3.12-slim`
- install `agent-sandbox-server` from a wheel in the build context, otherwise
  `pip install agent-sandbox-server`
- `WORKDIR /app`
- `CMD ["python3", "commands.py"]`

The README must say what the template is, how to deploy it, and how to run
its e2e:

```bash
abx template install alibaba-agent-sandbox/awesome-templates//<name>
abx deploy
python3 scripts/run_local_e2e.py
```

`abx template install` builds and registers unless you pass
`--download-only`. `abx deploy` (and `abx template deploy`) publish the
template directory. There is no top-level `abx install` or `abx init`; use
`abx template install` and `abx template init`.

## Named commands

Named commands are registered in `commands.py` with the `@command` decorator.
`template.yaml` has no command map. `start()` serves them and freezes the
registry:

```python
from agent_sandbox.server import command, start


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
```

Callers use `abx run <sandbox-id> hello --name Alice` or
`await sandbox.run("hello", name="Alice")` (`sandbox.run_sync` from
synchronous code). A shell string is `sandbox.commands.run("echo hi")` or
`abx exec`, not a template.yaml command map.

## Server policy

Every server endpoint has an id (`files_list`, `shell`, `agents_sessions_create`).
`template.yaml` `server:` is one layer: an endpoint policy. Name the routes you
expose under `endpoints` (`enabled`, `scopes`, `paths`, `limits`, `params`,
`audit`). Presets are `default`, `transfer-only`, `read-only`, `hardened`, and
`locked`. Unknown keys are rejected.

A group (`commands`, `file_ops`, `process`, `terminal`, `system`, `dev_tools`,
`browser`, `agents`) is only a name for the endpoints that declare it.
`core`, `commands`, `file_ops`, `process`, `terminal` and `system` start on;
`dev_tools`, `browser` and `agents` start off. Turn a group on from:

- `template.yaml`: `server.groups` as a list (`groups: [dev_tools]`) or a map
  (`groups: {process: false}`)
- `commands.py`: `default_table().enable_group(CapabilityGroup.BROWSER)`
- the container environment: `ABX_SERVER_ENABLED_GROUPS=dev_tools,browser`
  (it only turns groups on)

```yaml
server:
  endpoints:
    "*":
      enabled: false
    agents_sessions_create:
      enabled: true
```

`commands.py` must build the same `ServerPolicy` and pass it to
`SandboxServer(policy=...)` (or `start(..., policy=...)`). The local e2e runs
`commands.py`; it does not read `template.yaml`. A disabled endpoint answers
404 with `code: endpoint_disabled` and the `rule` that decided; `GET
/capabilities` lists each endpoint's state. A path outside `ABX_SERVER_BASE_DIR`
answers 403 `path_not_allowed`. `core` cannot be disabled.

Environment variables inside the container use the `ABX_` prefix
(`ABX_SERVER_PORT`, `ABX_SERVER_TOKEN`, `ABX_SERVER_BASE_DIR`,
`ABX_SERVER_ENABLED_GROUPS`).

## The one e2e command

```bash
python3 -m pip install agent-sandbox-server httpx
python3 scripts/run_local_e2e.py
```

The script binds an ephemeral port per template, starts
`python3 commands.py`, sets `E2E_BASE_URL`, runs `e2e_test.py`, and stops
the process. It does not forward cloud credentials. A case inside
`e2e_test.py` may print SKIP when a model key or Playwright is absent; the
template's process must still exit 0.

## Naming

**Agent Sandbox.** CLI `abx`. Client package `agent-sandbox`
(`agent_sandbox`). In-image package `agent-sandbox-server`
(`agent_sandbox.server`). GitHub `alibaba-agent-sandbox/awesome-templates`,
`alibaba-agent-sandbox/python-sdk`, and `alibaba-agent-sandbox/agent-sandbox`.
npm `@agent-sandbox/cli`. The previous names are not accepted.
