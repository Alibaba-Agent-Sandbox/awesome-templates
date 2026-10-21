# Template development, listing, and acceptance

This is the normative spec for a template in this repository. [docs/template-spec.zh-CN.md](./template-spec.zh-CN.md) is the same content in Chinese. If the two files disagree, this file wins.

`docs/acceptance.md` is a pointer here. `_skeleton/` is a passing example of the file layout. It is not a catalog entry.

Tooling that later template work relies on:

| Tool | Role |
|---|---|
| `scripts/check_template.py` | Static lint. Exit 0 when the directory matches this spec. |
| `scripts/express_e2e.py` | L2 on `alicloud-express`. Writes evidence only after smoke and owned sandbox/template cleanup pass. Serializes ACR pushes with a file lock and stops a push that makes no progress. |
| `scripts/run_local_e2e.py` | L0 for every directory that has `commands.py` and `e2e_test.py`. Also runs the checker. |
| `scripts/image_size_report.py` | Per-layer sizes of a local image (`docker history`). |

Repository governance and completion criteria are in [project standards](project-standards.md);
shared writing and translation rules are in [documentation standards](documentation-standards.md).

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
| `spec_version` | `2` for the existing contract; `3` for the strict schema with optional `application`. Only manifests without a version are legacy. Unknown explicit versions fail. |
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

## Optional application deployment (spec version 3)

Use `spec_version: 3` to opt into the closed machine schema
[schema/template-v3.schema.json](../schema/template-v3.schema.json). All existing
sandbox fields retain their meaning. V3 requires an explicit non-null smoke `expect`; it supports strings, numbers, booleans, objects and arrays with the existing structural comparison. A v2 smoke without an expectation needs an explicit expected result when adopting v3. `application` is optional, so an ordinary
v3 sandbox template has no application deployment. v2 remains supported; adding
`application` to v2 is an error. Unknown fields, versions and topology combinations
fail the checker. Old CLI versions must reject v3 until they support this contract.

`template.yaml` is the sole user configuration entry. Do not add `agent-app.yaml`.
Application deployment is an explicit CLI operation; installing a template,
importing a module, building a sandbox image, or `Sandbox.create()` never executes
application hooks or deploys FC functions. Sandbox providers and application
deployment adapters remain separate interfaces.

The syntax-checked [local example](examples/application-local/template.yaml)
uses the existing `agents-cli` local API profile. It describes configuration,
not a newly accepted image or a durable hosted service. The
[external example](examples/application-external/template.yaml) demonstrates an
inline Serverless Devs project; its component version, role, images, database and
identity bindings must be resolved and reviewed before deployment. It is not an
executed cloud receipt or an installable catalog entry.

