# agents-api

## Purpose

Provide one stable business endpoint for session-owned Sandbox Agents, with
Server-managed admission, durable receipts, files, events and cleanup. This new
managed application is separate from the local `agents-cli` template. See
[Issue295](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/295).

## Capabilities

The Gateway exposes the [managed API](../managed-agents-api.md). Each session
owns one native thread/workspace; first input allocates compute. PostgreSQL is
host-authoritative for acceptance/ownership, not independent proof of Agent
execution. Same-UID guest records do not establish hostile-code attestation.

## Deployment architecture

The [user-facing architecture and resource map](../../agents-api/README.md#architecture-and-cloud-services)
describes the current cloud prerequisites. Gateway, Dispatcher and Worker run as
three FC functions sharing the Server image. Gateway accepts business requests
and persists them to PostgreSQL. The FC timer invokes Dispatcher, which reads due
work and invokes the revision-bound Worker through FC asynchronous tasks. Worker
creates or reuses the session-owned Sandbox, drives the private bridge, and
captures events and artifacts. The native Agent calls the model from the Sandbox.
PostgreSQL stores queue state and bounded file/artifact bytes as well as sessions.
The deployer supplies the database, model access, ACR namespace and RAM role;
private network and custom-domain resources are conditional existing inputs.

## Exposed API

Business calls use Gateway authentication; no guest endpoint is returned. The
private bridge has health, capabilities, nonce-stable session creation, durable
submission receipts and targeted cancellation. It exposes no generic shell/files
or named command HTTP routes. `agents_version() -> str` in commands.py has no
parameters and executes fixed bounded `codex --version` and `qwen --version` argv
for local installation diagnostics only; it is not an acceptance substitute.

## How to build

The [guest recipe](../../agents-api/Dockerfile) preserves Alibaba generation2 and
non-root user, pins Node24.16.0 and exact Codex0.162.1/Qwen0.23.0 packages. The
[thin Server recipe](../../agents-api/server/Dockerfile) runs the shared runtime's
module entrypoint; it copies no duplicate Server implementation. The public recipes pin client/server 0.4.0a7 and the deployment guide uses CLI
0.5.10. Source artifact testing remains separate from published-package and
cloud acceptance.

Spec6 uses exact managed module start and the existing healthcheck ready command.
The app profile builds/resolves immutable images before freezing plans, prepares
unique revision-owned SandboxTemplate/image refs and retains them while referenced
by current or draining revisions. fc3@0.1.26 is a real fixed component; generated
locks cover its actual loaded dependency graph. No general second steps DSL.

## Express feasibility

Feasible: slice

Limiting factor: hosted compatibility is explicitly bounded by the managed API.

The guest requires normal unprivileged processes and model egress, not Docker or
KVM. FC Server, reachable existing PostgreSQL, execution roles and image access
are separate prerequisites. Function-alias test domains are not a production SLA.

## Risks

Model configuration enters only the owned guest. Cloud/database/business secrets
stay on the Server; guest token is separately generated. Unknown delivery/restart
freezes execution instead of replaying tool effects. Cancel/timeout does not prove
child processes stopped; uncertain stop requires provider-level destruction and
confirmation. Event gaps, byte limits, borrowed resources and retained revisions
must remain explicit. Host hooks are bounded trusted deployment actions.

## Test plan

L0 uses the actual manifest-selected private bridge with a temporary workspace,
state and random token; test health, token enforcement, capabilities and closed
route families. Version diagnostic is not the model or bridge test. Spec tests
prove old5 unchanged and reject6 privilege/path/profile/budget false claims.

L1 builds both original recipes using exact published dependencies and checks real
non-root execution/pinned CLIs. Source-built wheels are a distinct provenance gate.
L2 requires complete app deployment/build/plan/apply/status/update/retirement/
reconcile/destroy and independent owned cleanup, not legacy sandbox named smoke.
L3 requires real compatible model input upload, two-turn native continuation,
executed tools, independently calculated/downloaded CSV artifacts, SSE/replay,
cancel/isolation/restart/delivery/limits checks, and close retaining artifacts.
The image includes an explicitly named CSV exercise with a real source bug, original
tests and decimal/quoted/Unicode input. The Gateway-only afterReady script repairs
the existing source in turn one, publishes source/summary/report, then adds shares in
turn two while retaining the first artifact version. It checks downloaded CSV results
without executing generated code on the host. An optional trusted in-process inspector
runs only after publication and before continuation/close; an engineering controller
can use owned Provider APIs to verify source/test hashes and run original/held-out
assertions inside that same Sandbox. No public exec route or extra cloud credential is
added to the business hook. That independent execution is separate from the default
Gateway-only assertion and must have its own evidence.

The Gateway-only afterReady script covers a bounded business path; the full shared
runtime/CLI acceptance matrices remain separately required. L4 requires each actual
additional-provider run; no additional provider is declared for this profile.

Actual results and blocked release/cloud gates belong in dated engineering evidence.

The local business smoke persists bounded label-only progress beneath its own
`.abx/agents-smoke-reports` directory before its first HTTP call. Per-attempt
JSONL and atomic latest snapshots survive the deployer's temporary-hook cleanup.
The local report never retains hook context identities, credentials, URLs,
model text or raw exceptions; an incomplete/running report cannot grant success.
This does not change the deployment hook result or Gateway protocol.


## Manifest profile defaults

The manifest selects `fc-managed-agents` explicitly. Fixed runtime, API, lifecycle
and binding-role fields come from the shared application-profile contract; the
normalizer preserves explicit values for strict schema and semantic validation.
Provider, binding references, images, region and configurable budgets remain
visible author inputs. This changes the manifest consumer requirement, not the
runtime or deployment topology. Existing execution evidence remains historical.
