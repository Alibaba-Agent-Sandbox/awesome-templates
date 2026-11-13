# Using templates

[中文](using-templates.zh-CN.md)

Choose a template, configure the sandbox platform and any model service it needs, launch once, then call its named commands. Each template README supplies its exact parameters, model/authentication setup and a useful task through CLI, Python and HTTP.

## Installation

These examples require a reviewed YAML v1 development revision. Replace the revision placeholder with the matching CLI commit; checking out main does not select an unreleased change. Published CLI 0.5.10 does not support these new entry points. Install the CLI from source with Node 20+; Python examples continue to use client 0.4.0a7 in a virtual environment.

```bash
git clone https://github.com/Alibaba-Agent-Sandbox/agent-sandbox.git
cd agent-sandbox
git checkout <reviewed-yaml-v1-cli-revision>
npm ci
npm run build
npm link
cd ..
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --index-url https://pypi.org/simple 'agent-sandbox-client==0.4.0a7'
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

The template's `run.py` generates a private application token unless you supply `ABX_SERVER_TOKEN`, and saves it in `.sandbox-session.json`. This token authenticates application calls; the Sandbox platform key creates instances, while model keys authenticate upstream model services. See [runtime configuration](runtime-environment.md) for their separate lifetimes.

Templates use different upstream configuration. Do not assume every tool consumes `ABX_LLM_*`, supports arbitrary OpenAI-compatible endpoints, or inherits a login from your machine. Non-model tools do not need a model key. Commercial account login, API-key login and optional web-service passwords are described in the applicable README.

Runtime defaults live in the Dockerfile. `run.py` forwards only its explicit `RUNTIME_ENV_NAMES` from your exported environment. Supply model keys and endpoint/model overrides before startup. Editing exports after startup does not reconfigure an already running application.

## CLI, SDK and HTTP

Download the `python-hello` directory from the same template revision and run these commands inside it. This template requires no model service. Replace the returned ID placeholder. The private token is read without printing it:

```bash
export ABX_HTTP_TIMEOUT=660
abx deploy . --yes
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command list "$ABX_SANDBOX_ID"
abx sandbox command run "$ABX_SANDBOX_ID" hello --arg name=Ada
```

Expected result: `Hello, Ada!`. Deployment prepares a reusable template; `run.py` creates the dynamic instance and starts its application, returning a Sandbox ID and private session-file path. `abx sandbox command run` calls named commands, while `abx sandbox exec` executes a process. Numeric and boolean named-command arguments use `--json-args`.

`run.py --timeout` controls instance lifetime; `--ready-timeout` controls application startup waiting. `ABX_HTTP_TIMEOUT` controls CLI request waiting. A model command's own execution deadline is separate. A client timeout does not prove the remote task stopped.

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

Use `abx sandbox download "$ABX_SANDBOX_ID" /remote/path ./local-file` or `await sb.files.read_bytes("/remote/path")` before removing the sandbox. Only delete the instance owned by your task:

```bash
abx sandbox delete "$ABX_SANDBOX_ID" --yes
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

These provider/application examples use `ProviderSandbox`. Standard `Sandbox` / `AsyncSandbox` interpreter interfaces are separate; follow the selected template and the [SDK entry-point guide](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/README.md).

This resource format requires the matching development CLI. The standalone runtime scripts use the published Python client's create, start-server and connection methods; they do not ask Python to parse or build YAML. Registry metadata is used for publication/initialization and is not required by local resource deployment. See the [resource specification](template-spec.md).
