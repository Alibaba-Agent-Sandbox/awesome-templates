# Template development, listing, and acceptance

This is the normative spec for a template in this repository. [docs/template-spec.zh-CN.md](./template-spec.zh-CN.md) is the same content in Chinese. If the two files disagree, this file wins.

`docs/acceptance.md` is a pointer here. `_skeleton/` is a passing example of the file layout. It is not a catalog entry.

Tooling that later template work relies on:

| Tool | Role |
|---|---|
| `scripts/check_template.py` | Static lint. Exit 0 when the directory matches this spec. |
| `scripts/express_e2e.py` | L2 on `alicloud-express`. Writes evidence only after a pass, then deletes the sandbox and the template. |
| `scripts/run_local_e2e.py` | L0 for every directory that has `commands.py` and `e2e_test.py`. Also runs the checker. |

## Directory layout

A template is one directory at the repository root. The directory name, `template.yaml` `name`, and the `path` in `awesome-templates.yaml` are the same string. Product names match `^[a-z0-9][a-z0-9-]*$`. `_skeleton` is the only underscore directory, and it is not installed.

```
<name>/
├── template.yaml
├── Dockerfile
├── commands.py
├── e2e_test.py
├── README.md
├── README.zh-CN.md
└── evidence/                 # only after a passing provider run
    └── express-<YYYY-MM-DD>.json
docs/design/<name>.md         # required for every product template
```

| File | Required content |
|---|---|
| `template.yaml` | Schema below. |
| `Dockerfile` | Alibaba base image, pinned installs, `WORKDIR /home/user/app`, `USER user`. No `CMD` or `ENTRYPOINT`. |
| `commands.py` | `@command` functions. `start()` only under `if __name__ == "__main__"`. |
| `e2e_test.py` | Local smoke. Reads `E2E_BASE_URL`. |
| `README.md` | English sections below. |
| `README.zh-CN.md` | The same sections in Chinese. |
| `docs/design/<name>.md` | Pre-analysis. Copy [docs/design/_TEMPLATE.md](./design/_TEMPLATE.md). |
| `evidence/*.json` | Machine-readable pass. Do not commit a failed run. |

OpenSandbox images that the SDK already resolves (`code-interpreter`, `code-interpreter-base`, `desktop`, `playwright`, `vscode`) stay out of this repository. Do not copy those Dockerfiles in.

## template.yaml

```yaml
name: my-template
version: "1.0.0"
description: "One sentence."
author: "github-handle"
license: Apache-2.0
spec_version: 2

base: "fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"
generation: 2
start_cmd: "agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py"
ready_cmd: "agent-sandbox-server healthcheck --port 9000"

resources:
  cpu: 2          # vCPU
  memory: 2048    # MB

ports:
  - 9000

tags: [example]
priority: P2      # P0, P1, or P2
wave: other       # 1, 2, 3, or other
tested_on: []     # provider ids with a passing evidence file, else []

capabilities: [shell, files, code, ports]

env:
  SOME_API_KEY: ""

smoke:
  - command: hello
    args:
      name: Express
    expect: "Hello, Express!"
```

