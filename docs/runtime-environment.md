# Configure the template application before launch

[中文](runtime-environment.zh-CN.md)

Use one startup owner: `abx template launch` prepares the template and starts its declared application. Connect the SDK to that running sandbox to call its named commands. Model settings and `ABX_SERVER_TOKEN` must reach the application process before it imports the template; connecting another client does not reconfigure that process.

## Launch once, then connect

Follow [installation and provider setup](using-templates.md#installation). The example uses the published CLI 0.5.6, Python client 0.4.0a6 and the `python-hello` template. Configure Express and securely set `ABX_SERVER_TOKEN` in your local environment before launching. For a model template, also set the configuration names declared in its README; declaring an empty value in `template.yaml` does not provide a secret.

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
```

Copy the returned sandbox ID into the Python example below. Use the same provider and application token as the launch. The application already runs on its declared port 9000; this connection does not start another server.

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

The expected result is `Hello, Ada!`. For OpenSandbox, use `--provider opensandbox` for launch and `provider="opensandbox"` for the connection, after its [provider setup](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Use the selected template's actual service port and command names. For CLI calls, HTTP POST and cleanup, follow [the complete calling example](using-templates.md#cli-sdk-and-http).

`client.aclose()` and `sb.close()` close client resources; they do not delete the sandbox. When finished, the owner deletes that instance with `abx --provider alicloud-express kill <sandbox-id>` and separately removes any exact owned prepared template/image no longer needed. Do not create another sandbox merely to consume this running application's API.

## Startup configuration and authentication

Keep the template's startup command and declared services together. If model configuration is missing, inspect the template's documented read-only setup command and launch configuration. Do not start a second command server to work around a failed configuration check. Creating an instance from a prepared reference is an advanced startup path; an already started application must not be started again by another owner. Authors should follow the existing [SDK template-authoring guide](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/docs/en/guide/authoring-templates.md).

`ABX_SERVER_TOKEN` is read at application process startup. A non-empty token protects named-command calls; an unset token allows anonymous application calls. A later create/connect call cannot add authentication to an already running process. `/health` is exempt from the application token, while provider gateway authentication may still apply. Health alone does not verify command authentication or model settings.

The application token, provider gateway credentials and upstream model keys have separate purposes. `application_client(..., token=...)` preserves provider gateway headers and sends the application token using the supported headers. Do not log tokens or place model keys in command arguments, prompts or image layers. See the [authentication specification](template-spec.md#auth-token) for the exact header behavior.

## Verification scope

This guide follows the current unified launch and public connection API. Its examples receive syntax, installed-import and local-link checks; those checks are not a fresh cloud or model test. Provider acceptance must identify the exact source, packages, calling path and owned cleanup.

The [historical Aider PR](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88) retains a separate image/process experiment and real-model result at its recorded inputs. It does not establish the current unified launch, other providers' environment behavior or all templates' model capabilities, and it is not the recommended startup procedure.
