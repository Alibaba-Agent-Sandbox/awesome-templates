# apply-patch

[中文](README.zh-CN.md)

## What it does

Runs the actual official Codex *** Begin Patch dialect: add, update, move and delete. Patch bytes enter native stdin through a private temporary file, without a shell or patch text in argv.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

Alibaba FC base v0.0.49, generation2, non-root user. `npm ci --ignore-scripts` installs official @openai/codex0.162.1/native architecture packages using [lockfile integrity](package-lock.json). The validated native binary is dispatched by apply_patch argv0. The corresponding official release tag points to [092d3acd](https://github.com/openai/codex/tree/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d). This uses official prebuilt packages; it does not claim a local rebuild from that source commit.

## Problem solved

Supplies the real Codex file tool without a model account, Rust compiler, Docker or KVM. Linux x86_64/aarch64 only.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//apply-patch --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" apply_patch --json-args '{"patch_text":"*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n"}'
```

Creates `hello.txt`; inspect `exit_code == 0` and the actual file.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('apply_patch', patch_text='*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n')
            print(result)
            Path('hello.txt').write_bytes(await sb.files.read_bytes('/home/user/app/hello.txt'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/apply_patch`

```json
{
  "patch_text": "*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Result |
| --- | --- | --- |
| apply_patch | patch_text: str required, nonempty UTF-8 up to256KiB; cwd: str optional empty=WORKSPACE, existing subdirectory | {stdout: str, stderr: str, exit_code: int} from actual native parser |
| apply_patch_version | none | actual native `codex-cli 0.162.1` |
| apply_patch_smoke | none | APPLY_PATCH_OK only after real add/update/move/delete/literal bytes and owned cleanup |

Upstream failures retain nonzero exit_code; HTTP200 means the invocation completed, not that patching succeeded. Missing/undeclared arguments return400 and unknown command404. The SDK coerces scalar JSON values to declared strings; malformed patches still fail in the native parser. File and move paths must be relative to cwd; absolute paths, .., backslashes and existing symlinks are rejected before executing any part. An upstream failure may leave partial in-workspace edits; patching is not transactional.

## Configuration

No model key. WORKSPACE defaults to /home/user/app. Export ABX_SERVER_TOKEN before application launch; see [runtime environment](../docs/runtime-environment.md). Native patch subprocesses receive only PATH and LANG, without model/cloud credentials.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
abx download "$SANDBOX_ID" /home/user/app/hello.txt ./hello.txt
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

2vCPU,2048MB,port9000. Each patch has a30-second deadline and256KiB per-output-stream limit. Owned process groups are stopped before reaping the original leader. Temporary patch files close automatically; caller modifications persist. Path preflight is not an OS isolation boundary against concurrent same-user rename/symlink races.

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/apply-patch.md).

## Issues

[Template Issue60](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/60); CLI defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues); SDK defects: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues).

## License

Template and Codex: Apache-2.0. Retain pinned-source [upstream-LICENSE](upstream-LICENSE) and official native npm metadata/notices.
