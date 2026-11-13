# Template YAML v1 specification

[中文](template-spec.zh-CN.md)

`template.yaml` declares the resources to prepare and deploy. This format requires a matching development CLI; published CLI 0.5.10 does not implement it.

## Directory layout

Keep the resource values in `template.yaml`, image instructions in the Dockerfile, and application behavior in source code. Optional `registry.yaml` supplies publication metadata and initialization forms. Local execution does not read Registry defaults again.

## template.yaml

```yaml
specVersion: 1
name: python-hello
vars:
  location: cn-hangzhou
sandbox:
  agent:
    provider: alicloud-express
    template:
      region: ${vars.location}
      buildConfig:
        dockerfile: ./Dockerfile
      generation: 2
      cpu: 2
      memorySize: 2048
      startCommand: agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py
      readyCommand: agent-sandbox-server healthcheck --port 9000
```

| Field | Meaning |
| --- | --- |
| `specVersion` | Integer `1`. |
| `name` | Project name, 1–63 lowercase ASCII letters, digits and hyphens. |
| `vars` | Optional author-defined reusable values; no reserved image variable names. Direct literal values work too. |
| `sandbox.<name>` | Named Sandbox resource with a Provider, template, optional volumes and resource actions. |
| `sandbox.<name>.template` | Provider attributes; Express uses `region`, `image`, `generation`, `cpu`, `memorySize`, `diskSize`, network/logging/registry settings and native template commands. |
| `sandbox.<name>.template.reference` | Borrow an existing native template. Only `region` may accompany it; borrowed resources are never updated or removed. |
| `sandbox.<name>.volumes` | Named static volume declarations. `props` creates an owned volume; `reference` borrows one. `retain: true` keeps an owned volume during removal. Volumes share `template.region`. |
| `serving.<name>` | Native component selector, `props` and optional resource actions. |

Logical names are globally unique across Sandbox and Serving. `access`, `application`, `deployment`, user-defined `outputs`, `instance`, `runtimeConfig`, `sandboxConfig`, and generic `build`/`builds` are not resource inputs. Reuse the configured credentials. CPU/memory combinations and account/regional availability remain Provider checks; omitted API properties are not silently filled with guessed defaults.

See the [nested field reference](template-fields.md) and [schema](../spec/template-v1.schema.json).

## Build sources and image meaning

`buildConfig` has exactly two alternatives: `dockerfile` with optional `context`, or `steps`. It cannot be empty and `context` cannot stand alone. Paths are relative to the directory containing `template.yaml`; omitted `context` is the Dockerfile's directory. There is no implicit scan for a Dockerfile when the whole build configuration is absent.

| Configuration | Result |
| --- | --- |
| `image` alone | Use the existing image to prepare the template. |
| `image` and `buildConfig.dockerfile` | Build and push to that image address, then prepare the template. Without an explicit address, the configured build destination must supply one. |
| `image` and `buildConfig.steps` | Use the image as the input for native template steps. The result is a prepared template ID; native steps do not promise an OCI image export to the input address. |
| `reference` | Reuse an existing template without a build or update. |

Native steps use `type: USER|WORKDIR|ENV|RUN` and `args: string[]`. ENV uses key/value pairs. USER takes a username and optional boolean-string sudo flag; RUN takes a command and optional execution user. Runtime secrets do not belong in image ENV or template build steps.

For Express, `registryConfig` optionally overrides pull authentication, TLS and registry network settings. Omit the whole object when unused. Ordinary Linux and recognizable ACR image references do not require duplicate `osType`, registry type or ACR instance inputs. Storage clients belong in the Dockerfile or base image; installing them does not create or mount volumes or grant storage access. Provider internals handle required image copying/injection instead of exposing a second advanced build configuration.

## Serving and actions

```yaml
serving:
  api:
    component: serverless-devs/fc3@0.1.26
    actions:
      pre-deploy:
        - component: serverless-devs/fc3@0.1.26 build --dockerfile ./server/Dockerfile --context ./server
    props:
      region: cn-hangzhou
      functionName: sandbox-api
      runtime: custom-container
      code: ./server
      customContainerConfig:
        image: registry.example/project/api:release-1
        port: 9000
      environmentVariables:
        SANDBOX_TEMPLATE_ID: ${resources.agent.output.templateId}
```

The image address above is a placeholder. Use a repository you can push to. The `serverless-devs/` prefix selects the component execution adapter; native `fc3@0.1.26` owns its properties. FC build and deploy have distinct image-push behavior. Existing remote images must use the component's supported skip-push path; omitting a build action alone does not establish that behavior.

Actions run on the deployment host. `run` executes a shell command; `component` invokes the selected native component command with the resource context. Optional `path` selects a working directory. `pre-deploy` runs before the resource, `success-deploy` after it is ready, `fail-deploy` on failure and `complete-deploy` on either outcome. Sandbox readiness means a successful template readiness query, not merely acceptance of a build request. Output references order dependent resources; unresolved names and cycles fail before deployment.

