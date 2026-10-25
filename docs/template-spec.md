# Template development, listing, and acceptance

This is the normative spec for a template in this repository. [docs/template-spec.zh-CN.md](./template-spec.zh-CN.md) is the same content in Chinese. If the two files disagree, this file wins.

`docs/acceptance.md` is a pointer here. `_skeleton/` is a passing example of the file layout. It is not a catalog entry.

Tooling that later template work relies on:

| Tool | Role |
|---|---|
| `scripts/check_template.py` | Static lint. Exit 0 when the directory matches this spec. |
| `scripts/public_launch_e2e.py` | Installed CLI source launch, host CLI/Python/HTTP smoke and independent owned-resource cleanup on Express or OpenSandbox. |
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
└── evidence/                 # dated attempts; successful receipts remain distinct
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
| `evidence/*.json` | Sanitized machine-readable results. Provider/date qualification files require a passing run and independent cleanup; retain failed attempts under distinct attempt filenames without claiming provider acceptance. |

Provider-managed runtimes are catalog references, not copied source recipes. Keep their provider identity and usage contract in the managed catalog described below.

## template.yaml

```yaml
name: my-template
version: "1.0.0"
description: "One sentence."
author: "github-handle"
license: Apache-2.0
spec_version: 5

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

provides:
  app:
    protocol: agent-sandbox-server
    version: 2
    port: 9000
    operations: [commands.list, commands.run]
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
| `spec_version` | Only integer `5` is accepted. Retired and unknown schemas are rejected without compatibility mode. |
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
| `provides` | All services supplied by the template, with protocol, version, port and operations. Launch returns every declared endpoint without selecting a workflow. |
| `smoke` | List of `{command, args, expect}` run by `scripts/public_launch_e2e.py`. `args` keys are the command parameters. An optional `expect` is compared after strip for strings; without it, a successful nonempty result proves only the call path. |

`template launch` prepares the template, creates its sandbox, executes `start_cmd`,
runs `ready_cmd` and resolves every declared service endpoint. The built-in server v2
protocol also receives health checks and command discovery when declared. Other protocols are
exposed as endpoints; resolving a URL does not prove protocol readiness. All installed commands remain
available. Business tasks and services requiring task arguments are invoked when
needed; launch does not execute every registered command. Creating another sandbox
from a prepared reference does not inherit a running process.

Named commands are not listed in `template.yaml`. They are registered in `commands.py`.

## Optional application deployment (spec version 5)

Every input uses the closed [spec/template-v5.schema.json](../spec/template-v5.schema.json).
`application` remains optional. When present, its existing deployment topology,
hooks, durable state and non-null smoke expectations retain their meaning.
Template startup and application deployment remain separate operations.
Unknown fields, retired versions and invalid topology combinations fail without
compatibility mode.

`template.yaml` is the sole user configuration entry. Do not add `agent-app.yaml`.
Application deployment is an explicit CLI operation; installing a template,
importing a module, building a sandbox image, or `ProviderSandbox.create()` never executes
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
| `runtime` | `placement: external` requires `driver: python-remote-tools` without a local profile. `in-sandbox` requires `driver: sandbox-local-api` and profile `server-core-agents`. A profile does not certify that every local endpoint is enabled. |
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
still apply independently; schema validity cannot certify a launch or promote catalog status.

## Alibaba base image

The default official recipe keeps non-root `user` and declares resources in its manifest. Provider limits are separate from application requirements. Its base image is:

```
fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
```

The installed CLI stages the official source recipe and resolves its supported
`<region>` and `<tag>` placeholders using the selected provider's configuration or
CLI defaults. For OpenSandbox's single-stage official recipe with `COPY *.whl /tmp/`, shared CLI staging
builds the wheel from the exact SDK archive commit in a Docker builder stage;
original runtime instructions and non-root execution are preserved. The source
checkout is unchanged. Other image placeholders are not implicitly resolved and
portable profiles are selected explicitly. Effective build inputs enter the receipt.

The default Express recipe must not replace the platform entrypoint with `CMD`
or `ENTRYPOINT`. Preserve its generation2 startup/readiness configuration. An
explicit portable profile is a separate reviewed recipe, not a silent fallback.

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

`<40-hex-sha>` is the full immutable `Alibaba-Agent-Sandbox/python-sdk` commit,
not a short SHA or branch. A PyPI pin must identify an actually published version.
The image SDK pin belongs to the recipe; it need not change merely because the
host client gets a compatible bug-fix release.

Express uses its native preparation adapter. For OpenSandbox `template launch`,
the official wheel recipe is prepared automatically as specified above; a host
Python source checkout is unnecessary. A raw `docker build`
that bypasses CLI preparation still needs a matching wheel for `COPY *.whl`, or an
explicit recipe such as python-hello's portable profile that installs its pinned
archive directly. Missing COPY inputs are not optional Docker instructions.

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

The server reads `ABX_SERVER_TOKEN` when the process starts. When the variable is non-empty, protected requests need `Authorization: Bearer <token>` or `X-Access-Token: <token>`. Declare the name in `env` with an empty value. Provide the real value to the server process before it starts. Create-time injection (`abx create --env` or `ProviderSandbox.create(envs=...)`) applies only when that provider starts the server with those values; it cannot reconfigure a prewarmed process. Follow [runtime environment configuration](runtime-environment.md), inspect the actual service and target its configured port.

When the variable is unset, the application allows anonymous calls; provider gateway authentication remains separate. The client preserves the provider's gateway headers and sends an explicit application token as `Authorization: Bearer <token>`, also adding the existing application `X-Access-Token` header when unoccupied. Authentication failures are returned without an anonymous retry. Templates that set `ABX_SERVER_TOKEN` must document `await sb.application_client(port, token=...)` for the project Python API and `ABX_SERVER_TOKEN` for CLI named commands.

## Calling a command

CLI, after `abx --provider alicloud-express template launch <source> --yes` has started the application:

```bash
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` values are strings. Use `--json-args` for numbers and booleans. `abx exec` is a shell or argv, not a named command.

Python SDK. The client distribution on PyPI is `agent-sandbox-client`. The import stays `agent_sandbox`. `pip install agent-sandbox` installs an unrelated project.

Install the compatible published version from [Python client installation](./python-client-installation.md).
Connect to the instance launched above, using the same application token:

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main() -> None:
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
        print((await sb.commands.run("python3 -c 'print(1)'")).stdout)
    finally:
        await sb.close()

asyncio.run(main())
```