| Field | Rule |
|---|---|
| `name` | Same as the directory. |
| `description`, `version`, `author`, `license` | Non-empty strings. |
| `spec_version` | `2` once the directory follows this document. The checker treats any other directory as legacy and reports it without failing `--all`. |
| `base` | String. Either the placeholder `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` or a pinned `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:vX.Y.Z`. Not a mapping. |
| `generation` | Integer `2`. |
| `start_cmd` | `agent-sandbox-server serve` plus the path of `commands.py` inside the image. |
| `ready_cmd` | `agent-sandbox-server healthcheck` plus the port. |
| `resources.cpu` | Positive integer, vCPU. |
| `resources.memory` | Positive integer, MB. |
| `env` | Mapping. A key ending in `API_KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `CREDENTIAL`, or `PRIVATE_KEY` has an empty string value. |
| `ports` | Includes `9000`. |
| `tags` | Non-empty list of strings. |
| `priority` | `P0`, `P1`, or `P2`, matching `docs/template-backlog.json` when the template is listed there. |
| `wave` | `1` (whole product on Express), `2` (a stated slice), `3` (needs another provider for the workload), or `other`. |
| `tested_on` | Provider ids that have a passing evidence file. Empty until then. The same set is the README Verified table. |
| `capabilities` | Subset of `shell`, `files`, `code`, `terminal`, `ports`. Metadata for the client. They do not toggle HTTP routes by themselves. |
| `smoke` | List of `{command, args, expect}` run by `scripts/express_e2e.py`. `args` keys are the command parameters. `expect` is compared after strip for strings. |

`abx template deploy` reads `generation`, `start_cmd`, and `ready_cmd` from this file (CLI flags win). On `alicloud-express`, a directory with `commands.py` and no explicit values defaults to generation 2 and:

```
agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py
agent-sandbox-server healthcheck --port 9000
```

Write the three keys anyway. The default path is wrong for an image whose `commands.py` is not at `/home/user/app/commands.py`.

Named commands are not listed in `template.yaml`. They are registered in `commands.py`.

## Alibaba base image

Express sandboxes run as non-root `user`, with 2 vCPU, no `/dev/kvm`, no Docker, no extra capabilities, about 10G of rootfs, and working egress. The platform base image is:

```
fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
```

`<region>` is `cn-hangzhou` unless `ALIBABA_CLOUD_REGION_ID` or `ABX_BASE_IMAGE_REGION` is set. `<tag>` is `v0.0.49` unless `ABX_BASE_IMAGE_TAG` is set. `abx template deploy` rewrites the placeholders in the Dockerfile before `docker build` (see `src/api/docker_builder.ts` in `agent-sandbox`). The image already contains Python 3.13 and Node.js 20.

The image entrypoint cannot be replaced. The Dockerfile has no `CMD` and no `ENTRYPOINT`. The platform runs `start_cmd` and probes `ready_cmd`. Generation 2 is required for those commands. Updating a generation-1 template of the same name while sending `start_cmd` fails. Deploy under a new name, or delete the generation-1 template first. `scripts/express_e2e.py` uses a unique alias so it does not delete a template it did not create.

`Dockerfile` shape:

```dockerfile
FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive

COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server==0.3.0"; \
    fi

# Pin every other installer the same way: pip name==X.Y.Z, npm package@X.Y.Z.
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
```

`abx template deploy` injects an `agent-sandbox-server` wheel into the build context when `ABX_SERVER_SDK_SOURCE` points at a `server-sdk` tree, otherwise it can download a pinned release. The `else` branch still pins `agent-sandbox-server==0.3.0`. Build with BuildKit so an empty `COPY *.whl` is accepted when no wheel was injected (`DOCKER_BUILDKIT=1`).

A base image other than the Alibaba image is allowed only when a hard dependency makes the platform image impossible. The README then has `## Base image` with the reason (at least a short paragraph). The checker accepts that escape hatch. "We already had a Dockerfile" is not a reason.

Upstream CLIs and libraries are pinned to an exact version. A floating tag such as `latest` or an unpinned `npm install -g` is a conformance failure.

## commands.py

Import the server SDK and register named commands:

```python
from __future__ import annotations

import os

from agent_sandbox.server import command, start


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
```

