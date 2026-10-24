# Using and verifying templates

Read this page for setup and the calling contract, then use the selected
template's README for its exact command names, arguments, runtime limits and
examples. The [specification](template-spec.md) owns development and acceptance
rules; [source-runtime diagnostics](express-source-runtime.md) explain a
separate check that does not establish image deployment acceptance.

## Installation

Install the published CLI and preview Python SDK (Node 22+ is recommended for terminal support):

```bash
npm install -g @agent-sandbox/cli@0.4.16
python3 -m pip install 'agent-sandbox-client==0.3.1a5'
abx --version
```

For standalone binaries, follow the [CLI installation guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/binary-installation.md). Docker and a writable image registry are needed to build source templates. Configure the selected provider using its guide; keep credentials in environment variables or the provider configuration.

## CLI, SDK and HTTP

For Express, configure its Sandbox API key, base URL/domain, control-plane credentials and ACR namespace. Set `ABX_SERVER_TOKEN` securely before launching the application:

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
abx sandbox command list <sandbox-id>
abx run <sandbox-id> hello --arg name=Ada
```

Launch returns the sandbox ID and prepared template reference. The CLI starts the application for this instance. `abx run` calls a named template command; `abx exec` runs a process. Use `--json-args` for numeric/boolean arguments.

Connect the Python SDK to that running instance. Creating another instance from its template reference requires its own application startup; it does not inherit the first instance's running process.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

For HTTP, use the port URL from `abx sandbox url <sandbox-id> --port 9000` as `ABX_SERVER_URL`:

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello"   --header 'Content-Type: application/json'   --header "Authorization: Bearer $ABX_SERVER_TOKEN" --header "X-Access-Token: $ABX_SERVER_TOKEN" --data '{"name":"Ada"}'
# {"result":"Hello, Ada!"}
```

Arguments are the direct JSON body. The existing application `X-Access-Token` header also works through the OpenSandbox server proxy, which strips Bearer authorization. The CLI and Python application client add it automatically when that header is unoccupied. A provider gateway may require its own headers: preserve those values, including an existing gateway `X-Access-Token`. A failed authentication is an error, never a reason to retry anonymously.

When finished, delete the instance with `abx kill <sandbox-id>`. The launch journal identifies the prepared template and image retained for reuse. Delete those exact owned resources separately when they are no longer needed. Connecting a client does not transfer ownership or automatically delete the instance.

For OpenSandbox, install/configure the [provider](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md) and select `--provider opensandbox` on every CLI call and `provider="opensandbox"` when connecting Python. The CLI prepares the default source recipe directly. A template with a declared portable profile may also be built with explicit `--build-profile portable`.

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

The [2026-10-22 matrix](../.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json) records 46 source templates passing Express image/HTTP and OpenSandbox image/HTTP checks. [Steps results](../.agents/evidence/verify/2026-10-22-current-steps-after-backend-qualification.json) record the separate Express steps route. These are real historical tests, with the original inputs and calling paths. OpenSandbox used sandbox-local/bridge HTTP; those results do not certify later host `template launch` changes or unrun model tasks.

A missing record means no matching test record, not an unsupported platform. Read the date, template input, provider, build method and executed checks; do not infer terminal or interpreter coverage from a command API pass. Historical receipts remain unchanged.

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
