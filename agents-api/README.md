# agents-api

One stable Gateway endpoint for Agents whose model, tools and workspace run in a
session-owned Sandbox. Business clients configure the Gateway URL and business
key once.

[中文](README.zh-CN.md) · [API reference](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.md)

This branch uses YAML v1 and needs matching development builds; published CLI0.5.10 does not support this format. Sandbox instance environment settings are under `sandbox.instance.envs`; model access belongs to `application.bindings.model`. See Configuration for their purpose and credential sources. See the [configuration specification](../docs/template-spec.md).

## What it does

Create logical sessions, upload inputs, run Codex or Qwen Code, follow durable
submissions and events, and download captured artifacts through the same Gateway.
The first input creates an exclusive Sandbox; later turns keep its native thread
and workspace. Close releases compute and retains results. Delete removes public
data while cleanup completes internally.

This is an OpenAI Agents inspired subset with explicit managed extensions. Read
`/v1/agent-sandbox/capabilities` for supported fields. A busy session rejects input
that cannot steer its current turn; use the explicit submission queue to enqueue
another turn. It does not provide the OpenAI hosted harness or promise arbitrary
OpenAI SDK compatibility.

## Stack

Alibaba generation-2 Sandbox base, non-root user, Node.js 24.16.0, Codex 0.162.1,
Qwen Code 0.23.0, PostgreSQL and FC Gateway/Worker/Dispatcher functions.

[template.yaml](template.yaml) · [Sandbox Dockerfile](Dockerfile) ·
[Server Dockerfile](server/Dockerfile)

The Guest pins published Server0.4.0a7. The Server image explicitly builds the development client at SDK commit `b988d2a76057b6202d836ec329cc0bd90a572b26`, with its archive hash fixed in the [Server Dockerfile](server/Dockerfile). Its package metadata still says a7; this is not a new PyPI release.
Application deployment requires Node.js 20 or later and the current source CLI. Business HTTP clients need only the Gateway endpoint and business key.

## Problem solved

Callers use one application endpoint instead of discovering an endpoint for each
Sandbox. Deployment credentials, database access and Sandbox management stay on
the Server. Only the selected model configuration and a separate generated guest
application token enter the Sandbox.

## Quick start (CLI)