| Rule | Detail |
|---|---|
| Import | `from agent_sandbox.server import command`. Add `start` when the local process serves HTTP. Stdlib imports are fine. Do not import a second HTTP server. |
| Name | `@command("name")` or the function name when the first argument is omitted. Use the upstream CLI's verb in `snake_case` when the command wraps a product (`claude`, `codex_exec`). |
| Parameters | Taken from the function signature. `int`, `float`, and `bool` stay typed. Everything else is a string. A parameter with no default is required. |
| Return | One JSON-serializable value: `str`, `int`, `float`, `bool`, `None`, `list`, or `dict`. The HTTP body is `{"result": <value>}`. Do not return a generator. |
| Streaming | A named command is one request and one JSON response. Live stdout belongs to the process API (`sb.commands.stream`, `abx exec`), not to `@command`. Return the full text, or write a file and let the client read it with `sb.files`. |
| Errors | Missing or mistyped arguments never call the function: HTTP 400 `{"error", "type": "ValueError"}`. Raise `RuntimeError` (or `ValueError`) for an upstream failure. The server returns HTTP 500 `{"error": "<message>", "type": "<ExceptionName>"}`. A non-zero upstream exit is an exception, not a successful string. Keep secrets out of the message. |
| Hidden | `@command(hidden=True)` stays callable and is omitted from `GET /commands`. |
| `start()` | Only under `if __name__ == "__main__"`. `agent-sandbox-server serve --commands` imports the module. A `start()` at import time breaks that path. |
| Upstream | The body of a product command runs that product's own non-interactive argv. Do not splice a prompt into a shell string. Pass argv as a list. |

`GET /commands` returns `{"commands": [{"name", "description", "args": [{"name", "type", "required", "default", "description"}]}]}`.

### Auth token

The server reads `ABX_SERVER_TOKEN` when the process starts. When the variable is non-empty, every request needs `Authorization: Bearer <token>` or `X-Access-Token: <token>`. Declare the name in `env` with an empty value. Inject the real value at `abx create --env` or `Sandbox.create(envs=...)`.

When the variable is unset, anonymous calls are allowed. On Express the gateway may still present the sandbox access token. Current `abx` (agent-sandbox main, the deploy/run fix in `#16`) retries a 401 once without that header. Current `agent_sandbox.Sandbox.server` does not send the sandbox token to port 9000. A template that sets `ABX_SERVER_TOKEN` must document how the client passes `token=` to `server_at`.

## Calling a command

CLI, after `abx create --template <id>`:

```bash
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` values are strings. Use `--json-args` for numbers and booleans. `abx exec` is a shell or argv, not a named command.

Python SDK:

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))  # "Hello, Ada!"
        print((await sb.commands.run("python3 -c 'print(1)'")).stdout)
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` posts the keyword arguments as the JSON body of `POST /commands/hello` and returns the `result` value. `sb.commands.run` is the shell API. Attach to an existing sandbox with `await Sandbox.connect(sandbox_id)`.

On python-sdk 0.3.0, `Sandbox.create_sync`, `Sandbox.connect_sync`, `Sandbox.list_sync`, and `Sandbox.kill_by_id_sync` raise `TypeError` (the class argument is dropped). Instance methods such as `sb.run_sync` work after `await Sandbox.connect`. Use the async constructors above until [python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22) is fixed.

Local L0 does not create a cloud sandbox. `scripts/run_local_e2e.py` starts `python3 commands.py`, sets `E2E_BASE_URL`, and runs `e2e_test.py`. That test may use HTTP against `E2E_BASE_URL`. Every cloud path uses the SDK above.

## Test levels

Record a level only when it passed. The README Verified table and `tested_on` list passed providers only.

| Level | Pass means |
|---|---|
| L0 | `python3 scripts/run_local_e2e.py` starts the template and `e2e_test.py` exits 0. A missing model key inside one case may print SKIP. That SKIP is not acceptance of the agent. `E2E_RUN_LLM=0` is what the local script sets. |
| L1 | `docker build` succeeds and the log shows the pinned upstream version. |
| L2 | `abx template deploy` reaches READY, `Sandbox.create(template=<id>)` (or `connect`) succeeds, and each smoke command is invoked from outside the sandbox through the SDK and asserted. Record provider `alicloud-express`, the UTC date, template version, and SDK version. Do not record the template id. |
| L3 | A real model or product call with a key this environment has. The prompt asks for the marker `ABX_E2E_OK` and the output contains it. An empty key is a failure, not a skip, when `E2E_REQUIRE_LLM=1`. |
| L4 | `e2b`, `opensandbox`, `alicloud-container`, or `cubesandbox`, only after a run on that provider. |

`scripts/express_e2e.py <dir>` is the L2 runner. It writes `evidence/express-<YYYY-MM-DD>.json` only when every smoke command passed through the CLI and the SDK:

```json
{
  "provider": "alicloud-express",
  "date": "2026-10-15",
  "template": "my-template",
  "template_version": "1.0.0",
  "sdk_version": "0.3.0",
  "cli": "abx",
  "passed": true,
  "commands": [
    {"name": "hello", "via": "cli", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.4},
    {"name": "hello", "via": "sdk", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.3}
  ]
}
```

The checker accepts `alicloud-express` in the Verified table only when a file of that shape exists (filename `evidence/express-<date>.json` or `evidence/alicloud-express-<date>.json`) and both `via` values are present with `ok: true`. Other providers use `evidence/<provider>-<date>.json`.

### Verified on

The catalog table in the root README has a Verified on column. A cell lists a provider only when that template's evidence directory contains a passing file for it. An empty cell means no passing run is recorded. A failed run is not written into the cell and is not committed as evidence.

Inside the template README, `## Verified` is either the sentence `No provider has a passing run recorded for this template.` or a table whose first column is the provider id. The Chinese file uses `尚未记录任何通过的提供方测试。` or the same provider ids. `tested_on` lists the same ids.