## Templates and dynamic instances

Deployment prepares reusable templates and static volumes. Business code, SDK or `abx sandbox create --template <template-id>` creates instances and chooses their environment, lifetime and mounts. `startCommand` and `readyCommand` retain native template preparation/snapshot semantics; they are not per-instance hooks. A resumed prewarmed process does not automatically read new create-time environment values. Follow the [runtime environment guide](runtime-environment.md) for application startup and model credentials.

Image defaults are ordinary Dockerfile ENV declarations. Empty credential names contain no credentials. Pass private runtime values explicitly at instance creation or through the application runtime. Ports, listeners, network access and application protocols are distinct; declaring a port does not expose or authenticate a business API.

## Configuration and publication

Use one JSON-compatible YAML 1.2 Core document with string keys, no duplicate keys, aliases or custom tags, and at most 1 MiB of UTF-8. Static catalog tools do not evaluate `${env('NAME')}`, `${vars.key}` or resource output expressions.

Optional `registry.yaml` contains `specVersion`, `name`, `version`, bilingual `description`, `author`, `license`, `tags`, bilingual `readme` and `parameters`. Each parameter names an existing value with a JSON Pointer `target` and bilingual `title`. A sensitive parameter also specifies `environmentVariable`; its target must be the corresponding `${env('NAME')}` expression. Initialization edits those concrete local values or private sources; subsequent execution uses only `template.yaml` and its explicit references.

## Alibaba base image

The default official recipe keeps non-root `user` and declares resources in its manifest. Provider limits are separate from application requirements. Its base image is:

```
fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
```

The installed CLI stages the official source recipe and resolves its supported
`<region>` and `<tag>` placeholders using the selected provider's configuration or
CLI defaults. The recipe installs its exact published server dependency directly;
no generated wheel, SDK source archive or host Python checkout is required.
The source checkout is unchanged. Other image placeholders are not implicitly
resolved and portable profiles are selected explicitly. Effective build inputs enter the receipt.

The default Express recipe must not replace the platform entrypoint with `CMD`
or `ENTRYPOINT`. Preserve its generation2 startup/readiness configuration. An
explicit portable profile is a separate reviewed recipe, not a silent fallback.

`Dockerfile` shape:

```dockerfile
FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive

# Heavy tools first (one RUN, pinned versions, pip --no-cache-dir, npm cache cleaned).
# commands.py is the last COPY so a command edit does not rebuild that layer.
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

# Pin every other installer the same way: pip name==X.Y.Z, npm package@X.Y.Z.
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
```

### Published `agent-sandbox-server` dependency

A `RUN` instruction must install one exact, actually published distribution, for example:

```dockerfile
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"
```

A comment does not count as an install. Git-archive and injected-wheel fallbacks are removed from current recipes. The image dependency belongs to the Dockerfile and is verified in the actual image; a host client version alone does not establish the guest server version.

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
| Streaming | A named command is one request and one JSON response. Live stdout belongs to the process API (`sb.commands.stream`, `abx sandbox exec`), not to `@command`. Return the full text, or write a file and let the client read it with `sb.files`. |
| Errors | Missing or mistyped arguments never call the function: HTTP 400 `{"error", "type": "ValueError"}`. Raise `RuntimeError` (or `ValueError`) for an upstream failure. The server returns HTTP 500 `{"error": "<message>", "type": "<ExceptionName>"}`. A non-zero upstream exit is an exception, not a successful string. Keep secrets out of the message. |
| Hidden | `@command(hidden=True)` stays callable and is omitted from `GET /commands`. |
| `start()` | Only under `if __name__ == "__main__"`. `agent-sandbox-server serve --commands` imports the module. A `start()` at import time breaks that path. |
| Upstream | The body of a product command runs that product's own non-interactive argv. Do not splice a prompt into a shell string. Pass argv as a list. |

`GET /commands` returns `{"commands": [{"name", "description", "args": [{"name", "type", "required", "default", "description"}]}]}`.

### Auth token

`/health` is exempt from server-token authentication; the provider gateway may still authenticate that request. A successful health probe does not prove named-command authentication or model configuration.

The server reads `ABX_SERVER_TOKEN` at application startup. Protected requests use `Authorization: Bearer <token>` or `X-Access-Token: <token>`. Ordinary templates start through `run.py`, which generates or accepts the token, creates the instance, explicitly starts the application and verifies authenticated discovery. Keep credentials out of native template preparation commands and image layers. See [runtime configuration](runtime-environment.md).

