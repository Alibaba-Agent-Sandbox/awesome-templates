# opensandbox-code-interpreter

[中文](README.zh-CN.md).

## What it does

Catalog entry for the original OpenSandbox Code Interpreter image. Create it through the OpenSandbox provider/server; this repository does not own its Dockerfile or register it on Express.

## Stack

Original [OpenSandbox example at30348cbd](https://github.com/opensandbox-group/OpenSandbox/blob/30348cbdfe4b9cfd49e0963617aed357a8f1ac4c/docs/examples/code-interpreter.md) uses imagev1.1.0, also published as sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.1.0. The tag is a version reference, not an immutable image digest or deployment receipt. Provider plugin0.3.0 speaks the OpenSandbox lifecycle/execd contract.

## Problem solved

Discover the external interpreter image without confusing it with Express[code-interpreter-v1](../code-interpreter-v1/README.md). The current Agent Sandbox OpenSandbox provider supports shell/files; native code.interpret is unsupported(E8004), so shell Python is not a native interpreter/session pass.

## Quick start (CLI)

Use the Node-capable[provider host](../../using-templates.md#client-entry-compatibility), not a native-only step builder. Install the exact public provider revision; configure its independent account/server first. These examples were syntax/source reviewed, NOT_RUN on a live backend. Replace the owned sandbox ID with the result of your own create; do not delete the managed template definition.

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//opensandbox@9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d --yes
abx provider info opensandbox
abx provider doctor opensandbox
abx --provider opensandbox create --template opensandbox/code-interpreter:v1.1.0 --timeout 180 -y
abx --provider opensandbox exec <owned-sandbox-id> -- python3 -c 'print(6*7)'
abx --provider opensandbox kill <owned-sandbox-id> -y
```

## Quick start (Python SDK)

Install the[paired agent-sandbox-client](../../python-client-installation.md) and the same provider/engine. Configure the provider-specific settings below before startup. The actual Agent Sandbox SDK create/shell/files and original native interpreter flow below was verified on hosted Docker. Install the original native SDKs using the exact source/uv lockfiles in the [reproduction workflow](../../../.github/workflows/managed-opensandbox.yml). CLI visitor commands above remain source reviewed, not a separate CLI product E2E receipt.

```python
import asyncio, os, uuid
from urllib.parse import urlsplit
from opensandbox import Sandbox as NativeSandbox
from opensandbox.config import ConnectionConfig
from code_interpreter import CodeInterpreter, SupportedLanguage
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    provider = "opensandbox"
    sb = await Sandbox.create(provider=provider, template="opensandbox/code-interpreter:v1.1.0", timeout=180,
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
        url = urlsplit(os.environ.get("ABX_OPENSANDBOX_BASE_URL", "http://127.0.0.1:8080"))
        config = ConnectionConfig(domain=url.netloc, protocol=url.scheme,
            api_key=os.environ.get("ABX_OPENSANDBOX_API_KEY") or os.environ.get("OPEN_SANDBOX_API_KEY"),
            use_server_proxy=True)
        native = await NativeSandbox.connect(sid, connection_config=config)
        try:
            interpreter = await CodeInterpreter.create(sandbox=native)
            try:
                context = await interpreter.codes.create_context(SupportedLanguage.PYTHON)
                first = await interpreter.codes.run("owned_value = 37\nowned_value", context=context)
                assert first.error is None and first.result[0].text.strip() == "37"
                second = await interpreter.codes.run("owned_value + 5", context=context)
                assert second.error is None and second.result[0].text.strip() == "42"
                await interpreter.codes.delete_context(context.id)
            finally:
                await interpreter.aclose()
        finally:
            await native.close()
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

This image supplies no repository-defined POST /commands/execute_code. The provider creates through POST /v1/sandboxes with optional OPEN-SANDBOX-API-KEY, preserving the original code-interpreter entrypoint, then uses execd for shell/files. Native interpreter requests need the original OpenSandbox Code Interpreter SDK; Agent Sandbox run_code is unsupported(E8004), not silently claimed as working. See the[exact provider contract](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d/opensandbox/README.md). No raw invented HTTP result envelope is supplied.

## Command reference

| Operation | Parameters/result | Scope |
| --- | --- | --- |
| Sandbox.create | provider:string, template:string, timeout:int seconds, metadata:dict; returns owned sandbox | Native provider lifecycle |
| commands.run | command:string, timeout:int seconds; exit_code/stdout/stderr | Generic shell, not desktop/native interpreter |
| files.write/read/remove/exists | sandbox path and text/bytes | Generic file round trip |
| original codes.create_context/run/delete_context | Python source and native context; result/error | Original native interpreter/session API |
| interpreter.aclose / native.close | no remote deletion | Release local native SDK resources |
| kill/get_info_by_id | exact owned ID, same provider/config | Independent absence must follow cleanup |

No repository @command is registered. Unsupported features raise E8004; authentication/transport/permission failures remain failures. Client timeout and backend TTL differ; use bounded commands and explicit cleanup.

## Configuration

Set ABX_OPENSANDBOX_BASE_URL to a reachable OpenSandbox server root (a trailing/v1 is normalized). ABX_OPENSANDBOX_API_KEY/OPEN_SANDBOX_API_KEY is optional if your own server is anonymous. Other native domain/protocol/proxy/image settings are in the pinned provider guide. Never replace these with Express credentials or convert an Express template ID. Keep the original interpreter entrypoint; explicitly overriding it can disable the native service.

## Resources

The recorded native run requested2CPU/3072MB/600seconds on hosted Linuxamd64 Docker and verified the container image identity. Actual resource utilization was not measured; visitor capacity still depends on the selected external deployment. Finite180second example TTL is not a provider quota guarantee. No KVM/privileged/GUI/native-kernel claim is inferred from catalog metadata. Keep credentials/private URLs/IDs/raw logs out of public receipts; delete only your own sandbox, forwards and fixtures.

## Verified

PASS: original OpenSandbox Docker backend, actual Agent Sandbox SDK create/shell/files, original SDK connection to the same ID, real Jupyter health and Python execution, persistent and isolated contexts, deliberate program failure, context deletion, independent SDKNotFound/Docker absence and local engine/server shutdown. All24checksPASS11.769seconds after dependency/image preparation. [Native receipt](../evidence/verification-opensandbox-code-interpreter-2026-10-21-native-docker.json), [actual hosted run](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39643705253).

Original interpreter image digest: `opensandbox/code-interpreter@sha256:133a3c1720dd52291a019740c2987e7164ea6de79e23d8198798e58950ae2e6e`; execd digest and exact original server/native SDK/provider/CLI/client pins/observed versions are in the receipt. Native SDKs report1.2.0rc2.dev222+g30348cbd; paired Agent Sandbox packages0.3.0. No real account/cloud/model credential was needed for this isolated local server.

This is OpenSandbox native interpreter acceptance, not Express deployment or Agent Sandbox native code.interpret support; generic run_code still returnsE8004. No GUI, privileged nesting or other provider qualification is implied. Preserve the [earlier NOT_VERIFIED record](../evidence/verification-opensandbox-code-interpreter-2026-10-21.json) and failed-run engineering records as history.

## Secondary development

Keep this entry in managed_templates, outside source image selection/steps. Do not add a fake source directory, Alibaba Dockerfile, commands.py or tested_on to represent this external ID. Reproduce offline tests with the exact provider fixture described in the[verification record](../../../.agents/evidence/verify/2026-10-21-external-managed-catalog.md).

For each runtime/SDK/image update, run actual SDK create/shell/files, a real original native interpreter calculation/output and persistent-kernel behavior (if claimed), then independent cleanup. Generic shell success does not fulfill this gate. Preserve a new dated result; source-image L1/L2/steps do not certify a provider-managed ID.

## Contributing

Follow[CONTRIBUTING](../../../CONTRIBUTING.md),[project standards](../../project-standards.md) and[documentation standards](../../documentation-standards.md). Keep English/Chinese guides, catalog scope and dated evidence aligned. The managed catalog checker validates metadata/claims; it does not turn NOT_VERIFIED into a runtime pass.

## Issues

Tracking [Issue34](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/34);[templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues),[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues),[providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues),[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Native service/GUI behavior belongs to its upstream project.

## License

Authored documentation/testsApache-2.0. Upstream image, bundled OS/applications, SDKs and service retain their own licenses/terms; this repository copies no external Dockerfile, binary or registered image. Source inspection is not a redistribution grant or vendor endorsement.
