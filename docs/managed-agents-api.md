# Managed Agents API reference

Clients use the stable Gateway URL and `Authorization: Bearer <businessKey>`.
Resources are scoped to the authenticated owner. Missing or unsupported settings
fail explicitly; inspect `GET /v1/agent-sandbox/capabilities` and the deployment's
model allowlist before submitting work. This protocol is
`agent-sandbox-managed-agents/v1`, an OpenAI Agents inspired subset with project
extensions; it does not promise arbitrary OpenAI SDK interoperability.

Use a runtime release that advertises this protocol. Published SDK 0.4.0a6 does not provide the managed API. The deployed capability response is authoritative for supported adapter features.


## Operations

The public surface has the following operations. Health is a readiness probe,
not proof that a model task succeeds.

| Method | Path | Success |
| --- | --- | --- |
| `GET` | `/healthz` | 200 |
| `GET` | `/v1/agent-sandbox/capabilities` | 200 |
| `GET` | `/v1/models` | 200 |
| `GET` | `/v1/models/{model_id}` | 200 |
| `GET` | `/v1/agents/runtimes` | 200 |
| `POST` | `/v1/agents` | 201 |
| `GET` | `/v1/agents` | 200 |
| `GET` | `/v1/agents/{agent_id}` | 200 |
| `POST` | `/v1/agents/{agent_id}` | 200 |
| `DELETE` | `/v1/agents/{agent_id}` | 200 |
| `POST` | `/v1/agents/sessions` | 201 |
| `GET` | `/v1/agents/sessions` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}` | 200 |
| `POST` | `/v1/agents/sessions/{session_id}` | 200 |
| `DELETE` | `/v1/agents/sessions/{session_id}` | 200 |
| `POST` | `/v1/agents/sessions/{session_id}/events` | 202 |
| `GET` | `/v1/agents/sessions/{session_id}/events` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/items` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns/{turn_id}` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/turns/{turn_id}/items` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}` | 200 |
| `GET` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}/content` | 200 |
| `DELETE` | `/v1/agents/sessions/{session_id}/artifacts/{artifact_id}` | 200 |
| `POST` | `/v1/files` | 200 |
| `GET` | `/v1/files` | 200 |
| `GET` | `/v1/files/{file_id}` | 200 |
| `GET` | `/v1/files/{file_id}/content` | 200 |
| `DELETE` | `/v1/files/{file_id}` | 200 |
| `GET` | `/v1/agents/environments` | 200 |
| `GET` | `/v1/agents/environments/{environment_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/close` | 202 |
| `GET` | `/v1/agent-sandbox/operations/{operation_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/submissions` | 202 |
| `GET` | `/v1/agent-sandbox/sessions/{session_id}/submissions` | 200 |
| `GET` | `/v1/agent-sandbox/sessions/{session_id}/submissions/{submission_id}` | 200 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/turns/{turn_id}/cancel` | 202 |
| `POST` | `/v1/agent-sandbox/sessions/{session_id}/submissions/{submission_id}/cancel` | 202 |

## Sessions, input and receipts

Create a logical Session with an inline `agent` or saved Agent configuration and
optional initial `input`. Configuration is frozen for that Session; changing a
saved Agent affects newly created Sessions. Session updates support metadata
only. Arbitrary remote tools, MCP endpoints and workspace/environment creation
are unsupported in this profile. Environments are read-only session projections.

Use a stable `Idempotency-Key` for Session creation and input retries. Session
creation returns 201; an initial input also supplies
`X-Agent-Sandbox-Submission-Id`. `POST .../events` accepts supported input/cancel
events and returns 202 with an empty body, a receipt header and a `Location`.
Query the managed Submission to recover acceptance and its fixed Turn ID. The
explicit enqueue endpoint requires `Idempotency-Key` and returns a Submission.
A lost response or expired lease never proves an execution is safe to replay.

While a turn executes or collects artifacts, unsupported steering returns
409 `active_turn_not_steerable`. Enqueue is a separate new turn, not steering.
Cancellation targets a specific Submission or Turn and returns an Operation.
An accepted cancellation is not confirmation that compute stopped. Keep querying
the Operation; uncertain results require reconciliation.

## Files and artifacts

`POST /v1/files` accepts multipart form data: `purpose=user_data` and a binary
`file`. Reference the resulting opaque ID in a Session's initial input or a later
input request:

```json
{"input":"Read the CSV and write /workspace/outputs/summary.csv",
 "x_agent_sandbox":{"input_files":[
   {"file_id":"file-id","path":"/workspace/input/sales.csv"}]}}
```

Inputs are installed only at the next turn boundary, under `/workspace/input/`.
A file upload alone does not write a live workspace. Artifact metadata/content
are immutable captured bytes from `/workspace/outputs/`, associated with Turn,
path and digest. Deleting a published artifact does not delete the live file.
Deleting a public input removes its public visibility while frozen submissions
can retain internal references until safe reclamation. Configured byte limits
apply separately to files, artifacts, a turn and retained owner storage.

## Pagination, events and cleanup

List routes use opaque cursors with `limit`, `order`, `after` or `before` as
supported by the capability contract. Keep the returned `last_id` when
`has_more` is true. Never derive cursor values from database positions.

GET Session events streams durable SSE events. Reconnect with the last event ID;
replay does not rerun the Agent. Respect explicit event-gap/cursor-expiry errors
and read saved Turn/items for durable outcome. Disconnect and client timeout do
not cancel a turn. Slow subscribers and maximum subscribers are bounded.

Close rejects new work, releases compute and retains committed history/artifacts.
Poll the returned Operation for `succeeded`; `failed` or `requires_reconcile` needs
operator action. Delete returns 200 after removing the public resource; it returns
409 while executing/collecting. Internal ownership records may remain until
cleanup is confirmed. Retention expiry removes access independently of compute.

[Template usage](../agents-api/README.md) ·
[Application manifest reference](managed-agent-applications.md)
