# Managed Agent applications

Specification 6 describes an application with one stable public Gateway and one
exclusive Sandbox per session. The Agent's model/tool loop and CLI run inside the
Sandbox. Business callers use the Gateway URL and business credentials; Sandbox
addresses and management credentials remain internal.

The closed contract is [template-v6.schema.json](../spec/template-v6.schema.json).
Version 5 retains its original lifecycle and deployment semantics. Application
deployment is explicit; importing, building or creating a Sandbox never deploys
Server resources or executes host hooks.

## Runtime and lifecycle

The supported combination is:

```yaml
runtime:
  placement: in-sandbox
  driver: sandbox-local-api
  profile: managed-bridge-v1
gateway:
  placement: fc-web
sandbox:
  provider: alicloud-express
  lifetime: per-session
  workspace: exclusive
  requiredFeatures: [sandbox.lifecycle, ports.url]
```

The private bridge protocol differs from `server-core-agents`. It starts with
`python -m agent_sandbox.server.managed --port 9000`, protects capabilities and
managed operations with a generated application token, and permits the read-only
`/health` readiness probe. Root `provides.app` declares
`protocol: agent-sandbox-managed-bridge`, `version: 1`, and port 9000.

Root smoke declarations use a bridge operation and expectation, for example:

```yaml
smoke:
  - operation: health
    expect: {status: ok, protocol: agent-sandbox-managed-bridge/v1}
```

The first input allocates compute. Later turns retain the same native thread and
workspace. A session has one executing or collecting turn at a time. Empty logical
sessions, live/uncertain Sandboxes, queue length and retained storage have independent
limits. Status/event reads do not extend idle time. New work must fit inside the
Sandbox's remaining maximum lifetime and collection/cleanup allowance.

Close stops accepting work and releases compute while retaining committed results
for their retention period. Delete removes public session data and preserves only
the internal records needed to finish cleanup. An uncertain submission, restart or
resource deletion is not automatically replayed or treated as confirmed absence.

## Configuration and bindings

`application.api.protocol` is `agent-sandbox-managed-agents/v1`. The supported
OpenAI-inspired subset and explicit managed extensions are discoverable from the
Gateway. Unsupported steering, tools and settings fail explicitly; a queued new
turn is not silently described as steering the active turn.

Bindings store references, never secret values or connection URLs. Each binding
declares its permitted role targets:

| Binding | Targets | Purpose and source |
| --- | --- | --- |
| State (`state.bindingRef`) | gateway, worker, dispatcher | Existing PostgreSQL service reference resolved by the deployment environment. |
| `sandboxAccess` | worker, dispatcher | Existing Sandbox access configuration for lifecycle and reconciliation. |
| `model` | sandbox-creation | Permitted model key/base/model reference, resolved only by the Worker for guest injection. |
| `clientAuth` | gateway | Business authentication configuration; generated tokens are delivered securely to callers. |
| `internalAuth` | gateway, worker, dispatcher | Independent private control identity/signing configuration. |
| Ingress (`deployment.ingressBindingRef`) | deployment-publisher | Owned or borrowed stable route/alias/domain configuration. |

`model` requires `resolverRole: worker` and an explicit `allowedEnv` subset of
`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `CODEX_API_KEY`. No cloud,
database or business-auth configuration is copied to the Sandbox. The application
token is generated per session; it is not a cloud-console API key.

The deployment resolver validates the binding's actual value type and ownership.
Missing required values prevent publication. The resolved State binding accepts
a PostgreSQL URL string or `{databaseUrl, vpcConfig?, databaseCa?}`. Optional `vpcConfig` has
exactly `vpcId`, distinct `vSwitchIds` and `securityGroupId` for the three FC roles;
it is deployment networking, never a guest environment value. It borrows existing
network resources and does not create NAT/routing or prove endpoint reachability.
Optional `databaseCa` accepts a bounded certificate-only PEM string, environment
reference, or CLI-host file reference; preserve database hostname verification.
It configures Server trust only and is not an image/plan/receipt/guest input.
The CLI pins the database's durable identity internally; users do not supply it.
Same-UID Agent tools can access model
credentials intentionally provided to that Sandbox; they do not receive Server
control credentials.

## Server build and deployment

`application.deployment` selects `profile: fc-managed-agents`, an exact published
`fc3@X.Y.Z` component, the deployment `accessRef`, region, ingress reference and
`revisionStrategy: immutable-workers-with-drain`.

Choose exactly one Server artifact input:

```yaml
serverBuildRecipe:
  dockerfile: server/Dockerfile
  context: .
```

or `serverImage` with an immutable `@sha256:<64 lowercase hex>` digest. Build
inputs remain within the template context. The CLI builds and resolves the image
before freezing its plan and generated toolchain/integrity lock. Arbitrary
`deployment.steps` and a second workflow DSL are not accepted by this profile.

The profile prepares the Sandbox Template, creates revision-owned Workers,
deploys a candidate Gateway/Dispatcher, verifies it, then publishes the stable
ingress. Verification uses bounded private dispatch while production timers are
disabled. Public endpoint output comes from verified ingress, not a guessed
component field. Function-alias and custom-domain bindings have distinct Provider
requirements; a test function URL is not a production domain guarantee.

Session revisions remain fixed during updates. Old Workers and compatible Server
artifacts are retained until sessions drain. Cleanup failures retain ownership
records and an operational cleanup path; borrowed databases and model services
are not deleted. Unused, confirmed owned Server builds can be cleaned with
`abx app clean-build BUILD --yes`. Once a build participates in Apply it belongs
to app Destroy/Retire, which delete owned image tags only after references drain;
borrowed Server images are preserved. Sandbox image builds may remain under
`retained_build_artifacts` for explicit registry cleanup.

## Hooks and outputs

`beforeApply` and `afterReady` each contain at most eight hooks with globally unique
IDs. `custom` declares argv, safe relative cwd, a 1–900 second timeout and explicit
environment allowlist. `serverless-devs` refers to `gateway`, `worker` or
`dispatcher` and supports only bounded `command: info` queries. Deployment and
destruction belong to managed steps, not an unrecorded hook side effect.

Outputs are the verified `publish.outputs.endpoint` and protocol
`agent-sandbox-managed-agents/v1`. Health, syntax validity, URL resolution and a
successful hook are separate from a completed business task.

## Client and resource use

Upload inputs to the Gateway before referencing their opaque file IDs. Installation
into the workspace occurs at a turn boundary, under the session's execution
ownership. Published artifacts are immutable captured bytes with turn/path/digest
identity; deleting a published copy does not delete the live workspace file.

Use a saved idempotency key when retrying supported creation/submission calls.
Stream reconnection retrieves committed events; it does not cancel or restart an
Agent. Read the specific turn and its saved items to determine the outcome. Close
the session to release compute, download retained outputs before expiry, and
delete public data when no longer needed.

User instructions belong in the template README. Implementation/review evidence
and exact tested versions remain in the repository's engineering records.
