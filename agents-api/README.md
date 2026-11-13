# agents-api

One stable Gateway endpoint for Agents whose model, tools and workspace run in a
session-owned Sandbox. Business clients configure the Gateway URL and business
key once.

[中文](README.zh-CN.md) · [API reference](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.md)

This recipe uses YAML v1 and requires a matching development CLI. Configure resources in `template.yaml`; `registry.yaml` is only used for catalog metadata and initialization forms. See the [configuration specification](../docs/template-spec.md).

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

Use the matching source CLI and configure Sandbox/build credentials with the [usage guide](../docs/using-templates.md). The deployment host needs Python 3, Docker and cloud credentials authorized for FC. Keep the project virtual environment active for deploy and maintenance.

```bash
abx template init ./agents-api --from agents-api
cd agents-api
python3 -m venv .abx/venv
. .abx/venv/bin/activate
python -m pip install -r scripts/requirements.txt
```

Supply the variables in Configuration through a private `.env` or process environment. Set `vars.adapter` and `vars.region` in `template.yaml`. Use an immutable, unique tag in `AGENTS_SERVER_IMAGE` for every Server build. To change the application name, change both `name` and `vars.applicationName` before its first deployment.

```bash
abx deploy . --plan
abx deploy . --yes
python scripts/release.py status
```

The plan does not build or run actions. Deployment prepares the Sandbox template, builds the Server image and creates separate Worker, Dispatcher and Gateway functions. It runs a model-backed two-turn file task before switching the stable `prod` Gateway alias. It does not create a permanent Sandbox instance.

First deployment generates distinct business and internal tokens and reuses them on updates. The private `.abx/agents-api/credentials.json` contains `businessKey` and `internalToken`; share only the business key. The endpoint is in `.abx/agents-api/release.json` under `endpoint`. Explicit process credentials are not copied to the credential store. Keep `.env` and `.abx/` private and retain them for updates and cleanup.

Run the same deploy command after editing the template and selecting a new Server image tag. Existing Sessions retain their original Worker revision; the new Dispatcher knows the retained Workers. Old revisions stay allocated until application removal. Internal-token rotation is rejected while revisions share the application; it needs a separate coordinated migration. Configure native FC `logConfig` in each role's `props` to enable log delivery.

A failed or interrupted publication can leave a candidate or an uncertain alias update. Inspect the saved phase and `python scripts/release.py status`; do not delete the record or repeat publication. The new Dispatcher takes over old and new revision routing before the candidate task; it continues serving old Sessions if that task fails. Automatic rollback and resume of uncertain publication are not provided by this recipe. Preserve old resources until the outcome is confirmed.

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

Customize the three native FC `props` objects and the Sandbox template independently. Session and task budgets belong to this recipe's `vars.policy`; they are checked by its deployment script.

## Configuration

Edit [template.yaml](template.yaml) for resource values. Its `${env('NAME')}` expressions read a private project `.env` or process environment; process values take precedence. `vars` keys are author-defined. The keys below are this recipe's choices, not reserved specification names.

| Variable / field | Purpose and source |
| --- | --- |
| `AGENTS_SERVER_IMAGE` | Your writable OCI repository and unique Server image tag, used by native FC build and all three Server roles. |
| `ABX_MANAGED_DATABASE_URL` | Existing PostgreSQL URL from the database provider, reachable by all three roles. Database creation/deletion is separate. |
| `SANDBOX_API_KEY` | Sandbox platform key from account setup, used by Worker/Dispatcher for instance lifecycle. |
| `SANDBOX_BASE_URL` / `SANDBOX_DOMAIN` / `SANDBOX_REGION` | Matching platform API, instance endpoint domain and region. |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | Model-provider key, HTTPS API base and authorized model ID. Only Worker receives the model key. qwen-code needs tool-capable Chat Completions; codex needs tool-capable Responses. |
| `AGENTS_FC_ROLE_ARN` | Existing RAM role ARN for FC execution, including permission to invoke private Worker functions. |
| `AGENTS_DATABASE_CA_PEM` | Optional database-provider CA certificate PEM, not a private key. Retain `sslmode=verify-full` and a matching hostname in the database URL. |
| `vars.adapter` / `vars.region` | Choose qwen-code or codex and the resource region. Region stays under each `sandbox.<name>.template` / native FC `props`; these expressions merely reuse a value. |
| `vars.policy` | Positive session, task and storage budgets. Its `instance.timeout` must equal the Session lifetime. |
| `AGENTS_BUSINESS_KEY` / `AGENTS_INTERNAL_TOKEN` | Optional overrides of generated application credentials; each needs at least 32 characters and they must differ. These are not cloud API keys. |

For a private-network database, put its existing network IDs into `serving.worker.props.vpcConfig`, `serving.dispatcher.props.vpcConfig` and `serving.gateway.props.vpcConfig`:

```yaml
vpcConfig:
  vpcId: "${env('AGENTS_VPC_ID')}"
  vSwitchIds: ["${env('AGENTS_VSWITCH_ID')}"]
  securityGroupId: "${env('AGENTS_SECURITY_GROUP_ID')}"
```

Verify database, registry, Sandbox API and model connectivity from those networks. The recipe creates no VPC, route, NAT, database or custom domain. Its stable entry uses the FC test URL; an existing custom domain must be configured separately to target the Gateway `prod` alias.

The Guest Dockerfile sets `ABX_MANAGED_WORKSPACE=/workspace` and `ABX_MANAGED_STATE_DIR=/home/user/.agent-sandbox/managed-bridge`. They control the per-Session workspace and bridge state inside the Sandbox; edit the image to change them, keeping the managed workspace contract aligned. The Worker creates each dynamic instance with its private token and model environment, then explicitly starts the managed bridge. The template does not start that authenticated process during snapshot preparation. Instance lifetime also belongs to the Worker. `ABX_SERVER_TOKEN` is a separate application token generated for each Sandbox by the runtime; no manual cloud-console key is needed.

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

Close individual Sessions, download needed results and delete unneeded public data. Remove the application with its drain-aware helper:

```bash
python scripts/release.py destroy
```

The helper stops admission and requests Session cleanup. If active Sessions, pending cleanup or uncertain resources remain, it keeps the FC resources and reports that drain is incomplete; resolve the remaining work and rerun. Every removal rechecks the Dispatcher and database identities. If an earlier partial deletion removed the Dispatcher, confirm cleanup separately before continuing resource removal. After confirmed drain it calls `abx delete agents-api --yes`, which removes recorded owned resources, including retained function revisions. Do not bypass drain while Sessions are active.

Existing databases, networks, execution roles, custom domains and supplied image tags remain yours to manage. Remove unused image tags through your registry. Application removal does not erase separately retained database history. Keep private deployment records until resource removal is confirmed.

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