## Security

- Secret values are not copied into the image, `template.yaml`, Docker history, or evidence JSON.
- `env` declares the name and an empty string. The create call injects the value.
- Logs and exception text omit tokens. `scripts/express_e2e.py` redacts environment values whose names contain `KEY`, `SECRET`, `TOKEN`, or `PASSWORD` before printing.
- Do not commit `.env`, cloud credentials, or `Dockerfile.abx-build`.

## README sections

`README.md` and `README.zh-CN.md` use these headings, in this order. The checker matches the heading text exactly.

| English | Chinese |
|---|---|
| What it does | 做什么 |
| Stack | 技术栈 |
| Problem solved | 解决的问题 |
| Quick start (CLI) | 快速开始（CLI） |
| Quick start (Python SDK) | 快速开始（Python SDK） |
| Command reference | 命令参考 |
| Configuration | 配置 |
| Resources | 资源 |
| Verified | 已验证 |
| Secondary development | 二次开发 |
| Contributing | 贡献 |
| Issues | 问题反馈 |
| License | 许可证 |

The CLI section contains an `abx run` example. The SDK section imports `Sandbox` and calls `.run` or `.run_sync`. The command reference is a table with the parameters. A non-Alibaba base adds `## Base image` / `## 基础镜像`.

## Listing and acceptance

A directory can be merged as `experimental` when `scripts/check_template.py <dir>` exits 0, L0 passes, and `docs/design/<name>.md` is filled in. `awesome-templates.yaml` gets one entry: `name`, `description`, `repo`, `path`, `tags`, `author`, `capabilities`, `status`.

`status: official` additionally requires:

1. L0 green in CI (`python3 scripts/run_local_e2e.py`).
2. L1 recorded on the PR (image build, pinned version visible).
3. L2 evidence for `alicloud-express` for the smoke commands that do not need a missing key.
4. L3 evidence before the README says the upstream agent itself works. A SKIP is not that statement.

`experimental` is the status until those passes exist. `community` is for a template maintained outside the official set that still meets the same file rules. The `providers` map on an index entry is not a verification record. The Verified column is.

`abx template install` builds on `alicloud-express`. Other providers are documented only after an L4 run.

## Contribution

