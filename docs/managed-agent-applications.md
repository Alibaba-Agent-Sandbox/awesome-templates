# Managed Agent applications

[中文](managed-agent-applications.zh-CN.md)

The [Agents API template](../agents-api/README.md) provides one stable Gateway with an exclusive Sandbox per active Session. The model, CLI and tool loop execute inside that Sandbox. This branch uses YAML v1 and matching development consumers; published CLI0.5.10 does not accept it.

## Runtime and lifecycle

Set `application.type: agents-api` and reference three distinct native FC resources with `application.roles.gateway`, `worker` and `dispatcher`. The coordinator supplies private bridge startup, readiness and service declarations; authors do not repeat protocol/version/operations constants.

The first input allocates compute; later turns keep the native thread and workspace. `sandbox.instance.timeout` is the sole maximum lifetime, default3600 seconds for Managed applications. `application.sessions.idleTimeoutSeconds` defaults900 and must fit inside it. Turn/tool budgets default600/60 seconds and must fit the instance lifetime. Logical Sessions, active Sandboxes, queue and retained storage have separate limits in the [complete field table](template-fields.md).

Close releases compute and retains committed results; delete removes public Session data while cleanup finishes. Uncertain submissions or remote deletion require reconciliation. Queueing a new turn is not steering an active one. The runtime exposes its OpenAI-inspired subset and explicit extensions through capabilities; it does not implement OpenAI's hosted harness.

## Configuration and bindings

Everything needed to configure resources is in [template.yaml](../agents-api/template.yaml). Use native `${env('NAME')}` references to local untracked `.env` or process values. Credentials, a second bindings JSON and Registry initialization questions are not separate resource files.

| Path | Value and source |
| --- | --- |
| application.state.databaseUrl | Existing PostgreSQL URL from its service owner. |
| application.state.vpcConfig | Optional existing vpcId, distinct vSwitchIds and securityGroupId; borrowed, not provisioned. |
| application.state.databaseCa | Optional private CA certificate PEM through a native expression; retain database hostname verification. |
| application.bindings.sandboxAccess | Existing platform apiKey/baseUrl/domain/region. Server-only lifecycle access. |
| application.bindings.model | Model apiKey/baseUrl/model and codex or qwen-code adapter; Worker supplies model credentials to the Session's Sandbox. |
| application.bindings.clientAuth | Default generate:true creates separate locally retained business credentials. Explicit supported hashes/owner/scopes are optional. |
| application.bindings.internalAuth | Separate generated private identity; execution authority comes from the matching native role properties. |
| application.bindings.ingress | Supported alias/domain route for the Gateway; not a Sandbox custom domain. |

The CLI generates each guest application token automatically; it is separate from platform, cloud and model credentials. Additional Sandbox instance env/metadata/volumes are subject to Managed ownership restrictions: system/model/auth variables and managed metadata cannot be overridden; mounted volumes cannot shadow the managed workspace or state. Pause/resume policies are not supported by this coordinator. Only the Worker receives private custom instance env values.

Same-UID Agent tools can read the model credentials deliberately supplied to their Sandbox. Server database, cloud management and business/internal authentication are not guest environment settings. Plans must not reveal resolved credentials or native environment values.

## Server build and deployment

The Server recipe pins the development client source at SDK commit `1079841307f1f63253ae68fdda6e6d2d1e77e851`; the Guest retains published Server0.4.0a7. Source package metadata still says a7, so the version alone cannot identify the v1 runtime.

`deployment` is the original Serverless Devs edition3 project. Keep real `component: fc3@<version>` identifiers and native `props`: cpu, memorySize, timeout, role, logConfig and vpcConfig retain native names and units. The three Managed role resources use one pinned FC component version and region, with the same execution role authority. User-selected native memory4096 is not normalized back to a coordinator constant.

`application.server` chooses exactly one source recipe `{source: {dockerfile, context}}` or digest-pinned image. It supplies the coordinator's actual Server image input. The coordinator owns generated function names, revision descriptions, container entrypoints and private control settings. Native domain resources and their output dependencies remain in the original project.

Build, deployment, configuration resolution, durable state, revision routing and resource cleanup remain explicit runtime operations. Static intent validation does not evaluate Devs variables or prove cloud deployability. Generic independent Sandbox plus Serving intent is valid, but unsupported combined execution fails before side effects rather than selecting this coordinator implicitly.

## Hooks and outputs

Optional beforeApply/afterReady hooks use bounded custom argv/cwd/timeout/envAllowlist or a Serverless Devs role info check. They do not run during source initialization or ordinary Sandbox launch. The [template](../agents-api/template.yaml) includes an afterReady two-turn business check; it requires the documented model service and can incur charges.

The coordinator publishes a stable endpoint and safely retained client credentials. Existing Sessions retain their original revision during an update. Close Sessions before deleting an unused old revision; borrowed databases, networks, domains and externally supplied image artifacts remain the owner's responsibility.

## Client and resource use

Clients use HTTP, not the private bridge or individual Sandbox endpoints. See the [API reference](managed-agents-api.md) and template's complete Python HTTP/URL examples. A dedicated Gateway SDK is not supplied. Check capabilities for supported operations rather than inferring full interoperability from path names.