`client.commands.run` posts keyword arguments as the JSON body of `POST /commands/hello`
and returns `result`. `sb.commands.run` is the process API. Closing a connection does
not delete the sandbox: delete your owned instance with `abx kill <sandbox-id>` when
finished, and reconcile its prepared template/image separately. Record source refs
and installed package versions for acceptance.

Local L0 does not create a cloud sandbox. `scripts/run_local_e2e.py` starts `python3 commands.py`, sets `E2E_BASE_URL`, and runs `e2e_test.py`. That test may use HTTP against `E2E_BASE_URL`. Cloud acceptance must exercise the actual selected CLI/SDK/HTTP entry points.

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
from the client HTTP timeout: `sb.application_client(..., timeout=...)` sets the client HTTP timeout,
so a command deadline parameter must have a different name, such as
`command_timeout` or `timeout_s`. A client timeout does not guarantee cancellation.
Use process APIs for running, reconnecting to, and cancelling background tasks.

## Test levels

These retained evidence labels describe test scope, not promotion or increasing platform support. Record only checks actually run with exact startup, endpoint and source inputs. Old evidence retains its historical scope.

| Level | Pass means |
|---|---|
| L0 | `python3 scripts/run_local_e2e.py` starts the template and `e2e_test.py` exits 0. A missing model key inside one case may print SKIP. That SKIP is not acceptance of the agent. `E2E_RUN_LLM=0` is what the local script sets. |
| L1 | `docker build` succeeds and the log shows the pinned upstream version. |
| L2 | The recorded Express source preparation/startup reaches readiness, and declared smoke commands pass through the recorded host entry points with independent owned cleanup. Record exact source, CLI/SDK versions, startup path and checks; preserve historical deploy receipts without claiming they tested later launch code. |
| L3 | A real model or product call with a compatible key. Coding agents must modify an existing source file, create a new artifact, and pass independently executed tests in the sandbox. Verify artifacts through the remote files/process APIs when the server is remote. A response marker alone is insufficient. An empty key fails when `E2E_REQUIRE_LLM=1`. |
| L4 | `e2b`, `opensandbox`, `alicloud-container`, or `cubesandbox`, only after a run on that provider. |

