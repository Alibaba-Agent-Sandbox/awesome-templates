# YAML v1 field reference

Fields are grouped by their YAML path. Required means required when that object or branch is used. Defaults come from the shared normalizer; a dash means no default is declared.

[Usage and units](template-spec.md) · [Managed semantics](managed-agent-applications.md) · [Machine schema](../spec/template-v1.schema.json)

This is the integrated high-level input subset. Native Devs/FC object fields belong to the selected component; this table neither duplicates its schema nor claims unintegrated Provider APIs.

<a id="template"></a>

## template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `specVersion` | integer | yes | — | = `1` | Public resource format version. |
| `name` | string | yes | — | ASCII kebab-case, 1–63 characters | Resource name. |
| `sandbox` | object · [fields](#field-sandbox) | no | — | — | Sandbox template and instance settings. |
| `deployment` | object · [fields](#field-deployment) | no | — | — | Native Serverless Devs project. |
| `application` | object · [fields](#field-application) | no | — | — | Select the Agents API coordinator. |

- Other fields are rejected.
- At least one: `sandbox`; `deployment`.
- `application` requires `sandbox`, `deployment`.

<a id="field-sandbox"></a>

## sandbox

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `provider` | string | no | CLI/context; agents-api: alicloud-express | complete ASCII identifier | Provider selected before execution. |
| `template` | object · [fields](#field-sandbox-template) | yes | — | — | Environment source, image or existing reference. |
| `instance` | object · [fields](#field-sandbox-instance) | no | — | — | Instance creation settings, separate from preparation. |
| `start` | string | no | — | length ≥ 1 | One workload startup command. |
| `ready` | string | no | — | length ≥ 1 | Workload readiness command. |
| `services` | object · [fields](#field-sandbox-services) | no | — | — | Named business service contracts. |
| `ports` | array of integer | no | — | unique items; each: ≥ 1; ≤ 65535 | Additional access ports; no listener or protocol promise. |

- Other fields are rejected.
- [When provider=alicloud-express](#field-sandbox-allof-0-then)
- [When provider=opensandbox](#field-sandbox-allof-1-then)
- [When provider=e2b](#field-sandbox-allof-2-then)
- [When provider=cubesandbox](#field-sandbox-allof-3-then)
- [When provider=alicloud-container](#field-sandbox-allof-4-then)

<a id="field-sandbox-template"></a>

## sandbox.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `source` | [source](#type-source) | no | — | — | Contained source build recipe. |
| `image` | string | no | — | length ≥ 1 | Container image input. |
| `reference` | string | no | — | length ≥ 1 | Existing Provider-native template ID; never translated across Providers. |
| `aliases` | array of string | no | — | unique items; each: length ≥ 1 | Template lookup names. |
| `props` | object · [fields](#field-sandbox-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |

- Other fields are rejected.
- Choose exactly one: `source`; `image`; `reference`.

<a id="field-sandbox-template-props"></a>

## sandbox.template.props

Preparation fields depend on the selected Provider:

- [provider=alicloud-express](#field-sandbox-allof-0-then-template-props)
- [provider=opensandbox](#field-sandbox-allof-1-then-template-props)
- [provider=e2b](#field-sandbox-allof-2-then-template-props)
- [provider=cubesandbox](#field-sandbox-allof-3-then-template-props)
- [provider=alicloud-container](#field-sandbox-allof-4-then-template-props)


<a id="field-sandbox-instance"></a>

## sandbox.instance

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#field-sandbox-instance-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#field-sandbox-instance-metadata) | no | empty map | — | Provider instance metadata. |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | Memory amount; Express uses MB, other adapters retain their input units. |
| `disk` | [nonnegative integer or expression](#type-nonnegativeintegerinput) | no | — | — | Instance disk amount in MB. |
| `gpu` | string | no | — | length ≥ 1 | Provider GPU selector; OpenSandbox requires a count string. |
| `secure` | [boolean or expression](#type-booleaninput) | no | — | — | OpenSandbox secure-mode setting. |
| `volume_mounts` | object · [fields](#field-sandbox-instance-volume-mounts) | no | — | — | Guest mount path to existing volume name; no volume creation. |
| `lifecycle` | object · [fields](#field-sandbox-instance-lifecycle) | no | — | — | Instance timeout policy. |
| `provider_options` | object · [fields](#field-sandbox-instance-provider-options) | no | — | — | Selected Provider's integrated create options. |

- Other fields are rejected.

<a id="field-sandbox-instance-envs"></a>

## sandbox.instance.envs

Each map value: string


<a id="field-sandbox-instance-metadata"></a>

## sandbox.instance.metadata

Each map value: string


<a id="field-sandbox-instance-volume-mounts"></a>

## sandbox.instance.volume_mounts

Each map value: string

Map keys: absolute mount path; system paths excluded


<a id="field-sandbox-instance-lifecycle"></a>

## sandbox.instance.lifecycle

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `onTimeout` | string | yes | — | `"pause"`, `"kill"` | Pause or delete the instance on timeout. |
| `autoResume` | [boolean or expression](#type-booleaninput) | no | — | — | Automatic resume; requires onTimeout=pause. |

- Other fields are rejected.

<a id="field-sandbox-instance-provider-options"></a>

## sandbox.instance.provider_options

[OpenSandbox options](#type-opensandboxoptions)


<a id="field-sandbox-services"></a>

## sandbox.services

Each map value: [service](#type-service)

Map keys: complete ASCII identifier


<a id="field-sandbox-allof-0-then"></a>

## sandbox — provider=alicloud-express

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_alicloud-express](#type-instance-alicloud-express) | no | — | — | Instance creation settings, separate from preparation. |
| `template` | object · [fields](#field-sandbox-allof-0-then-template) | yes | — | — | Environment source, image or existing reference. |


<a id="field-sandbox-allof-0-then-template"></a>

## sandbox — provider=alicloud-express.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-allof-0-then-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-allof-0-then-template-props"></a>

## sandbox — provider=alicloud-express.template.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | `2` | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | `2048`; agents-api:4096 | — | Memory amount; Express uses MB, other adapters retain their input units. |

- Other fields are rejected.
- Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.

<a id="field-sandbox-allof-1-then"></a>

## sandbox — provider=opensandbox

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_opensandbox](#type-instance-opensandbox) | no | — | — | Instance creation settings, separate from preparation. |
| `template` | object · [fields](#field-sandbox-allof-1-then-template) | yes | — | — | Environment source, image or existing reference. |


<a id="field-sandbox-allof-1-then-template"></a>

## sandbox — provider=opensandbox.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-allof-1-then-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-allof-1-then-template-props"></a>

## sandbox — provider=opensandbox.template.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | `2` | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | `2048`; agents-api:4096 | — | Memory amount; Express uses MB, other adapters retain their input units. |

- Other fields are rejected.
- Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.

<a id="field-sandbox-allof-2-then"></a>

## sandbox — provider=e2b

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_e2b](#type-instance-e2b) | no | — | — | Instance creation settings, separate from preparation. |
| `template` | object · [fields](#field-sandbox-allof-2-then-template) | yes | — | — | Environment source, image or existing reference. |


<a id="field-sandbox-allof-2-then-template"></a>

## sandbox — provider=e2b.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-allof-2-then-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-allof-2-then-template-props"></a>

## sandbox — provider=e2b.template.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | `2` | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | `2048`; agents-api:4096 | — | Memory amount; Express uses MB, other adapters retain their input units. |

- Other fields are rejected.
- Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.

<a id="field-sandbox-allof-3-then"></a>

## sandbox — provider=cubesandbox

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_cubesandbox](#type-instance-cubesandbox) | no | — | — | Instance creation settings, separate from preparation. |
| `template` | object · [fields](#field-sandbox-allof-3-then-template) | yes | — | — | Environment source, image or existing reference. |


<a id="field-sandbox-allof-3-then-template"></a>

## sandbox — provider=cubesandbox.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-allof-3-then-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-allof-3-then-template-props"></a>

## sandbox — provider=cubesandbox.template.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | `2` | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | `2048`; agents-api:4096 | — | Memory amount; Express uses MB, other adapters retain their input units. |

- Other fields are rejected.
- Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.

<a id="field-sandbox-allof-4-then"></a>

## sandbox — provider=alicloud-container

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_alicloud-container](#type-instance-alicloud-container) | no | — | — | Instance creation settings, separate from preparation. |
| `template` | object · [fields](#field-sandbox-allof-4-then-template) | yes | — | — | Environment source, image or existing reference. |


<a id="field-sandbox-allof-4-then-template"></a>

## sandbox — provider=alicloud-container.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-allof-4-then-template-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-allof-4-then-template-props"></a>

## sandbox — provider=alicloud-container.template.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | `2` | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | `2048`; agents-api:4096 | — | Memory amount; Express uses MB, other adapters retain their input units. |

- Other fields are rejected.
- Project preparation checks memory ≥128 and a multiple of64; Express also requires1024–4096 per vCPU. Values are checked after native expression resolution. Backend limits remain Provider-owned.

<a id="field-deployment"></a>

## deployment

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `edition` | string | yes | — | = `"3.0.0"` | Native Devs project edition. |
| `name` | string | no | root name | length ≥ 1 | Native project name. |
| `access` | string | no | `"default"` | length ≥ 1 | Existing Serverless Devs credential alias. |
| `vars` | object · [fields](#field-deployment-vars) | no | — | — | Native project variables. |
| `resources` | object · [fields](#field-deployment-resources) | yes | — | fields ≥ 1 | Native component resources keyed by project ID. |
| `flow` | object · [fields](#field-deployment-flow) | no | — | — | Native Devs execution flow. |
| `actions` | native JSON value | no | — | — | Native Devs lifecycle actions. |
| `template` | object · [fields](#field-deployment-template) | no | — | — | Native Devs project template settings. |
| `validation` | boolean | no | — | — | Native project validation setting. |

- Other fields are rejected.

<a id="field-deployment-vars"></a>

## deployment.vars

Object contents are defined by the native component or linked usage reference.


<a id="field-deployment-resources"></a>

## deployment.resources

Each map value: object · [fields](#field-deployment-resources-additionalproperties)

Map keys: complete ASCII identifier


<a id="field-deployment-resources-additionalproperties"></a>

## deployment.resources.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `component` | string | yes | — | length ≥ 1 | Actual native component identifier and version. |
| `props` | [native object or expression](#type-componentprops) | yes | — | — | Native component-owned props; not a duplicated FC schema. |
| `actions` | native JSON value | no | — | — | Native Devs lifecycle actions. |

- Other fields are rejected.

<a id="field-deployment-flow"></a>

## deployment.flow

Object contents are defined by the native component or linked usage reference.


<a id="field-deployment-template"></a>

## deployment.template

Object contents are defined by the native component or linked usage reference.


<a id="field-application"></a>

## application

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `type` | string | yes | — | = `"agents-api"` | Declared application or hook type. |
| `roles` | object · [fields](#field-application-roles) | yes | — | — | References to three distinct native FC resources. |
| `server` | object · [fields](#field-application-server) | yes | — | — | Server image source or digest-pinned image. |
| `sessions` | object · [fields](#field-application-sessions) | no | — | — | Managed Session admission and retention settings. |
| `storage` | object · [fields](#field-application-storage) | no | — | — | File and artifact storage bounds. |
| `limits` | object · [fields](#field-application-limits) | no | — | — | Run, queue, event and output budgets. |
| `state` | object · [fields](#field-application-state) | yes | — | — | Existing durable database and optional connection settings. |
| `bindings` | object · [fields](#field-application-bindings) | yes | — | — | Local business and credential inputs. |
| `hooks` | object · [fields](#field-application-hooks) | no | — | — | Optional bounded deployment checks. |

- Other fields are rejected.

<a id="field-application-roles"></a>

## application.roles

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `gateway` | string | yes | — | length ≥ 1 | Public Gateway resource ID. |
| `worker` | string | yes | — | length ≥ 1 | Private Worker resource ID. |
| `dispatcher` | string | yes | — | length ≥ 1 | Private Dispatcher resource ID. |

- Other fields are rejected.

<a id="field-application-server"></a>

## application.server

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `source` | [recipe](#type-recipe) | no | — | — | Contained source build recipe. |
| `image` | string | no | — | image@sha256:64 lowercase hex digits | Digest-pinned Server image, exclusive with source. |

- Other fields are rejected.
- Choose exactly one: `source`; `image`.

<a id="field-application-sessions"></a>

## application.sessions

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `idleTimeoutSeconds` | integer or [native expression](#type-expression) | no | `900` | literal: ≥ 1 | Session idle timeout in seconds. |
| `maxLogicalSessionsPerOwner` | integer or [native expression](#type-expression) | no | `100` | literal: ≥ 1 | Maximum logical Sessions per owner. |
| `maxActiveSessions` | integer or [native expression](#type-expression) | no | `20` | literal: ≥ 1 | Active Session admission limit. |
| `maxQueuedTurnsPerSession` | integer or [native expression](#type-expression) | no | `8` | literal: ≥ 1 | Queued turns per Session. |
| `resultRetentionSeconds` | integer or [native expression](#type-expression) | no | `86400` | literal: ≥ 1 | Committed-result retention in seconds. |

- Other fields are rejected.

<a id="field-application-storage"></a>

## application.storage

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `maxFileBytes` | integer or [native expression](#type-expression) | no | `10485760` | literal: ≥ 1 | Maximum input file size in bytes. |
| `maxArtifactBytes` | integer or [native expression](#type-expression) | no | `10485760` | literal: ≥ 1 | Maximum individual artifact size in bytes. |
| `maxTurnArtifactBytes` | integer or [native expression](#type-expression) | no | `10485760` | literal: ≥ 1 | Total artifact bytes per turn. |
| `maxRetainedBytesPerOwner` | integer or [native expression](#type-expression) | no | `104857600` | literal: ≥ 1 | Retained bytes per owner. |

- Other fields are rejected.

<a id="field-application-limits"></a>

## application.limits

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `maxRunSeconds` | integer or [native expression](#type-expression) | no | `600` | literal: ≥ 1 | Run time budget in seconds. |
| `maxToolSeconds` | integer or [native expression](#type-expression) | no | `60` | literal: ≥ 1 | Tool-call time budget in seconds. |
| `maxConcurrentRuns` | integer or [native expression](#type-expression) | no | `10` | literal: ≥ 1 | Concurrent-run admission budget. |
| `maxQueuedRuns` | integer or [native expression](#type-expression) | no | `80` | literal: ≥ 1 | Queued-run admission budget. |
| `maxRunsPerMinute` | integer or [native expression](#type-expression) | no | `60` | literal: ≥ 1 | Run admission budget per minute. |
| `maxEventsPerRun` | integer or [native expression](#type-expression) | no | `10000` | literal: ≥ 5 | Event count bound per run. |
| `maxOutputBytes` | integer or [native expression](#type-expression) | no | `8388608` | literal: ≥ 1024 | Captured output bound in bytes. |
| `maxSubscribersPerSession` | integer or [native expression](#type-expression) | no | `4` | literal: ≥ 1; ≤ 100 | Concurrent event subscribers per Session. |

- Other fields are rejected.

<a id="field-application-state"></a>

## application.state

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `databaseUrl` | [secret expression](#type-secret) | yes | — | — | Existing PostgreSQL connection URL; Server-only. |
| `vpcConfig` | object · [fields](#field-application-state-vpcconfig) | no | — | — | Existing FC network configuration; see the Managed reference. |
| `databaseCa` | [secret expression](#type-secret) | no | — | — | Optional private database CA certificate PEM. |

- Other fields are rejected.

<a id="field-application-state-vpcconfig"></a>

## application.state.vpcConfig

Existing network IDs: see [configuration and bindings](managed-agent-applications.md#configuration-and-bindings).


<a id="field-application-bindings"></a>

## application.bindings

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `sandboxAccess` | object · [fields](#field-application-bindings-sandboxaccess) | yes | — | — | Server-only Sandbox lifecycle access. |
| `model` | object · [fields](#field-application-bindings-model) | yes | — | — | Allowed model identifier or model-access configuration. |
| `clientAuth` | object · [generate=true](#field-application-bindings-clientauth-oneof-0) or object · [explicit tokens](#field-application-bindings-clientauth-oneof-1) or [native expression](#type-expression) | no | generated credentials | — | Generated business credentials or explicit token hashes. |
| `internalAuth` | object · [generate=true](#field-application-bindings-internalauth-oneof-0) or object · [explicit token](#field-application-bindings-internalauth-oneof-1) or [native expression](#type-expression) | no | generated credentials | — | Separate private control-plane authentication. |
| `ingress` | object · [fields](#field-application-bindings-ingress) | yes | — | — | Stable Gateway alias or domain route. |

- Other fields are rejected.

<a id="field-application-bindings-sandboxaccess"></a>

## application.bindings.sandboxAccess

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `apiKey` | [secret expression](#type-secret) | yes | — | — | Referenced service API key. |
| `baseUrl` | string | yes | — | length ≥ 1 | Explicit service API base URL. |
| `domain` | string | yes | — | length ≥ 1 | Sandbox endpoint domain from the selected platform. |
| `region` | string | yes | — | length ≥ 1 | Matching target region. |

- Other fields are rejected.

<a id="field-application-bindings-model"></a>

## application.bindings.model

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `apiKey` | [secret expression](#type-secret) | yes | — | — | Referenced service API key. |
| `baseUrl` | string | yes | — | length ≥ 1 | Explicit service API base URL. |
| `model` | string | yes | — | length ≥ 1 | Allowed model identifier or model-access configuration. |
| `adapter` | string | yes | — | `"codex"`, `"qwen-code"` | Agent CLI adapter matching the model API. |

- Other fields are rejected.

<a id="field-application-bindings-clientauth"></a>

## application.bindings.clientAuth

object · [generate=true](#field-application-bindings-clientauth-oneof-0) or object · [explicit tokens](#field-application-bindings-clientauth-oneof-1) or [native expression](#type-expression)


<a id="field-application-bindings-clientauth-oneof-0"></a>

## application.bindings.clientAuth — generate=true

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `generate` | boolean | yes | `true` | = `true` | Generate and safely reuse a local credential. |
| `owner` | string | no | `"default"` | length ≥ 1 | Business credential owner. |

- Other fields are rejected.

<a id="field-application-bindings-clientauth-oneof-1"></a>

## application.bindings.clientAuth — explicit tokens

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `tokens` | array of object · [fields](#field-application-bindings-clientauth-oneof-1-tokens-items) | yes | — | items ≥ 1 | Explicit accepted business-token hashes. |

- Other fields are rejected.

<a id="field-application-bindings-clientauth-oneof-1-tokens-items"></a>

## application.bindings.clientAuth — explicit tokens.tokens[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `sha256` | string | yes | — | 64 lowercase hex digits | Lowercase SHA256 of a business token, never its plaintext. |
| `owner` | string | yes | — | length ≥ 1 | Business credential owner. |
| `scopes` | array of string | yes | — | items ≥ 1; unique items; each: `"agents:read"`, `"agents:write"` | Allowed business API scopes. |
| `expiresAt` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | Credential expiration timestamp. |

- Other fields are rejected.

<a id="field-application-bindings-internalauth"></a>

## application.bindings.internalAuth

object · [generate=true](#field-application-bindings-internalauth-oneof-0) or object · [explicit token](#field-application-bindings-internalauth-oneof-1) or [native expression](#type-expression)


<a id="field-application-bindings-internalauth-oneof-0"></a>

## application.bindings.internalAuth — generate=true

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `generate` | boolean | yes | `true` | = `true` | Generate and safely reuse a local credential. |
| `roleArn` | string | no | — | length ≥ 1 | Existing FC execution role; must agree with native roles. |

- Other fields are rejected.

<a id="field-application-bindings-internalauth-oneof-1"></a>

## application.bindings.internalAuth — explicit token

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `token` | [secret expression](#type-secret) | yes | — | — | Referenced private internal token. |
| `roleArn` | string | no | — | length ≥ 1 | Existing FC execution role; must agree with native roles. |

- Other fields are rejected.

<a id="field-application-bindings-ingress"></a>

## application.bindings.ingress

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `kind` | string | yes | — | `"function-alias"`, `"custom-domain"` | Gateway ingress mode. |
| `aliasName` | string | no | `"prod"` | length ≥ 1 | Stable FC alias name. |
| `allowTestDomain` | boolean | no | — | — | Explicitly allow the FC test domain. |
| `domainName` | string | no | — | length ≥ 1 | Configured HTTPS custom domain. |
| `protocol` | string | no | — | = `"HTTPS"` | Declared service protocol, or HTTPS for custom-domain ingress. |
| `path` | string | no | — | = `"/"` | Custom-domain root route. |

- Other fields are rejected.
- [When kind=function-alias](#field-application-bindings-ingress-allof-0-then)
- [When kind=custom-domain](#field-application-bindings-ingress-allof-1-then)

<a id="field-application-bindings-ingress-allof-0-then"></a>

## application.bindings.ingress — kind=function-alias

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `allowTestDomain` | boolean | yes | — | = `true` | Explicitly allow the FC test domain. |

- Do not provide: `domainName`, `protocol`, `path`.

<a id="field-application-bindings-ingress-allof-1-then"></a>

## application.bindings.ingress — kind=custom-domain

- Required inherited fields: `domainName`, `protocol`.
- Do not provide: `allowTestDomain`.

<a id="field-application-hooks"></a>

## application.hooks

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `beforeApply` | [hooks](#type-hooks) | no | — | — | Checks before applying deployment changes. |
| `afterReady` | [hooks](#type-hooks) | no | — | — | Checks after the candidate becomes ready. |

- Other fields are rejected.

<a id="type-expression"></a>

## expression

string; native `${...}`; evaluated by Devs


<a id="type-positiveintegerinput"></a>

## positiveIntegerInput

integer or [native expression](#type-expression)

literal: ≥ 1; ≤ 9007199254740991


<a id="type-nonnegativeintegerinput"></a>

## nonnegativeIntegerInput

integer or [native expression](#type-expression)

literal: ≥ 0; ≤ 9007199254740991


<a id="type-booleaninput"></a>

## booleanInput

boolean or [native expression](#type-expression)


<a id="type-secret"></a>

## secret

string; native `${...}`; evaluated by Devs


<a id="type-componentprops"></a>

## componentProps

object · [choice 1](#type-componentprops-oneof-0) or [native expression](#type-expression)


<a id="type-componentprops-oneof-0"></a>

## componentProps — choice 1

Object contents are defined by the native component or linked usage reference.


<a id="type-source"></a>

## source

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | no | `"Dockerfile"` | length ≥ 1 | Dockerfile inside the template directory. |
| `context` | string | no | `"."` | = `"."` | Build context rooted in the template directory. |
| `profiles` | object · [fields](#type-source-properties-profiles) | no | — | — | Explicit alternate source recipes. |

- Other fields are rejected.

<a id="type-source-properties-profiles"></a>

## source.profiles

Each map value: object · [fields](#type-source-properties-profiles-additionalproperties)

Map keys: complete ASCII identifier


<a id="type-source-properties-profiles-additionalproperties"></a>

## source.profiles.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | no | `"Dockerfile"` | length ≥ 1 | Dockerfile inside the template directory. |
| `context` | string | no | `"."` | = `"."` | Build context rooted in the template directory. |

- Other fields are rejected.

<a id="type-recipe"></a>

## recipe

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | no | `"Dockerfile"` | length ≥ 1 | Dockerfile inside the template directory. |
| `context` | string | no | `"."` | = `"."` | Build context rooted in the template directory. |

- Other fields are rejected.

<a id="type-service"></a>

## service

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `protocol` | string | yes | — | length ≥ 1 | Declared service protocol, or HTTPS for custom-domain ingress. |
| `version` | integer | yes | — | ≥ 1; ≤ 9007199254740991 | Service protocol contract version. |
| `port` | integer | yes | — | ≥ 1; ≤ 65535 | Service access port. |
| `operations` | array of string | no | empty list | unique items; each: length ≥ 1 | Described service operations; not a permission grant. |

- Other fields are rejected.

<a id="type-opensandboxoptions"></a>

## openSandboxOptions

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `entrypoint` | string | no | — | length ≥ 1 | OpenSandbox container entrypoint command. |
| `ready_timeout` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | OpenSandbox readiness wait in seconds. |
| `network_policy` | string | no | — | length ≥ 1 | OpenSandbox network-policy selector. |
| `platform` | string | no | — | `"linux/amd64"`, `"linux/arm64"`, `"windows/amd64"`, `"windows/arm64"` | Container operating system and architecture. |
| `secure_access` | [boolean or expression](#type-booleaninput) | no | — | — | OpenSandbox secure-access option. |

- Other fields are rejected.

<a id="type-instance-alicloud-express"></a>

## instance_alicloud-express

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#type-instance-alicloud-express-properties-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#type-instance-alicloud-express-properties-metadata) | no | empty map | — | Provider instance metadata. |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | Memory amount; Express uses MB, other adapters retain their input units. |
| `disk` | [nonnegative integer or expression](#type-nonnegativeintegerinput) | no | — | — | Instance disk amount in MB. |
| `gpu` | string | no | — | length ≥ 1 | Provider GPU selector; OpenSandbox requires a count string. |
| `volume_mounts` | object · [fields](#type-instance-alicloud-express-properties-volume-mounts) | no | — | — | Guest mount path to existing volume name; no volume creation. |
| `lifecycle` | object · [fields](#type-instance-alicloud-express-properties-lifecycle) | no | — | — | Instance timeout policy. |

- Other fields are rejected.

<a id="type-instance-alicloud-express-properties-envs"></a>

## instance_alicloud-express.envs

Each map value: string


<a id="type-instance-alicloud-express-properties-metadata"></a>

## instance_alicloud-express.metadata

Each map value: string


<a id="type-instance-alicloud-express-properties-volume-mounts"></a>

## instance_alicloud-express.volume_mounts

Each map value: string

Map keys: absolute mount path; system paths excluded


<a id="type-instance-alicloud-express-properties-lifecycle"></a>

## instance_alicloud-express.lifecycle

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `onTimeout` | string | yes | — | `"pause"`, `"kill"` | Pause or delete the instance on timeout. |
| `autoResume` | [boolean or expression](#type-booleaninput) | no | — | — | Automatic resume; requires onTimeout=pause. |

- Other fields are rejected.

<a id="type-instance-opensandbox"></a>

## instance_opensandbox

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#type-instance-opensandbox-properties-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#type-instance-opensandbox-properties-metadata) | no | empty map | — | Provider instance metadata. |
| `cpu` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | vCPU count for this stage. |
| `memory` | [positive integer or expression](#type-positiveintegerinput) | no | — | — | Memory amount; Express uses MB, other adapters retain their input units. |
| `gpu` | string | no | — | length ≥ 1 | Provider GPU selector; OpenSandbox requires a count string. |
| `secure` | [boolean or expression](#type-booleaninput) | no | — | — | OpenSandbox secure-mode setting. |
| `provider_options` | [openSandboxOptions](#type-opensandboxoptions) | no | — | — | Selected Provider's integrated create options. |

- Other fields are rejected.

<a id="type-instance-opensandbox-properties-envs"></a>

## instance_opensandbox.envs

Each map value: string


<a id="type-instance-opensandbox-properties-metadata"></a>

## instance_opensandbox.metadata

Each map value: string


<a id="type-instance-e2b"></a>

## instance_e2b

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#type-instance-e2b-properties-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#type-instance-e2b-properties-metadata) | no | empty map | — | Provider instance metadata. |

- Other fields are rejected.

<a id="type-instance-e2b-properties-envs"></a>

## instance_e2b.envs

Each map value: string


<a id="type-instance-e2b-properties-metadata"></a>

## instance_e2b.metadata

Each map value: string


<a id="type-instance-cubesandbox"></a>

## instance_cubesandbox

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#type-instance-cubesandbox-properties-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#type-instance-cubesandbox-properties-metadata) | no | empty map | — | Provider instance metadata. |

- Other fields are rejected.

<a id="type-instance-cubesandbox-properties-envs"></a>

## instance_cubesandbox.envs

Each map value: string


<a id="type-instance-cubesandbox-properties-metadata"></a>

## instance_cubesandbox.metadata

Each map value: string


<a id="type-instance-alicloud-container"></a>

## instance_alicloud-container

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [positive integer or expression](#type-positiveintegerinput) | no | 300; agents-api:3600 | — | Instance lifetime in seconds; maximum 86400. |
| `envs` | object · [fields](#type-instance-alicloud-container-properties-envs) | no | empty map | — | Declared guest environment values. |
| `metadata` | object · [fields](#type-instance-alicloud-container-properties-metadata) | no | empty map | — | Provider instance metadata. |

- Other fields are rejected.

<a id="type-instance-alicloud-container-properties-envs"></a>

## instance_alicloud-container.envs

Each map value: string


<a id="type-instance-alicloud-container-properties-metadata"></a>

## instance_alicloud-container.metadata

Each map value: string


<a id="type-refname"></a>

## refName

string; ASCII reference ID, 1–128 characters


<a id="type-relativepath"></a>

## relativePath

string; length ≥ 1; length ≤ 1024; contained relative path


<a id="type-hooks"></a>

## hooks

array of object · [type=custom](#type-hooks-items-oneof-0) or object · [type=serverless-devs](#type-hooks-items-oneof-1); items ≤ 8


<a id="type-hooks-items"></a>

## hooks[]

object · [type=custom](#type-hooks-items-oneof-0) or object · [type=serverless-devs](#type-hooks-items-oneof-1)

- Choose exactly one: `id`, `type`, `argv`, `cwd`, `timeoutSeconds`, `envAllowlist`; `id`, `type`, `step`, `command`, `timeoutSeconds`.

<a id="type-hooks-items-oneof-0"></a>

## hooks[] — type=custom

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `id` | [refName](#type-refname) | yes | — | — | Unique hook identifier across phases. |
| `type` | string | yes | — | = `"custom"` | Declared application or hook type. |
| `argv` | array of string | yes | — | items ≥ 1; items ≤ 64; each: length ≥ 1; length ≤ 4096 | Executable and arguments; no implicit shell. |
| `cwd` | [relativePath](#type-relativepath) | yes | — | — | Contained working directory relative to the template. |
| `timeoutSeconds` | integer | yes | — | ≥ 1; ≤ 900 | Hook time budget in seconds. |
| `envAllowlist` | array of string | yes | — | unique items; each: complete ASCII identifier | Host variable names allowed into this hook. |

- Other fields are rejected.

<a id="type-hooks-items-oneof-1"></a>

## hooks[] — type=serverless-devs

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `id` | [refName](#type-refname) | yes | — | — | Unique hook identifier across phases. |
| `type` | string | yes | — | = `"serverless-devs"` | Declared application or hook type. |
| `step` | string | yes | — | `"gateway"`, `"worker"`, `"dispatcher"` | Managed role inspected by the native info command. |
| `command` | string | yes | — | = `"info"` | Read-only native component command. |
| `timeoutSeconds` | integer | yes | — | ≥ 1; ≤ 900 | Hook time budget in seconds. |

- Other fields are rejected.
