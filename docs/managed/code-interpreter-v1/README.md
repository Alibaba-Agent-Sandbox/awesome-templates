# code-interpreter-v1

## What it does

Provider-managed template ID on Alibaba Express. Create a sandbox directly; this repository does not own its Dockerfile, image version or deployment lifecycle.

## Stack

Observed inventory on2026-10-19; the provider-managed image is mutable, so these are observations, not repository pins.

| Component | Observed version |
| --- | --- |
| Python | 3.13.13 |
| Node.js | v20.20.2 |
| Git | git version 2.47.3 |
| pip | 26.0.1 |
| numpy | 2.4.6 |
| pandas | 3.0.3 |
| matplotlib | 3.11.1 |
| jupyter | not installed |
| ipykernel | 7.3.0 |

## Problem solved

Use shell, files and SDK code execution without building a user image.

## Quick start (CLI)

Native CLI0.3 syntax (check `abx create --help`):

```bash
abx create code-interpreter-v1 --detach --timeout 180
abx exec <sandbox-id> -- python3 -c 'print(6*7)'
abx kill <sandbox-id>
```

See [client entry compatibility](../../using-templates.md#client-entry-compatibility) for the standard CLI. Delete only your sandbox; do not delete the provider-managed template definition.

## Quick start (Python SDK)

Install the [paired `agent-sandbox-client`](../../python-client-installation.md), then:

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="code-interpreter-v1", timeout=180)
    try:
        print((await sb.commands.run("python3 --version")).stdout)
        await sb.files.write("/tmp/owned-example.txt", "hello")
        print(await sb.files.read("/tmp/owned-example.txt"))
        await sb.files.remove("/tmp/owned-example.txt")
        result = await sb.run_code("print(6*7)")
        assert result.exit_code == 0 and result.stdout.strip() == "42"
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

The native run_code service returned HTTP404 in this run. The SDK shell fallback executed successfully and returned42. Native interpreter service, multiple language kernels and persistent contexts are unverified. An installed ipykernel does not establish service availability.

## Quick start (HTTP POST)

This managed definition has no repository-defined `/commands/*` server. Use the SDK shell/files/run_code APIs; no named-command HTTP endpoint is supplied by this catalog entry.

## Command reference

SDK: Sandbox.create(template: str, timeout: int=300); commands.run(cmd: str, timeout: int) returns exit_code/stdout/stderr; files.write/read/remove/exists operate on sandbox paths; run_code(code: str) returns execution results. See [public SDK source](https://github.com/Alibaba-Agent-Sandbox/python-sdk). No custom named command is registered.

## Configuration

Use the configured Alibaba SDK/CLI account. Keep credentials in process environments; no model key is required. Create-time environment does not guarantee reconfiguration of prewarmed servers; see [runtime environment](../../runtime-environment.md).

## Resources

Observed Linux x86_64/non-root, with no /dev/kvm or Docker socket. Resource sizing, pricing and image revisions are provider-managed. Set a finite sandbox timeout, kill owned instances and independently read back absence.

## Verified

| Provider | Runtime verification | Scope |
| --- | --- | --- |
| alicloud-express | [PASS receipt](../evidence/code-interpreter-v1-2026-10-19T154153Z.json) | SDK shell/files/run_code fallback + real CLI exec; cleanup confirmed |

The native run_code service returned HTTP404 in this run. The SDK shell fallback executed successfully and returned42. Native interpreter service, multiple language kernels and persistent contexts are unverified. An installed ipykernel does not establish service availability.

Other providers were not tested. This is a managed-runtime receipt, not source-template L1/L2 deployment acceptance.

## Secondary development

Platform steps build a new source template; they do not rebuild provider-managed IDs. Start from the [source skeleton](../../../_skeleton/README.md) for custom dependencies. Reproduce this entry:

```bash
python scripts/verify_managed_templates.py code-interpreter-v1 --cli /path/to/abx --output /tmp/managed-proof
```

## Contributing

Follow [contribution standards](../../../CONTRIBUTING.md). Add a timestamped receipt on rerun; preserve history.

## Issues

[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) · [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) · [agent-sandbox CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Tracking Issue [32](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/32).

## License

Documentation and verification script: Apache-2.0. Provider-managed image and bundled software retain their own licenses; this repository does not redistribute that image.