The current default acceptance runner is [public source launch](public-launch-testing.md).
It calls the installed CLI, then host CLI/Python/HTTP, and independently verifies
sandbox, prepared-template and image cleanup. It records failed attempts separately;
`PARTIAL` is not a pass. The retained native deployment harness is a
[pinned maintenance workflow](canonical-express-review.md).

The following is the legacy dated receipt shape still read by the catalog checker.
Its original source, calling path and cleanup scope remain historical. It is not
the new public-launch report format and does not prove a later entry point:

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

The catalog table in the root README has a Verified on column. A cell links a recorded historical provider run. Read that receipt for its exact source, entry point, checks and date; it does not assert current default-path acceptance. An empty cell means no matching record, not lack of support. Failed attempts never populate this column or qualify a provider. Preserve their sanitized results under distinct attempt filenames; provider/date pass files require successful execution and independent cleanup.

Inside the template README, `## Verified` states the exact scope of the available evidence. An author-written pass claim does not establish an executed test. The static checker rejects hand-written provider pass tables. See [launch verification](workflows.md).

## Security

- Secret values are not copied into the image, `template.yaml`, Docker history, or evidence JSON.
- `env` declares the name and an empty string. Pass values explicitly to the process that needs them before it starts; a create call does not update existing processes.
- Logs and reports must omit secrets and native resource identifiers. The public runner keeps raw subprocess diagnostics private and exports only controlled check labels, stable codes and numeric HTTP statuses.
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

The CLI section contains an `abx run` example. The SDK section imports `ProviderSandbox`, resolves its application client with `application_client`, and calls `client.commands.run`. The command reference is a table with the parameters. A non-Alibaba base adds `## Base image` / `## 基础镜像`.

## Listing and acceptance

A directory must pass `scripts/check_template.py <dir>` and L0, with
`docs/design/<name>.md` completed. Add one `awesome-templates.yaml` entry:
`name`, `description`, `repo`, `path`, `tags`, `author`, `status`.

The existing catalog labels describe maintenance: `official` is maintained by this
project, `community` is maintained externally, and `experimental` marks development
in progress. No test automatically promotes a label. A label does not prove a
provider, startup method, terminal, interpreter or model task works.

Actual component acceptance requirements remain:

1. L0 green in CI (`python3 scripts/run_local_e2e.py`).
2. L1 recorded for the image recipe (build and pinned version).
3. L2 evidence for the implemented Express smoke path, including owned cleanup.
4. L3 evidence before claiming the upstream agent/model task works. SKIP is not a pass.

