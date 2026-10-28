# Using templates

[中文](using-templates.zh-CN.md)

Choose a template, configure the sandbox platform and any model service it needs, launch once, then call its named commands. Each template README supplies its exact parameters, model/authentication setup and a useful task through CLI, Python and HTTP.

## Installation

Install published CLI 0.5.8 and Python client 0.4.0a6. Use a virtual environment for Python. The Python distribution is a preview, so the version is explicit. Node 20+ is required for npm installation; Node 22+ is recommended for terminal support.

```bash
npm install -g @agent-sandbox/cli@0.5.8 --registry=https://registry.npmjs.org
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --index-url https://pypi.org/simple 'agent-sandbox-client==0.4.0a6'
abx --version
```

For the standalone binary, use the [CLI installation guide](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/binary-installation.md). If `abx` is not on PATH, apply the PATH instruction printed by the installer.

### Configure the sandbox platform

For an Express **source** template, prepare Docker, an ACR namespace and the build account permissions, then configure:

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SANDBOX_API_KEY="<sandbox-platform-api-key>"
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
export ALICLOUD_ACCESS_KEY_ID="<build-access-key-id>"
export ALICLOUD_ACCESS_KEY_SECRET="<build-access-key-secret>"
export ACR_NAMESPACE="<your-acr-namespace>"
```

The default control-plane URL and data-plane domain are derived from the selected region. Override `ABX_SANDBOX_BASE_URL` and `ABX_SANDBOX_DOMAIN` only when the platform's instructions require a different endpoint or gateway. The Sandbox API key must match that platform/region. See the [CLI configuration reference](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/reference/configuration.md) for the exact account and ACR settings. These are platform credentials, not model credentials.

For OpenSandbox, first follow its [provider setup](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md), then set `ABX_PROVIDER=opensandbox` for both launch and every later operation. Its server/container registry prerequisites differ from Express. The four managed entries have their own README and backend; starting an existing platform template does not require rebuilding a source recipe.

### Configure the application and model

The CLI generates a private application token during normal template launch, saves it locally and reuses it for later commands. To use your own token or call the service from an external SDK/HTTP client, follow [application authentication](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/guide/guided-configuration.md). Configure the template's documented model API key, endpoint, model selector and any required account login separately. Sandbox, application and model credentials serve different purposes.

Templates use different upstream configuration. Do not assume every tool consumes `ABX_LLM_*`, supports arbitrary OpenAI-compatible endpoints, or inherits a login from your machine. Non-model tools do not need a model key. Commercial account login, API-key login and optional web-service passwords are described in the applicable README.

In CLI 0.5.8, declared **empty** template env values can be filled from the host environment. A non-empty manifest value wins over a same-name host export. Use a command's documented model argument to select another model. For an empty startup-only model/key/endpoint setting, export the new value and launch a new instance from the public recipe; use the new returned sandbox ID. A local template copy is only needed to change a non-empty manifest default or the implementation. Only declared runtime settings are carried through this path. Changing exports after launch does not reconfigure an already running process.

## CLI, SDK and HTTP

This walkthrough also calls the application from external Python/HTTP clients, so it sets a custom `ABX_SERVER_TOKEN` and reuses it for launch and calls. CLI-only use does not require setting a token manually.

The `python-hello` template below needs no model service. The example's credential and ID placeholders must be replaced before use; set `ABX_PROVIDER` consistently as described above.

```bash
export ABX_SERVER_TOKEN="<independent-application-token>"
export ABX_HTTP_TIMEOUT=660
abx template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --sandbox-timeout 1800 --yes
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command list "$ABX_SANDBOX_ID"
abx run "$ABX_SANDBOX_ID" hello --arg name=Ada
```

Expected result: `Hello, Ada!`. Launch prepares the template and starts its declared application; it returns the sandbox ID and references to retained prepared resources. `abx run` calls named commands, while `abx exec` executes a process. Numeric and boolean named-command arguments use `--json-args`.

The three timeout controls serve different purposes: `--timeout` is the build deadline; `--sandbox-timeout` is the instance lifetime; `ABX_HTTP_TIMEOUT` is the CLI HTTP wait. A model command's own execution limit is separate. For a 600-second coding task, an 1800-second instance and a 660-second client wait avoid the default 300-second instance/30-second SDK wait expiring first.

### Python SDK

Save and run this complete example in the configured Python environment. Connect to the already running sandbox; do not create a second instance and expect the first instance's application to be present.

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

`client.commands.run` calls the template application. `sb.commands.run` executes a process. Both `client.aclose()` and `sb.close()` release client resources; neither deletes the sandbox. Use the selected template's actual command, parameters, port and client wait.

### HTTP POST

Save and run this example to call `POST /commands/hello` directly. It resolves the provider URL and gateway headers rather than assuming that every platform exposes a bare host/port:

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        occupied = {key.lower() for key in headers}
        token = os.environ["ABX_SERVER_TOKEN"]
        if "authorization" not in occupied:
            headers["Authorization"] = "Bearer " + token
        if "x-access-token" not in occupied:
            headers["X-Access-Token"] = token
        if {"authorization", "x-access-token"}.issubset(occupied):
            raise ValueError("Gateway occupies both application authentication headers")
        url = httpx.URL(endpoint)
        url = url.copy_with(path=url.path.rstrip("/") + "/commands/hello")
        async with httpx.AsyncClient(timeout=660) as http:
            response = await http.post(url, headers=headers, json={"name": "Ada"})
            response.raise_for_status()
            print(response.json())
    finally:
        await sb.close()

asyncio.run(main())
```

Expected response: `{"result":"Hello, Ada!"}`. The command arguments are the direct JSON body. Preserve gateway headers and any URL path/query. The application's `X-Access-Token` header also works through OpenSandbox's proxy, which removes Bearer authorization. If the gateway already uses Authorization, the example keeps it and uses the free application token header. A gateway occupying both supported application-authentication headers needs a compatible route; never replace its credentials or retry anonymously.

For another template, change the command path and JSON arguments to its documented task. Set the client wait long enough for that task. A client timeout is not proof that the remote task stopped.

### Export files and clean up

Use `abx download "$ABX_SANDBOX_ID" /remote/path ./local-file` or `await sb.files.read_bytes("/remote/path")` before removing the sandbox. Only delete the instance owned by your task:

```bash
abx kill "$ABX_SANDBOX_ID"
```

Prepared templates/images may remain for reuse. When no longer needed, remove the exact owned resources reported by launch using the selected platform's management tools. Do not delete shared base templates or other users' resources.

## Evidence and providers

Maintainer test procedures and dated results live in [public launch testing](public-launch-testing.md) and the [engineering index](../.agents/README.md), rather than user template READMEs. A historical run describes its recorded inputs; it does not promise every model, terminal or interpreter feature.

## Documentation and catalog ownership

- Template READMEs: tasks, installation, configuration, command parameters, limitations, output and cleanup.
- `docs/design/<name>.md` and [CONTRIBUTING](../CONTRIBUTING.md): implementation and authoring.
- `template-spec.md`: normative development rules.
- `.agents/` and template-local evidence: engineering decisions and dated verification.
- `awesome-templates.yaml`: the source catalog consumed by the CLI and [Registry](https://github.com/Alibaba-Agent-Sandbox/registry).

## Client entry compatibility

These provider/application examples use `ProviderSandbox`. Standard `Sandbox` / `AsyncSandbox` interpreter interfaces are separate; follow the selected template's instructions and the [SDK entry-point guide](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/README.md). `abx create <platform-template-id>` selects an existing platform template, whereas source templates use `abx template launch <source-reference>`.