| Application field | Contract |
| --- | --- |
| `runtime` | `placement: external` requires `driver: python-remote-tools` without a local profile. `in-sandbox` requires `driver: sandbox-local-api` and profile `server-core-agents` or `legacy-codex-agent-api`. A profile does not certify that every local endpoint is enabled. |
| `gateway` | `placement: fc-web` selects an external gateway; `client-direct` is only for the in-sandbox runtime. |
| `deployment` | Direct access requires exactly `{adapter: none}`. FC requires `adapter: serverless-devs-fc3`, `accessRef`, `toolchainLock`, and exactly one of `inline` or `project`. Access references are names, not credentials. |
| `deployment.inline` | Serverless Devs v3 mapping with `edition: "3.0.0"`, `name`, and `resources`. Resource keys are `gateway`, `worker`, `dispatcher`; external runtime requires all three. Each resource has exact `component: fc3@X.Y.Z`, nonempty `props`, optional `actions`. The adapter extracts this mapping to a frozen generated `s.yaml`; users do not maintain another YAML. The schema validates topology, not FC properties, component availability, IAM, or deployed code. |
| `deployment.project` | Optional advanced alternative: relative path to a reviewed hand-written Serverless Devs project. Its complete referenced source tree is deployment input. |
| `deployment.toolchainLock` | Relative path to the deployment adapter's tool/version/integrity lock. JSON lock format and verified execution belong to the CLI adapter, not the template checker. |
| `sandbox` | Provider name, `lifetime: per-run`, `workspace: exclusive`, and nonempty `requiredFeatures`. Both modes require `sandbox.lifecycle`; external also requires `exec.run` and `files.rw`, in-sandbox requires `ports.url`. Features are requirements, not proof of provider support or runtime authorization. |
| `state` | External gateways require `profile: durable` and `bindingRef` naming a `bindings` key. Client-direct uses only `{profile: ephemeral}`. |
| `bindings` | Mapping from logical names to credential/service reference names. No secret values, connection strings, or signed URLs. Empty is allowed for direct local access. |
| `limits` | Positive integer `maxRunSeconds`, `maxToolSeconds`, `maxConcurrentRuns`, `maxQueuedRuns`, `maxRunsPerMinute`; `maxEventsPerRun >= 5`, `maxOutputBytes >= 1024`. Tool budget cannot exceed run budget. These declarations require runtime enforcement; the checker does not implement admission control. |
| `hooks` | Optional lists named `beforeApply` and `afterReady`, at most eight hooks per phase. Direct local access has no deployment hooks. Other phase names fail. |

Every hook declares a globally unique `id`, `executor: host-command`, argv array,
relative `cwd`, `timeoutSeconds` in `1..900`, and `envAllowlist` of environment
variable names. The deployment adapter executes reviewed argv on the host/CI and
bounds output; the checker only reads configuration. `beforeApply` validates
frozen inputs and cannot rebuild or change artifacts; `afterReady` verifies a
candidate before release. They are not sandbox startup hooks. Native Serverless
Devs actions and expressions are also executable code and require review; build
steps run before the deployment plan is frozen.

Paths must be relative, cannot contain backslashes, control characters or `..`
segments, and must resolve inside the template directory. Referenced project and
lock files and hook working directories must exist. Symlink escape is rejected.
Hook argv is never interpreted as a shell string by the template checker.

Install the pinned checker dependencies with
`python -m pip install -r scripts/requirements-spec.txt`, then run the checker and
`scripts/test_spec_tools.py`. Runtime/image/provider/model acceptance tiers below
still apply independently; schema validity cannot promote catalog status or
`tested_on`.

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

# Heavy tools first (one RUN, pinned versions, pip --no-cache-dir, npm cache cleaned).
# commands.py is the last COPY so a command edit does not rebuild that layer.
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40-hex-sha>.tar.gz#subdirectory=server-sdk"; \
    fi

# Pin every other installer the same way: pip name==X.Y.Z, npm package@X.Y.Z.
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
```

### Allowed `agent-sandbox-server` pins

A `RUN` line must use one of these two forms. The checker accepts either. A comment that only mentions the pin does not count.

| Form | Line |
|---|---|
| PyPI | `pip install --no-cache-dir "agent-sandbox-server==X.Y.Z"` |
| python-sdk git archive | `pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40-hex-sha>.tar.gz#subdirectory=server-sdk"` |

`<40-hex-sha>` is the full commit of `Alibaba-Agent-Sandbox/python-sdk` (40 hex characters), not a short sha. On 2026-10-15, `agent-sandbox-server==0.3.0` was not on PyPI (`https://pypi.org/pypi/agent-sandbox-server/0.3.0/json` returned 404). Use the archive pin until that release exists. The archive install is the more exact pin: it selects the commit, including the Express server fixes on `61c43e0` and later.

`abx template deploy` injects an `agent-sandbox-server` wheel into the build context when `ABX_SERVER_SDK_SOURCE` points at a `server-sdk` tree. The `if` branch installs that wheel. The `else` branch still carries one of the two pins. Build with BuildKit so an empty `COPY *.whl` is accepted when no wheel was injected (`DOCKER_BUILDKIT=1`).

