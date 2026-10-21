# desktop

[中文](README.zh-CN.md).

## What it does

Provider-managed E2B `desktop` catalog entry. The provider owns its mutable template registration/image and desktop runtime. This repository supplies documentation and tests, without copying/rebuilding its template.

## Stack

Original E2B Desktop source at[9fe5f55f](https://github.com/e2b-dev/desktop/tree/9fe5f55fabe3bd9f0277661a830e1d228b463b44) builds production aliasdesktop from Ubuntu22.04/Xfce. That is inspected source, not an observed deployed version. The official Desktop SDK is now in the E2B monorepo; neither Desktop SDK nor GUI tasks are claimed by Agent Sandbox generic exec/files.

## Problem solved

Discover the external desktop ID without confusing it with the independently implemented Express[OSWorld slice](../../../osworld/README.md). Generic shell/files smoke is separate from native screenshot/input/stream acceptance.

## Quick start (CLI)

Use the Node-capable[provider host](../../using-templates.md#client-entry-compatibility), not a native-only step builder. Install the exact public provider revision; configure its independent account/server first. These examples were syntax/source reviewed, NOT_RUN on a live backend. Replace the owned sandbox ID with the result of your own create; do not delete the managed template definition.

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//e2b@9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d --yes
abx provider info e2b
abx provider doctor e2b
abx --provider e2b create --template desktop --timeout 180 -y
abx --provider e2b exec <owned-sandbox-id> -- python3 -c 'print(6*7)'
abx --provider e2b kill <owned-sandbox-id> -y
```

## Quick start (Python SDK)

Install the[paired agent-sandbox-client](../../python-client-installation.md) and the same provider/engine. Configure the provider-specific settings below before startup. This actual Agent Sandbox SDK example runs shell/files only; it is syntax checked and NOT_RUN live.

```python
import asyncio, uuid
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    provider = "e2b"
    sb = await Sandbox.create(provider=provider, template="desktop", timeout=180,
        metadata={"verification": "managed-example-" + uuid.uuid4().hex})
    sid = sb.id
    try:
        result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
        assert result.exit_code == 0 and result.stdout.strip() == "42"
        path = "/tmp/owned-example-" + uuid.uuid4().hex + ".txt"
        await sb.files.write(path, "owned-example\n")
        assert await sb.files.read(path) == "owned-example\n"
        await sb.files.remove(path)
        assert not await sb.files.exists(path)
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()
    try:
        await Sandbox.get_info_by_id(sid, provider=provider)
    except SandboxNotFoundError:
        pass
    else:
        raise RuntimeError("owned sandbox cleanup is not verified")

asyncio.run(main())
```

Use unique metadata/private creation intent in production so an ambiguous create can be reconciled; a lost response plus empty inventory is not confirmed cleanup. No model-generated code runs in this example.

## Quick start (HTTP POST)

There is no repository-defined POST /commands/screenshot or port9000 command server for this managed ID. The E2B provider maps lifecycle creation to POST /sandboxes with X-API-Key; generic shell uses the native process protocol, not an invented JSON named command. Use the SDK above and the[provider contract](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d/e2b/docs/README.md). Native E2B Desktop screenshot/input/stream APIs require its original SDK and separate real GUI acceptance.

## Command reference

| Operation | Parameters/result | Scope |
| --- | --- | --- |
| Sandbox.create | provider:string, template:string, timeout:int seconds, metadata:dict; returns owned sandbox | Native provider lifecycle |
| commands.run | command:string, timeout:int seconds; exit_code/stdout/stderr | Generic shell, not desktop/native interpreter |
| files.write/read/remove/exists | sandbox path and text/bytes | Generic file round trip |
| kill/get_info_by_id | exact owned ID, same provider/config | Independent absence must follow cleanup |

No repository @command is registered. Unsupported features raise E8004; authentication/transport/permission failures remain failures. Client timeout and backend TTL differ; use bounded commands and explicit cleanup.

## Configuration

Set ABX_E2B_API_KEY to a genuine independent E2B account credential, and ABX_E2B_BASE_URL/ABX_E2B_DOMAIN only when your E2B deployment requires them. The pinned provider reads no generic E2B_API_KEY or Express key. Here the generic key equals an Express alias and was never forwarded. No genuine ABX_E2B_API_KEY was available.

## Resources

CPU, memory, image version, exposed endpoints and device capabilities belong to the external deployment; no live inventory was observed here. Finite180second example TTL is not a provider quota guarantee. No KVM/privileged/GUI/native-kernel claim is inferred from catalog metadata. Keep credentials/private URLs/IDs/raw logs out of public receipts; delete only your own sandbox, forwards and fixtures.

## Verified

No provider has a passing product/runtime run recorded for this entry. [Dated NOT_VERIFIED state](../evidence/verification-desktop-2026-10-21.json).

The Issue explicitly allows an unverified catalog-only result without a genuine E2B key. Actual Agent Sandbox SDK rejects missing provider-specific credentials before engine/network even with a synthetic generic Express key. Published provider tests14PASS0FAIL0SKIP include the actual pinned E2B2.55.0SDK against local HTTP. These are SDK/protocol checks, not E2B desktop creation, screenshot/input or Express verification.

## Secondary development

Keep this entry in managed_templates, outside source image selection/steps. Do not add a fake source directory, Alibaba Dockerfile, commands.py or tested_on to represent this external ID. Reproduce offline tests with the exact provider fixture described in the[verification record](../../../.agents/evidence/verify/2026-10-21-external-managed-catalog.md).

Before promoting runtime claims, run actual SDK create/shell/files, a real Desktop SDK screenshot with decoded pixels and observable input/application state change, then independent cleanup. Preserve a new dated result; source-image L1/L2/steps do not certify a provider-managed ID.

## Contributing

Follow[CONTRIBUTING](../../../CONTRIBUTING.md),[project standards](../../project-standards.md) and[documentation standards](../../documentation-standards.md). Keep English/Chinese guides, catalog scope and dated evidence aligned. The managed catalog checker validates metadata/claims; it does not turn NOT_VERIFIED into a runtime pass.

## Issues

Tracking [Issue33](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/33);[templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues),[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues),[providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues),[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Native service/GUI behavior belongs to its upstream project.

## License

Authored documentation/testsApache-2.0. Upstream image, bundled OS/applications, SDKs and service retain their own licenses/terms; this repository copies no external Dockerfile, binary or registered image. Source inspection is not a redistribution grant or vendor endorsement.
