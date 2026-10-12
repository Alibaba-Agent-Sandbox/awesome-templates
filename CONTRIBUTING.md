# Contributing to Awesome Templates for Easy Sandbox

Thanks for helping grow the [Easy Sandbox](https://pypi.org/project/easy-sandbox/)
template ecosystem! This guide explains how a template is structured, how the
runtime capability model works, how to develop and test locally with the `ebx`
CLI, and the exact steps to land your contribution.

- [Template Anatomy](#template-anatomy)
- [Capability Groups](#capability-groups)
- [Local Development & Testing](#local-development--testing)
- [Contribution Workflow](#contribution-workflow)
- [Naming & Quality Standards](#naming--quality-standards)

---

## Template Anatomy

Every template is a **top-level directory** in this repository containing:

```
<template-name>/
├── template.yaml    # Metadata, capabilities, custom commands
├── Dockerfile       # Container image (generic profile, installs easy-sandbox-server)
├── commands.py      # easy_sandbox.server route table + command registry
├── e2e_test.py      # HTTP checks against a locally started commands.py
└── README.md        # What it is, required env vars, usage
```

### `template.yaml`

The canonical descriptor. Recognised fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Unique template identifier (matches the directory name). |
| `version` | ✅ | Semantic version string, e.g. `"1.0.0"`. |
| `description` | ✅ | One-line summary. |
| `author` | ✅ | GitHub handle or org (e.g. `Easy-Sandbox`). |
| `tags` | ✅ | List of search tags. |
| `base` | ✅ | Base image. Use `python:3.12-slim` unless the template documents another generic base. |
| `system_packages` | | OS packages installed at build time. |
| `capabilities` | ✅ | Sandbox capabilities: `shell`, `files`, `code`, `terminal`, `ports`. |
| `ports` | | Ports the sandbox exposes. |
| `custom_commands` | | Named CLI commands with `cmd`, `description`, `cwd`, `timeout`, `args`. |
| `env` | | Default environment variables. |

Minimal example:

```yaml
name: my-template
version: "1.0.0"
description: "Short description of what this template does"
author: Easy-Sandbox
tags: [python, example]

base: python:3.12-slim
system_packages: [python3, python3-pip]

capabilities: [shell, files, code, ports]
ports: [9000]

env:
  LANG: C.UTF-8
```

> `terminal` and `ports` must be declared **explicitly** — they are never
> granted implicitly.

### `Dockerfile`

Use the generic image profile, not a provider-specific Function Compute image:

- `FROM python:3.12-slim`
- install `python3` and `pip` only when that base image does not already provide them
- copy an `easy-sandbox-server` wheel, with a PyPI fallback of `easy-sandbox-server`
- `WORKDIR /app`
- `CMD ["python3", "commands.py"]`

Keep the template's own packages (browser extras, agent CLIs). Do not write
API keys into the image. Declare key *names* with empty values in
`template.yaml` `env`, and inject the values when the sandbox is created.

```dockerfile
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# python:3.12-slim already includes python3 and pip.
RUN if ! command -v python3 >/dev/null 2>&1 || ! command -v pip >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends python3 python3-pip \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Install easy-sandbox-server (in-sandbox runtime: easy_sandbox.server).
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir easy-sandbox-server; \
    fi

WORKDIR /app
COPY commands.py .
EXPOSE 9000
CMD ["python3", "commands.py"]
```

### `commands.py` — RouteTable + CommandRegistry

This is where a template extends the sandbox HTTP server. Two building blocks:

- **`RouteTable`** — toggles capability groups and registers custom HTTP routes
  via the `@table.route(...)` decorator.
- **`CommandRegistry`** — registers named, callable commands exposed through the
  server's command API via `@registry.command(...)`.

```python
from easy_sandbox.server import (
    CapabilityGroup,
    CommandRegistry,
    SandboxServer,
    ServerResponse,
    default_table,
)

# 1. Route table — enable the capability groups this template needs
table = default_table()
table.enable_group(CapabilityGroup.FILE_OPS)   # upload/download + file ops
table.enable_group(CapabilityGroup.PROCESS)    # shell + process management
table.enable_group(CapabilityGroup.SYSTEM)     # system info + port detection

# 2. Command registry — custom commands
registry = CommandRegistry()


@registry.command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"


@registry.command(hidden=True)               # not listed in GET /commands
def _debug_info() -> dict:
    import platform
    return {"python": platform.python_version()}


# 3. Custom HTTP route via the RouteTable decorator
@table.route("GET", "/hello/{name}", group=CapabilityGroup.COMMANDS)
def hello_route(request: object) -> ServerResponse:
    name = getattr(request, "path_params", {}).get("name", "World")
    return ServerResponse.ok({"greeting": f"Hello, {name}!"})


# 4. Freeze the registry and serve when this file is the process entrypoint
registry.freeze()
if __name__ == "__main__":
    import os

    port = int(os.environ.get("EBX_SERVER_PORT", "9000"))
    server = SandboxServer(registry=registry)
    server.serve(port=port)
```

`commands.py` imports `easy_sandbox.server` from the `easy-sandbox-server`
package. The image installs that package, not the client distribution.

### `README.md`

Document what the template is, which environment variables / API keys it needs,
and a copy-pasteable usage snippet. Keep the install command in the
`Easy-Sandbox/awesome-templates//<name>` form.

---

## Capability Groups

The sandbox server organises endpoints into **capability groups**. Enabling a
group activates its family of routes.

| Group | Default state | Purpose |
|-------|---------------|---------|
| `CORE` | **Always on** (cannot be disabled) | Health/status essentials. |
| `COMMANDS` | Enabled | List & run registered commands. |
| `FILE_OPS` | Enabled | Upload/download & file operations. |
| `PROCESS` | Enabled | Shell execution & process management. |
| `TERMINAL` | Enabled | Interactive PTY / terminal WebSocket. |
| `SYSTEM` | Enabled | System info & port detection. |
| `DEV_TOOLS` | **Disabled** | Developer tooling — must be enabled explicitly. |
| `BROWSER` | **Disabled** | Browser/DevTools automation — must be enabled explicitly. |

Rules of thumb:

- `CORE` is always active; calling `enable_group(CapabilityGroup.CORE)` is a
  no-op and `disable_group(CapabilityGroup.CORE)` raises.
- `DEV_TOOLS` and `BROWSER` are **off by default**. If your template needs them,
  enable them explicitly:

  ```python
  table.enable_group(CapabilityGroup.BROWSER)
  ```

- Only enable the groups you actually use — a smaller surface is safer and
  faster to start.

---

## Local Development & Testing

Install `ebx` and validate your template against a **local registry** before
opening a PR — no GitHub Release required:

```bash
# Install directly from a local directory
ebx template install ./my-template --registry-type local

# Inspect what got cached (~/.ebx/templates/)
ebx template cache

# Confirm your template shows up in the index search
ebx template search my-template
```

What to verify:

1. **Files present** — `template.yaml`, `Dockerfile`, `commands.py`, `e2e_test.py`, `README.md`.
2. **`commands.py` imports cleanly** — no syntax errors; only enable capability
   groups you use. The process entrypoint calls `serve()` from `easy_sandbox.server`.
3. **Commands & routes resolve** — every `@registry.command` and `@table.route`
   is reachable and returns sensible output.
4. **Capabilities match reality** — the `capabilities` list in `template.yaml`
   reflects the groups your `commands.py` enables.
5. **Local e2e** — from the repository root, with `easy-sandbox-server` and
   `httpx` installed:

   ```bash
   python3 scripts/run_local_e2e.py
   ```

   The script starts `python3 commands.py` in each template directory on an
   ephemeral port, sets `E2E_BASE_URL`, runs `e2e_test.py`, and stops the
   process. It does not need cloud credentials. If your template cannot start
   without a third-party binary or API key, the run must skip that template
   with an explicit reason and still exit 0. A template whose `commands.py`
   only needs `easy-sandbox-server` must pass. The same script is the
   `ubuntu-latest` job in `.github/workflows/e2e.yml`.

> The final `install` step submits a build to the platform (`POST /templates`).
> Without platform credentials it will fail at that submission stage — that is
> expected. Reaching fetch → parse → build-submission proves the template is
> structurally valid.

---

## Contribution Workflow

1. **Fork** this repository.
2. **Create** a new top-level directory named exactly after your template
   (kebab-case, e.g. `my-agent`).
3. **Add the template files** — `template.yaml`, `Dockerfile`, `commands.py`,
   `e2e_test.py`, and `README.md`.
4. **Register** your template in [`awesome-templates.yaml`](./awesome-templates.yaml):

   ```yaml
   - name: my-agent
     description: "Brief description of what your template does"
     repo: https://github.com/Easy-Sandbox/awesome-templates
     path: my-agent
     tags: [ai-agent, your-tag]
     author: your-github-handle
     capabilities: [shell, files, code]
     status: community
   ```

5. **Validate locally** with
   `ebx template install ./my-agent --registry-type local`.
6. **Open a PR** and complete the checklist in the pull request template.

---

## Naming & Quality Standards

- **Brand:** Easy Sandbox. **CLI:** `ebx`. **Client PyPI package:** `easy-sandbox`.
  **In-image package:** `easy-sandbox-server` (import `easy_sandbox.server`).
  **GitHub org:** `Easy-Sandbox`.
  Install published templates with
  `ebx template install Easy-Sandbox/awesome-templates//<name>`.
  Never reference legacy names in new contributions.
- **Directory name == `template.yaml` `name` == index `path`.** All three must
  match.
- **No secrets.** Never commit API keys, tokens, or passwords. Use placeholders
  like `REPLACE_ME` and document required env vars in the README.
- **No build junk.** `__pycache__/`, `*.pyc`, and `.DS_Store` are excluded by
  `.gitignore` — keep it that way.
- **Minimal & reproducible images.** Pin versions where practical; install only
  what the template needs.
- **Conventional Commits** for commit messages (`feat:`, `fix:`, `docs:`, …).

Thanks for contributing! 🎉