1. Read `docs/template-backlog.json` and the matching section of `docs/template-market-survey-2026-10.md` when the template is already analyzed.
2. Write `docs/design/<name>.md` from `docs/design/_TEMPLATE.md`.
3. Copy `_skeleton/` to `<name>/`. Keep the Alibaba base image, the pinned server install, and the README headings.
4. Register commands that call the upstream program. Pin versions.
5. Add the index entry with `status: experimental` unless the acceptance list above is already true.
6. Run `python3 scripts/check_template.py <name>` and `python3 scripts/run_local_e2e.py`.
7. Run `python3 scripts/express_e2e.py <name>` when Express credentials are available. Commit the evidence file only when the process exits 0.
8. Open the PR. The body says which levels passed.

## Where to file issues

| Topic | Repository |
|---|---|
| Template behavior, the catalog, this spec, the checker, the Express harness | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| `agent_sandbox` or `agent_sandbox.server`: API friction, bugs, missing behavior | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Title prefix `[templates]`. Include what you ran, what you expected, what happened, a minimal repro, the provider, the template generation, and the SDK commit. |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Same title prefix and the same kind of body. |

Search open issues before filing. Comment on the existing issue when it is the same bug.

## Design pre-analysis

`docs/design/<name>.md` uses the headings in [docs/design/_TEMPLATE.md](./design/_TEMPLATE.md):

- Purpose
- Capabilities
- Exposed API
- How to build
- Express feasibility, including a line `Limiting factor:`
- Risks
- Test plan

The Express feasibility section says `yes`, `slice`, or `no`, and names the single limiting factor (`none` when the whole product fits).

## Checker

```bash
python3 scripts/check_template.py _skeleton
python3 scripts/check_template.py --all
python3 scripts/check_template.py --all --strict   # fail on legacy templates too
```

`--all` prints a conformance list and exits 0 when every `spec_version: 2` directory passes. Legacy directories are listed with their violation codes and do not fail the process. CI runs `--all`. `scripts/run_local_e2e.py` runs it as well and fails the script when a spec_version 2 directory fails.

Violation codes include `required-file`, `readme-section`, `base-image`, `dockerfile-cmd`, `dockerfile-user`, `yaml-field`, `commands-start`, `verified-evidence`, `pinned-version`, `secrets`.

## Express harness

```bash
export HOME=/home/ubuntu
unset ABX_PROVIDER
export ABX='node /path/to/agent-sandbox/dist/bin/abx.js'
export ACR_NAMESPACE=...
export ALICLOUD_ACCESS_KEY_ID=...
export ALICLOUD_ACCESS_KEY_SECRET=...
export ABX_SANDBOX_API_KEY=...
export ABX_SANDBOX_BASE_URL=...
export ABX_SANDBOX_DOMAIN=...
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
# optional: build the in-image server from a checkout
export ABX_SERVER_SDK_SOURCE=/path/to/python-sdk/server-sdk

python3 scripts/express_e2e.py python-hello \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000' \
  --command hello --arg name=E2E --expect 'Hello, E2E!'
```

`python-hello` on main does not yet declare `smoke`, `start_cmd`, or the Alibaba base image, so the flags above supply them. A spec_version 2 directory needs no flags: the harness reads `template.yaml`.

The remote name is a unique `e2e-<name>-<hex>` alias, not the catalog name, so a pre-existing generation-1 template is left alone. The `finally` block runs `abx kill <id> -y` and `abx template delete <id> -y` for ids this process created.

`--plan` prints the resolved commands and does not call `abx`.

Exit 2 means the output matched a known CLI or SDK failure mode (string `base` rejected, generation-1 update, `AuthError` / HTTP 401, or envd `promised N bytes in enveloped message`). Those were tracked as agent-sandbox `#12` `#13` `#14` and python-sdk `#15` `#17`. The deploy/run CLI fix is on `agent-sandbox` main (`#16`). The envd framing and port-9000 auth fix is on `python-sdk` main. The harness still classifies the old messages so an older binary stays explicit.

Exit 1 is any other failure. Exit 0 writes the evidence file.
