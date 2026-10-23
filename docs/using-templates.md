# Using and verifying templates

Read this page for setup and the calling contract, then use the selected
template's README for its exact command names, arguments, runtime limits and
examples. The [specification](template-spec.md) owns development and acceptance
rules; [source-runtime diagnostics](express-source-runtime.md) explain a
separate check that does not establish image deployment acceptance.

## Installation

On 2026-10-18 public 0.3.0 metadata for `@agent-sandbox/cli`,
`agent-sandbox-client` and `agent-sandbox-server` returned HTTP 404. Package
names alone are not proof of publication. Install the paired Python packages
using [the pinned source instructions](python-client-installation.md).
For a reproducible CLI source build with Node 20 or 22:

```bash
git clone https://github.com/Alibaba-Agent-Sandbox/agent-sandbox.git agent-sandbox-cli
git -C agent-sandbox-cli checkout 850a9bb780c44857630ac7928c2361c7be270921
npm --prefix agent-sandbox-cli ci
npm --prefix agent-sandbox-cli run build
ABX_CLI_ENTRY="$(pwd)/agent-sandbox-cli/dist/bin/abx.js"
abx() { node "$ABX_CLI_ENTRY" "$@"; }
abx --version
```

This shell function invokes the built entry by absolute path. For standalone
binaries follow the CLI owner's [installation guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/binary-installation.md)
and verify the selected release exists before downloading it. Source pins here
identify a setup baseline; they do not validate later template/SDK/CLI revisions.

Configure the provider securely before deployment. Express sandbox calls need
`ABX_SANDBOX_API_KEY` and the matching `ABX_SANDBOX_BASE_URL` and
`ABX_SANDBOX_DOMAIN`. Docker/ACR template deployment additionally needs a working
Docker daemon, authorized Alibaba control-plane credentials and ACR namespace.
Do not paste credentials into shell command arguments, reports or Issues.

## CLI, SDK and HTTP

From this repository checkout, with Express configured, deploy the selected
folder. For `python-hello`:

```bash
abx template deploy ./python-hello -y
abx create <template-id> --detach
abx sandbox command list <sandbox-id>
abx run <sandbox-id> hello --arg name=Ada
```

Replace angle-bracket placeholders with IDs from the preceding command; they
are not literal shell syntax. `abx run` calls a registered command. `abx exec`
is the process/shell API. Use `--json-args` for typed numeric/boolean arguments.
Template-specific READMEs show complete examples for their own commands.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

The SDK returns the `result` value. Use the printed URL as `ABX_SERVER_URL`:

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello"   --header 'Content-Type: application/json' --data '{"name":"Ada"}'
# {"result":"Hello, Ada!"}
```

Arguments are the direct JSON body, without an `args` wrapper. `GET /commands`
discovers public commands. Server authentication is separate from provider and
gateway credentials. An anonymous Express port-9000 server does not need the
envd token. If `ABX_SERVER_TOKEN` is configured, send that server token in an
Authorization Bearer header; use `await sb.application_client(9000, token=...)`
and close the returned application client in the SDK. Authentication failures do
not trigger an anonymous retry.
A provider that requires gateway access headers additionally needs its documented
headers. Do not send one provider's key to another provider.

Missing/invalid command arguments return 400, failed server auth 401, unknown
commands 404 and execution failures 500 with `error` and `type`. A caller timeout
does not prove remote cancellation. Each README documents command-specific
timeouts, processes and cleanup. Delete the created sandbox and only the template
you own when finished:

```bash
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## Evidence and providers

| Evidence | What it proves | What it cannot prove |
|---|---|---|
| Static checks | YAML, index and documentation conformance | Executable product behavior |
| L0 local HTTP | Started server and command assertions | Image pins, cloud deploy or a skipped model call |
| L1 actual image build | Build and declared keyless image checks | Production CLI deploy wrapper or real cloud |
| Source-runtime cloud diagnostic | Exact uploaded source/dependencies on an existing base | Changed Dockerfile or template deployment |
| L2 canonical deploy | Docker/ACR deploy, READY, new sandbox, external CLI/SDK smoke and owned cleanup | Every HTTP command or real-model coding unless explicitly tested |
| L3 product/model | The recorded task and independently checked result | A different template source/version or all upstream product behavior |
| L4 another provider | The actual recorded provider and workload | Unconfigured vendors |

`tested_on` and the README Verified table must match a passing, exact-version
provider evidence file. Keep previous evidence as history; never transfer its
badge to changed code. A green image job or skipped model/provider is not a pass
for another tier. Existing draft PRs must retain these boundaries.

Only the Express Dockerfile workflow is supplied by these catalog sources.
Installed provider plugins have their own declared capabilities. An image URI or
pre-existing template ID accepted by a provider does not establish that it can
build/deploy this catalog. Consult the provider's own README and test on that
provider before adding a verification badge.

## Documentation and catalog ownership

- Each template README: CLI/SDK/HTTP examples, parameters, configuration,
  limitations, verified evidence and extension instructions.
- `docs/design/<name>.md`: design rationale and feasibility.
- `template-spec.md`: normative development/acceptance rules.
- `python-client-installation.md`: one paired source-install recipe.
- `.agents/`: engineering decisions and dated verification, not user API docs.
- `awesome-templates.yaml`: template source catalog, consumed by CLI and the
  [registry repository](https://github.com/Alibaba-Agent-Sandbox/registry).

The old `registry/index.html` and `registry/catalog.json` in this repository had
no CLI, SDK, registry-ingestion or CI consumer and carried stale provider
claims. They are retired. Website UI originates in the
[website repository](https://github.com/Alibaba-Agent-Sandbox/website), while
registry builds its public catalog from source repositories. Do not copy either
frontend or generated catalog back here.

[中文](using-templates.zh-CN.md)

Local acceptance cleanup preserves Python verifier sources, including `e2e_sdk.py`, while removing generated artifacts and caches. The SDK controller must remain available for subsequent acceptance.


## Client entry compatibility

Custom commands, providers, sessions and `sb.server` examples explicitly import
`from agent_sandbox.api.sandbox import Sandbox`. This native async entry works on
accepted main and the standard-client candidate, avoiding await on the synchronous
root Sandbox. Standard Sandbox/AsyncSandbox and interpreter imports have a separate
contract: [SDK47](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47).

The current Express entry takes a positional template. This guide and template README examples target the CLI source revision above. Older native builds have different flags; consult the help shipped with that revision.

| Operation | Current Express entry |
| --- | --- |
| Scripted create | `abx create <template-id> --detach` |
| Shell | `abx exec --cwd /tmp <sandbox-id> sh -c 'echo hello'` |
| Owned cleanup | `abx kill <sandbox-id>` |

Template deploy, named commands through `abx run`, upload and download remain project extensions. Standard create without `--detach` opens a PTY. These documentation corrections do not change template sources or provider acceptance tiers.