Every `pip install` uses `--no-cache-dir`. An npm install deletes the npm cache in the same layer (`npm cache clean --force`).

### Image layers

Put package installs in an early layer and `COPY commands.py` last. On 2026-10-15 this VM pushed several template images at once to `registry.cn-hangzhou.aliyuncs.com`. `ss` showed the registry connections `rwnd_limited` about 98.8 percent (the receiver window, not the round trip: `minrtt` was under 1 ms). One upload moved about 35 KB/s and another did not increase `bytes_sent` over 8 seconds. Images were 0.9–1.2 GB. They share the two layers of base `v0.0.49` (about 632 MB, mostly one 606 MB rootfs) locally, but each harness push uses a new ACR repository, so a cross-repo mount of that base is not guaranteed and the base can be uploaded again.

`docker history` sizes are uncompressed diffs. The registry stores compressed blobs, and each blob is its own request. Dozens of small `COPY` layers (a CLI split into many parts) add a round trip per blob. `python3 scripts/image_size_report.py <image>` prints one line per layer. Pass `--base` to see how many rootfs digests are still the base image.

```bash
python3 scripts/image_size_report.py <local-image> \
  --base fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime/base:v0.0.49
```

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

`/health` is exempt from server-token authentication; the provider gateway may still authenticate that request. A successful health probe does not prove named-command authentication or model configuration.

The server reads `ABX_SERVER_TOKEN` when the process starts. When the variable is non-empty, protected requests need `Authorization: Bearer <token>` or `X-Access-Token: <token>`. Declare the name in `env` with an empty value. Provide the real value to the server process before it starts. Create-time injection (`abx create --env` or `Sandbox.create(envs=...)`) applies only when that provider starts the server with those values; it cannot reconfigure a prewarmed process. Follow [runtime environment configuration](runtime-environment.md), inspect the actual service and target its configured port.

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

Python SDK. The client distribution on PyPI is `agent-sandbox-client`. The import stays `agent_sandbox`. `pip install agent-sandbox` installs an unrelated project.

Check package availability before using the index command below. For an
unpublished release, use the paired, pinned source installation in
[Python client installation](./python-client-installation.md).

```bash
python3 -m pip install agent-sandbox-client
```

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

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