Apply the required tests and CI to the changed component as defined in the
[definition of done](project-standards.md#definition-of-done). Documentation-only
changes do not rerun unrelated cloud tests. Unfinished deployment/model acceptance
criteria keep their Issue open, regardless of catalog label. Record the exact source,
provider, entry point, test and cleanup result. Index entries must use only fields
accepted by the current catalog schema; retired capability/verification fields are rejected.

`abx --provider <provider> template launch <source>` prepares the selected recipe
and starts its application through that provider's implemented operations. Document
the actual usage contract for each provider. Claim a path is tested only when its
matching execution record exists; missing evidence does not by itself mean unsupported.

## Contribution

1. Read `docs/template-backlog.json` and the matching section of `docs/template-market-survey-2026-10.md` when the template is already analyzed.
2. Write `docs/design/<name>.md` from `docs/design/_TEMPLATE.md`.
3. Copy `_skeleton/` to `<name>/`. Keep the Alibaba base image, the pinned server install, and the README headings.
4. Register commands that call the upstream program. Pin versions.
5. Add the index entry with the maintenance/development label described above; record test results separately.
6. Run `python3 scripts/check_template.py <name>` and `python3 scripts/run_local_e2e.py`.
7. Run the public source-launch acceptance for each required provider/entry point. Preserve each attempt, assert outcomes and independently confirm owned cleanup; missing credentials leave that requirement incomplete.
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
```

`--all` checks every root directory containing `template.yaml`, including the skeleton. Every manifest requires an explicit supported `spec_version`; missing, malformed or unknown versions fail. The catalog requires `schema_version: 2`. CI and `scripts/run_local_e2e.py` use the same complete check and fail on any violation.

Violation codes include `required-file`, `readme-section`, `base-image`, `dockerfile-cmd`, `dockerfile-user`, `yaml-field`, `commands-start`, `verified-evidence`, `pinned-version`, `readme-client`, `secrets`. `pinned-version` fails when a `RUN` has neither allowed server pin above. `readme-client` fails when a spec_version 4 SDK section does not name `agent-sandbox-client`, or when a README tells the reader to `pip install agent-sandbox`.

## Native deployment maintenance

The older `scripts/express_e2e.py` and its private intent recovery remain available
for the [fixed native review workflow](canonical-express-review.md). Their native
flags and cleanup scope are tied to those pinned inputs. Current contributor and
user acceptance starts with [public source launch](public-launch-testing.md), which
uses explicit native-first `--native --json` only for Express preparation cleanup.
Never treat a successful recovery as a successful original application attempt.

## Provider-managed catalog entries

`managed_templates` is a catalog namespace separate from installable source `templates`. Each record contains exactly `name`, `provider`, `template_id`, `kind: provider-managed`, `documentation`, `historical_evidence`, `spec_version: 5` and `provides`. Native template identity stays bound to its provider. Use `provides: {}` when no application service is declared. No workflow is selected; use the provider interfaces after creation.

Exec startup requires an explicit `start_cmd`. Managed records have no such field,
so they reject `startup: exec`. Select `none` or an actual provider-supported
native `entrypoint` path; metadata does not grant provider startup support.

Managed IDs have no repository-owned Dockerfile, image version, commands.py or build context, so source image selection, steps generation and deploy checks do not apply. A native template reference does not establish immutable runtime identity. Runtime acceptance must bind the actual input, consumer and network path, observe exact operation semantics, and independently confirm owned cleanup. Shell execution cannot certify a native or unified interpreter. See [base](managed/base/README.md) and [code-interpreter-v1](managed/code-interpreter-v1/README.md).

When a changed version is verified on the same UTC date, use a distinct express-YYYY-MM-DDTHHMMSSZ.json receipt and preserve the older date-only file. Provider qualification requires the current manifest version, both passed and cleanup_verified true, and successful real CLI/SDK calls. Prior-version receipts cannot certify a changed template.

Spec4 manifests containing `application` require an explicit, non-null smoke `expect`, supporting strings, numbers, booleans, objects and arrays with structured comparison. Retired schema inputs are rejected.


Managed catalog validation: `python scripts/check_managed_catalog.py` checks exact fields, disjoint names, provided-service declarations, 14 ordered bilingual README sections, and local historical-evidence identity. `historical_evidence` links original receipts; its contents do not confer current launch certification. Only complete, input-matching receipts with independently trusted provenance can certify a path; see [launch verification](workflows.md). Managed IDs remain excluded from source image selection/steps. [Desktop](managed/desktop/README.md) and [OpenSandbox interpreter](managed/opensandbox-code-interpreter/README.md) document each entry’s prerequisites, actual evidence scope and remaining product gates.

The default Dockerfile server archive must match `scripts/server_sdk_pin.py` (or the explicit `server-sdk.commit`). The checker rejects a different fallback, so default and CI-injected builds select the same server source. Changing a pin invalidates prior source-specific image/workflow acceptance; preserve those receipts as history.