When the variable is unset, the application allows anonymous calls; provider gateway authentication remains separate. The client preserves the provider's gateway headers and sends an explicit application token as `Authorization: Bearer <token>`, also adding the existing application `X-Access-Token` header when unoccupied. Authentication failures are returned without an anonymous retry. Templates that set `ABX_SERVER_TOKEN` must document `await sb.application_client(port, token=...)` for the project Python API and `ABX_SERVER_TOKEN` for CLI named commands.

## Calling a command

CLI, after `abx --provider alicloud-express deploy <source> --yes` has started the application:

```bash
abx sandbox command run <sandbox-id> hello --arg name=Ada
abx sandbox command run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx sandbox exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` values are strings. Use `--json-args` for numbers and booleans. `abx sandbox exec` is a shell or argv, not a named command.

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
not delete the sandbox: delete your owned instance with `abx sandbox delete <sandbox-id> --yes` when
finished, and reconcile its prepared template/image separately. Record source refs
and installed package versions for acceptance.

Local L0 does not create a cloud sandbox. `scripts/run_local_e2e.py` starts `python3 commands.py` for ordinary Sandbox templates or the actual managed module for Managed Agents API, sets `E2E_BASE_URL`, and runs `e2e_test.py`. That test may use HTTP against `E2E_BASE_URL`. Cloud acceptance must exercise the actual selected CLI/SDK/HTTP entry points.

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
`PARTIAL` is not a pass. The retired pinned cloud workflow is retained only as
[historical documentation](canonical-express-review.md).

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

Historical Express receipts use `evidence/express-<date>.json` or `evidence/alicloud-express-<date>.json`; other providers use `evidence/<provider>-<date>.json`. The static checker does not certify a provider from locally supplied receipts, even if their fields claim success.

### Verified on

The catalog table in the root README has a Verified on column. A cell links a recorded historical provider run. Read that receipt for its exact source, entry point, checks and date; it does not assert current default-path acceptance. An empty cell means no matching record, not lack of support. Failed attempts never populate this column or qualify a provider. Preserve their sanitized results under distinct attempt filenames; provider/date pass files require successful execution and independent cleanup.

Template READMEs are usage guides: keep validation reports, historical acceptance, development instructions and test-level narratives in engineering records, design documents or contributor guides. They are not required README sections. Preserve all original evidence and the acceptance gates above. An author-written pass claim does not establish an executed test; the static checker continues to reject hand-written provider pass tables. See [launch verification](workflows.md).

## Security

- Secret values are not copied into the image, `template.yaml`, Docker history, or evidence JSON.
- instance-creation `envs` declares the name and an empty string. Pass values explicitly to the process that needs them before it starts; a create call does not update existing processes.
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
| Contributing | 贡献 |
| Issues | 问题反馈 |
| License | 许可证 |

For managed Managed Agents API applications, use `Quick start (Python HTTP client)` / `快速开始（Python HTTP 客户端）` in place of the Python SDK heading. These applications use `httpx` against the Gateway; a dedicated Gateway client SDK is not provided.

Before launch, explain required provider credentials separately from application and model credentials, and document the actual model, endpoint, API-key or product-login configuration consumed by the template. Do not invent a universal variable mapping for upstream tools.

For Managed Agents API, show explicit `abx deploy` deployment and standard Gateway HTTP through Python `httpx`, with the public API table and managed close/delete cleanup. The following client requirements apply to ordinary Sandbox templates. The CLI section contains an `abx sandbox command run` example. The SDK section imports `ProviderSandbox`, resolves its application client with `application_client`, and calls `client.commands.run`. The command reference is a table with the parameters. A non-Alibaba base adds `## Base image` / `## 基础镜像`.

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

`abx --provider <provider> deploy <source>` prepares the selected recipe
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

`--all` checks every root directory containing `template.yaml`, including the skeleton. Every manifest requires an explicit supported `specVersion: 1`; missing, malformed or unknown versions fail. The catalog requires `schema_version: 3`. CI and `scripts/run_local_e2e.py` use the same complete check and fail on any violation.

Violation codes include `required-file`, `readme-section`, `base-image`, `dockerfile-cmd`, `dockerfile-user`, `yaml-field`, `commands-start`, `verified-evidence`, `pinned-version`, `readme-client`, `secrets`. `pinned-version` fails when a `RUN` has neither allowed server pin above. `readme-client` fails when a ordinary Sandbox templates SDK section does not name `agent-sandbox-client` (Managed Agents API instead names `httpx`), or when a README tells the reader to `pip install agent-sandbox`.

## Native preparation maintenance

Source recipes build through Dockerfile by default. Native Provider steps APIs remain independently available. scripts/prepare_steps.py emits engineering-only prepared-steps.yaml, not a deployable public template.yaml. Acceptance registers through the native API, then launches a v1 reference. Smoke/priority/wave live in scripts/template-checks.json as engineering checks, not resource fields.

## Provider-managed catalog entries

Keep native Provider/template.reference identities, documentation and historical proof. A reference does not confer current verification, source installation or rebuildability.