The checked-out python-sdk includes the sync-classmethod fix in [python-sdk#24](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/24). Older commits that drop the class argument raise `TypeError`; update the SDK or use async constructors. Record the source commit as well as the package version when validating a checkout.

Local L0 does not create a cloud sandbox. `scripts/run_local_e2e.py` starts `python3 commands.py`, sets `E2E_BASE_URL`, and runs `e2e_test.py`. That test may use HTTP against `E2E_BASE_URL`. Every cloud path uses the SDK above.

### HTTP POST contract

Every README has a dedicated `Quick start (HTTP POST)` section after the Python
SDK section. It shows the same task as CLI/SDK, the sandbox port URL,
`POST /commands/<name>`, `Content-Type: application/json`, the direct JSON
argument object (no `args` wrapper), and the `{"result": ...}` response.
Document required/default values, types, allowed ranges, 400 argument errors,
401 authentication, 404 unknown commands, and 500 execution errors. Explain
`ABX_SERVER_TOKEN` authentication separately from provider gateway authentication;
never put real credentials in an example. Use the gateway access header required
by the selected provider in addition to any server authentication.

Named commands return buffered results. Distinguish a command execution deadline
from the client HTTP timeout: `Sandbox.run(timeout=...)` controls the HTTP request,
so a command deadline parameter must have a different name, such as
`command_timeout` or `timeout_s`. A client timeout does not guarantee cancellation.
Use process APIs for running, reconnecting to, and cancelling background tasks.

## Test levels

Record a level only when it passed. The README Verified table and `tested_on` list passed providers only.

| Level | Pass means |
|---|---|
| L0 | `python3 scripts/run_local_e2e.py` starts the template and `e2e_test.py` exits 0. A missing model key inside one case may print SKIP. That SKIP is not acceptance of the agent. `E2E_RUN_LLM=0` is what the local script sets. |
| L1 | `docker build` succeeds and the log shows the pinned upstream version. |
| L2 | `abx template deploy` reaches READY, `Sandbox.create(template=<id>)` (or `connect`) succeeds, and each smoke command is invoked from outside the sandbox through the SDK and asserted. Record provider `alicloud-express`, the UTC date, template version, and SDK version. Do not record the template id. |
| L3 | A real model or product call with a compatible key. Coding agents must modify an existing source file, create a new artifact, and pass independently executed tests in the sandbox. Verify artifacts through the remote files/process APIs when the server is remote. A response marker alone is insufficient. An empty key fails when `E2E_REQUIRE_LLM=1`. |
| L4 | `e2b`, `opensandbox`, `alicloud-container`, or `cubesandbox`, only after a run on that provider. |

`scripts/express_e2e.py <dir>` is the L2 runner. It writes `evidence/express-<YYYY-MM-DD>.json` only when every smoke command passed through the CLI and the SDK:

The runner also requires successful owned sandbox/template cleanup before writing
the pass file or returning exit 0, including independent SDK/official-list
readback that the known sandbox IDs/templates and exact alias are absent. CLI
kill/delete acknowledgements alone do not establish that. It refuses an existing exact alias through
`abx --json template list --official-api`. Cleanup failures and unknown deploy/create
responses retain a private, credential-free owned intent.
`python3 scripts/express_e2e.py --recover-intent PRIVATE_PATH` uses existing official
template list/delete and SDK sandbox list/kill APIs to reconcile only that attempt.
An unresolved response stays blocked; recovery success does not grant provider
acceptance to the original failed run. Registry-image retention is a separate
operator responsibility; this runner cleans sandbox/template resources and local
deploy processes.
The canonical deploy passes `--acr-repo <owned-alias> --tag review`; the private
intent records these exact registry identifiers for the operator.

```json
{
  "provider": "alicloud-express",
  "date": "2026-10-15",
  "template": "my-template",
  "template_version": "1.0.0",
  "sdk_version": "0.3.0",
  "cli": "abx",
  "passed": true,
  "cleanup_verified": true,
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
- `env` declares the name and an empty string. Pass values explicitly to the process that needs them before it starts; a create call does not update existing processes.
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
| Quick start (HTTP POST) | 快速开始（HTTP POST） |
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

`--all` prints a conformance list and exits 0 when every explicit `spec_version: 2` or `3` directory passes. Legacy directories are listed with their violation codes and do not fail the process. CI runs `--all --strict`. `scripts/run_local_e2e.py` runs it as well and fails the script when a supported-spec directory fails.

Violation codes include `required-file`, `readme-section`, `base-image`, `dockerfile-cmd`, `dockerfile-user`, `yaml-field`, `commands-start`, `verified-evidence`, `pinned-version`, `readme-client`, `secrets`. `pinned-version` fails when a `RUN` has neither allowed server pin above. `readme-client` fails when a spec_version 2/3 SDK section does not name `agent-sandbox-client`, or when a README tells the reader to `pip install agent-sandbox`.

## Express harness

```bash
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

python3 scripts/express_e2e.py python-hello
```

The current spec_version 2 `python-hello` declares its smoke and startup commands in `template.yaml`; the harness reads them directly. Preserve the caller’s native HOME.

The remote name is a unique `e2e-<name>-<hex>` alias, not the catalog name, so a pre-existing generation-1 template is left alone. The `finally` block runs `abx kill <id> -y` and `abx template delete <id> -y` for ids this process created. It also kills the deploy process group and any `docker push` whose command line contains that alias. A wall-clock kill of only the `abx` process used to leave the push running (the push is not in the same process group unless the harness starts one).

The harness calls `abx template deploy` with the existing flags (`--json`, `-y`, `--generation`, `--start-cmd`, `--ready-cmd`, `--alias`, `--acr-repo`, `--tag`, `--timeout`, `--verbose`). It does not push the image itself. `--timeout` is the READY poll budget inside `abx`. It is not a cap on the upload. `--verbose` is what makes layer lines show up under `--json`; without them the CLI prints phase lines only and a slow push looks idle. The harness drops `CI` and the other variables `abx` uses to detect CI (`GITHUB_ACTIONS`, `GITLAB_CI`, and the rest of that list), because CI mode suppresses those lines.

Concurrent harnesses take an exclusive `flock` on `/tmp/abx-acr-push.lock` (`ABX_ACR_PUSH_LOCK` overrides the path) for the whole deploy. The CLI does not expose a push-only step, so the lock covers build, push, and the READY poll. That is coarser than a lock around `docker push` alone. Push locking and a no-progress timeout belong in `abx` ([agent-sandbox#29](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/29)). Until that ships, the harness is the lock.

`--idle-timeout` (default 180) kills the deploy when stdout and stderr produce no new bytes. A push that is still printing layer status is in progress and is not killed. `--wall-timeout` (default `max(21600, --timeout)`) is only a safety cap for a deploy that never goes idle. Six hours covers a progressing upload of about 1 GB at the ~35 KB/s measured on a contended link; the idle timer is what stops a push that has stopped moving. `--push-retries` (default 2) retries a stalled push or a push error. A known CLI/SDK blocker and a Docker build failure are not retried. Each retry stops leftover `docker push` processes for this alias first, so a new upload is not piled on an orphan.

`--plan` prints the resolved commands, the lock path, and the timeouts. It does not call `abx`.

Exit 2 means the output matched a known CLI or SDK failure mode (string `base` rejected, generation-1 update, `AuthError` / HTTP 401, or envd `promised N bytes in enveloped message`). Those were tracked as agent-sandbox `#12` `#13` `#14` and python-sdk `#15` `#17`. The deploy/run CLI fix is on `agent-sandbox` main (`#16`). The envd framing and port-9000 auth fix is on `python-sdk` main. The harness still classifies the old messages so an older binary stays explicit.

Exit 1 is any other failure. Exit 0 writes the evidence file.

Alibaba FC resource profile: memory must be a multiple of64MB and1..4GiB per vCPU. The checker rejects invalid declared profiles before cloud use. [Official CreateFunction contract](https://api.alibabacloud.com/document/FC/2023-03-30/CreateFunction).

## Provider-managed catalog entries

`managed_templates` is an additive catalog namespace separate from installable source `templates`. Its fields are name/provider/template_id/kind/documentation/evidence/verification_scope/native_interpreter_verified. Managed IDs have no repository-owned Dockerfile, image version, commands.py or build context, so source image selection, steps generation and deploy checks do not apply. Runtime acceptance must record SDK fallbacks, observed inventory and independent owned cleanup; it cannot certify another provider or a native interpreter. See [base](managed/base/README.md) and [code-interpreter-v1](managed/code-interpreter-v1/README.md).

When a changed version is verified on the same UTC date, use a distinct express-YYYY-MM-DDTHHMMSSZ.json receipt and preserve the older date-only file. Provider qualification requires the current manifest version, both passed and cleanup_verified true, and successful real CLI/SDK calls. Prior-version receipts cannot certify a changed template.


Managed catalog validation: `python scripts/check_managed_catalog.py` checks the exact fields, disjoint names,14ordered bilingual README sections, local evidence identity, native-interpreter claim and runtime cleanup/checks. External catalog-only entries use `verification_scope: catalog-only-unverified` with evidence `status: NOT_VERIFIED`, `passed: false`, `native_interpreter_verified: false`; that is valid metadata and never a runtime/provider pass. A runtime pass requires actual checks and independent cleanup. Managed IDs remain excluded from source image selection/steps. [Desktop](managed/desktop/README.md) and [OpenSandbox interpreter](managed/opensandbox-code-interpreter/README.md) document the separate live prerequisites and unverified product gates.
