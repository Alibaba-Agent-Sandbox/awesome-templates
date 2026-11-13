# Configure the application at runtime

[中文](runtime-environment.zh-CN.md)

`abx deploy .` prepares reusable Sandbox templates and deploys any declared Serving resources. Ordinary source templates include `run.py` to create a dynamic instance and start their application with runtime credentials. Follow [installation](using-templates.md#installation) and the selected template's README.

```bash
abx deploy . --yes
python3 run.py --template <prepared-template-id> --timeout 1800
```

`run.py` preserves the template's startup command, forwards only its `RUNTIME_ENV_NAMES`, waits for server health and checks authenticated command discovery. Export the documented model key, endpoint and model settings before running it. Image defaults remain in the Dockerfile. Changing your local environment after startup does not reconfigure a running application.

The script generates an independent application token unless `ABX_SERVER_TOKEN` is supplied. It stores the token, Provider and acknowledged Sandbox ID in `.sandbox-session.json` with owner-only permissions. This file is private and ignored by Git. It refuses to overwrite an existing session: choose another `--session` path for a second instance. Startup failure attempts to delete the owned instance; keep the session file if cleanup needs retry.

For later CLI calls, load the token without displaying it:

```bash
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
```

Python clients can read the same private file directly:

```python
import asyncio
import json
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    session = json.loads(Path(".sandbox-session.json").read_text())
    sb = await ProviderSandbox.connect(session["sandbox_id"], provider=session["provider"])
    try:
        client = await sb.application_client(9000, token=session["application_token"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

This example is for `python-hello`; use your template's command and port. Closing clients does not delete the instance. Export useful files, then run `abx --provider alicloud-express sandbox delete <sandbox-id> --yes`. Delete the private session file only after its instance is removed. Prepared templates and images have separate lifetimes.

The Sandbox platform key, application token and model key serve different systems. `/health` alone does not verify application authentication. The SDK preserves Provider gateway authentication while adding the application token. See [authentication](template-spec.md#auth-token) and [CLI, SDK and HTTP](using-templates.md#cli-sdk-and-http).