Install the current source CLI using the linked guide; published CLI 0.5.10 does not support these commands. Configure your Sandbox/build registry with the
[usage guide](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/using-templates.md#installation), then select `deployment.access`: an existing Devs alias, `abx` for configured abx credentials, or `env` for process credentials. The default remains `default`. The FC
region, Sandbox region, database connectivity and registry image access must agree.
The CLI copies just this template into an editable project. Source acquisition
does not deploy it. Python 3 and `httpx==0.28.1` are needed on the deployment host:
after deployment, the template runs `scripts/smoke.py` against the Gateway for a
two-turn Agent file task. Keep the virtual environment active for deploy/update.
The venv command also creates `.abx/`; no separate directory setup is needed.

```bash
abx template init ./agents-api --from agents-api
cd agents-api
python3 -m venv .abx/venv
. .abx/venv/bin/activate
python -m pip install httpx==0.28.1
```

Set the referenced environment variables described in Configuration before deployment.
Choose `application.bindings.model.adapter` in template.yaml and supply its matching model ID through `OPENAI_MODEL`.
Edit the manifest's region, access profile and limits for your account. Keep
private files, plans and build receipts under `.abx/`, excluded from image builds.

```bash
abx deploy . --name agents-api --plan
abx deploy . --name agents-api --yes
abx status agents-api
```

`--plan` previews the resources without building or deploying. `--yes` authorizes
the build, cloud deployment and the template's model-backed business check.

`abx status agents-api` displays the endpoint and private local credentials file. The first deployment generates separate business and internal keys and reuses them on updates. Business clients need the endpoint and `businessKey` from that file; do not share `internalToken`. Explicit custom credentials are not copied into the local store.

```bash
abx logs agents-api
abx recover agents-api
```

`abx logs` requires FC `logConfig` to be configured; this template does not configure it by default. Without it, inspect available function diagnostics in the FC console.

After an interruption, use `recover` to inspect known resources and the next action; do not repeat creation requests. Update by running `abx deploy . --name agents-api --yes` again after editing the template or configuration. Existing Sessions keep their original revision. Close its Sessions before removing an unused revision:

```bash
abx status agents-api --revisions
abx delete agents-api --revision <old-revision> --yes
```

Authors may build separately with `abx template build . --out .abx/build.json --yes`, then reuse it through `abx deploy . --build .abx/build.json --name agents-api --yes`. `abx template publish` publishes committed source without automatically listing it in Registry.

## Quick start (Python HTTP client)

The Gateway accepts standard HTTP. There is no dedicated Gateway client SDK;
this example uses `httpx`, with no Sandbox SDK or individual Sandbox address.
Set `AGENTS_API_BASE_URL` to the returned endpoint and
`AGENTS_CREDENTIALS_FILE` to the returned private credentials file. This example
creates a session with an initial task and waits for its durable submission.

```python
import json, os, time
from pathlib import Path
import httpx

key = json.loads(Path(os.environ["AGENTS_CREDENTIALS_FILE"]).read_text())["businessKey"]
with httpx.Client(base_url=os.environ["AGENTS_API_BASE_URL"],
                  headers={"Authorization": "Bearer " + key}, timeout=30) as api:
    models = api.get("/v1/models").raise_for_status().json()["data"]
    response = api.post("/v1/agents/sessions",
        headers={"Idempotency-Key": "my-first-session"},
        json={"agent": {"model": models[0]["id"]},
              "input": "Write and run /workspace/outputs/hello.py printing hello."})
    response.raise_for_status()
    session = response.json()["id"]
    submission = response.headers["X-Agent-Sandbox-Submission-Id"]
    try:
        deadline = time.monotonic() + 660
        while time.monotonic() < deadline:
            value = api.get(f"/v1/agent-sandbox/sessions/{session}/submissions/{submission}").raise_for_status().json()
            if value["status"] in {"completed", "failed", "cancelled", "uncertain"}:
                break
            time.sleep(1)
        else:
            raise TimeoutError("Read the submission again; a client timeout does not cancel it")
        print(value["status"], value.get("turn_id"))
        # Download captured artifacts through /v1/agents/sessions/{session}/artifacts.
    finally:
        closed = api.post(f"/v1/agent-sandbox/sessions/{session}/close", json={})
        closed.raise_for_status()
        print("Cleanup operation:", closed.json()["id"])
```

Poll `/v1/agent-sandbox/operations/{id}` until close succeeds before considering
compute released. A failed or uncertain operation needs reconciliation; keep its
ID. Saved results remain available after successful close until retention expires.
For a complete upload/two-turn/download example, run `scripts/smoke.py` with
`AGENTS_API_BASE_URL` and `AGENTS_API_KEY` supplied from the same private store.

The image includes a CSV exercise with a deliberate aggregation defect and original
tests under `/workspace/agents-api-demo`. Attachments target `/workspace/input/`;
the CSV exercise uses `/workspace/input/sales.csv`. The full example asks the Agent to repair
the existing `aggregate.py`, run its original tests, and publish the summary, repair
report and modified source. The next turn adds shares to the same program. The
example downloads each turn's artifact version through the Gateway and independently
checks amounts and shares; it never executes generated code on the host. The exercise
directory does not replace your own files.

## Quick start (HTTP POST)

Read the business key from your private store into `AGENTS_API_KEY` without
printing it. Replace `model-id` with an ID returned by `/v1/models`.

```bash
curl --fail-with-body -X POST "$AGENTS_API_BASE_URL/v1/agents/sessions"   -H "Authorization: Bearer $AGENTS_API_KEY"   -H 'Content-Type: application/json' -H 'Idempotency-Key: example-session-1'   -d '{"agent":{"model":"model-id"},"input":"Create /workspace/outputs/hello.txt containing hello."}'
```

Session creation returns 201. Later input through `POST .../{session}/events`
returns 202 with an empty body and a submission receipt header. Poll that receipt
and its specific turn; an HTTP success or a disconnected stream does not prove
the Agent task completed.

## Command reference

[API reference](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.md) lists the public operations.

| Entry | Parameters | Result |
| --- | --- | --- |
| `POST /v1/agents/sessions` | `agent`, optional `input`, metadata and input-file extension | Logical Session; initial input also returns a receipt header. |
| `POST /v1/agents/sessions/{id}/events` | Supported input or cancellation events | 202; durable receipt in headers. |
| `POST /v1/agent-sandbox/sessions/{id}/submissions` | Input; required `Idempotency-Key` | Explicit queued Submission. |
| `POST /v1/agent-sandbox/sessions/{id}/close` | Empty object | Cleanup Operation; retains committed results. |
| `DELETE /v1/agents/sessions/{id}` | Closed or idle Session ID | Public deletion; executing/collecting sessions return 409. |

The private bridge is not the business API. `commands.py` contains a local
`agents_version()` diagnostic with no arguments; it checks installed CLI versions
and returns their pinned versions. It is not exposed by the private bridge.

The manifest omits fixed `fc-managed-agents` profile fields. Customize the declared
provider, bindings, region and budgets; see the [profile reference](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agent-applications.md)
for defaults and supported overrides.

## Configuration

Edit [template.yaml](template.yaml) only. Native Serverless Devs expressions `${env('NAME')}` read local configuration; supply the following in an untracked project `.env` or process environment. No bindings JSON is required. registry.yaml only supplies publication/initialization metadata.

| Variable / field | Purpose and source |
| --- | --- |
| ABX_MANAGED_DATABASE_URL | Existing PostgreSQL URL from your database provider, reachable by all three FC roles. Database provisioning/deletion is separate. |
| SANDBOX_API_KEY | Existing Sandbox platform key from its account setup; used for instance lifecycle. |
| SANDBOX_BASE_URL / SANDBOX_DOMAIN / SANDBOX_REGION | The matching Sandbox platform's API address, instance endpoint domain and region. |
| OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL | Model-provider key, compatible API base and exact authorized model ID. qwen-code needs tool-capable Chat Completions; codex needs tool-capable Responses. |
| AGENTS_FC_ROLE_ARN | Existing RAM execution role ARN allowed to invoke private Worker/Dispatcher functions, from RAM/FC setup. |
| application.bindings.model.adapter | Set qwen-code or codex in template.yaml to match the model service. |
| deployment.access / deployment.vars.region | Keep the native `default` access alias, select another existing Devs alias, use `abx` to reuse configured abx cloud credentials, or `env` for process cloud credentials. Set the FC region under `deployment.vars.region`. Deployment, model and Sandbox credentials are separate. |
| application.bindings.clientAuth / internalAuth | CLI defaults generate distinct business/internal keys and securely reuse them locally. Business clients receive only business credentials. |

For an existing private-network database, configure its supplied network IDs under application.state:

```yaml
application:
  state:
    databaseUrl: ${env('ABX_MANAGED_DATABASE_URL')}
    databaseCa: ${env('AGENTS_DATABASE_CA_PEM')}
    vpcConfig:
      vpcId: ${env('AGENTS_VPC_ID')}
      vSwitchIds: ["${env('AGENTS_VSWITCH_ID')}"]
      securityGroupId: ${env('AGENTS_SECURITY_GROUP_ID')}
```

Add databaseCa only for a private database CA. Supply certificate PEM from your database provider, never a private key. Keep sslmode=verify-full and the certificate's database hostname. This version does not add another {env: ...} or {file: ...} syntax.

The three FC roles borrow the supplied network. This creates no VPC, switch, security group, route or NAT. Verify actual database, registry, Sandbox API and model connectivity. For production, use an existing HTTPS domain with an exclusive `/*` route to this same Gateway; the Managed path updates its revision qualifier. It does not create domains, DNS or VPC resources. This Managed deployment accepts only the three role resources; extra native resources fail before deployment. See the [resource specification](../docs/template-spec.md).

ABX_SERVER_TOKEN is the independent application token generated per Sandbox by the runtime; there is no cloud-console key or manual setup step for it.

## Resources

The Sandbox requests 2 vCPU and 4096 MB. Default session idle/max lifetime is
900/3600 seconds; one turn per session executes at a time. Turn/tool budgets are
600/60 seconds. File and artifact limits are 10 MiB each and retained owner storage
is 100 MiB; check the manifest for all admission limits.

FC, registry storage, Sandbox runtime, database and model usage can incur charges.
The built-in FC function URL is a test entry and has provider limitations; it is
not a production SLA. Same-UID Agent tools can read their injected model key and
modify their workspace. Captured Agent output is not an independent execution
attestation. Restart or uncertain delivery freezes work for reconciliation rather
than silently replaying a tool action.

Close individual sessions when finished, download needed results and delete
public session/file data. To remove this deployment:

```bash
abx delete agents-api --yes
```

Inspect the result and use `abx recover agents-api` if an operation was interrupted
or its result is uncertain. Delete removes the deployment's recorded owned
resources. A reusable artifact supplied with `--build`, a supplied `application.server.image`,
and existing databases, networks, model services and custom domains remain yours
to manage.

When a standalone build is no longer used by any deployment, clean its confirmed
owned Server image with `abx template build --clean .abx/build.json --yes`.
Sandbox image builds may remain in `retained_build_artifacts`; remove only your
unused image tags using the registry's cleanup instructions. Deleting a deployment
does not erase separately retained database history.

## Contributing

Follow [CONTRIBUTING.md](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/CONTRIBUTING.md) and the
[template specification](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/template-spec.md). Keep both languages aligned.

## Issues

Report recipes/spec issues to [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues),
Gateway/bridge/runtime issues to [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues),
and deployment command issues to [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).
Remove keys, database URLs and private logs from reports.

## License

Apache-2.0; see [LICENSE](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/LICENSE). Upstream CLIs retain their own licenses.
