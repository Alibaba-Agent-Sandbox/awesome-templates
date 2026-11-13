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
| `vars` | object · [fields](#field-vars) | no | — | — | Native project variables. |
| `sandbox` | object · [fields](#field-sandbox) | no | — | fields ≥ 1 | Named Sandbox resources. |
| `serving` | object · [fields](#field-serving) | no | — | fields ≥ 1 | Named native component resources. |

- Other fields are rejected.
- At least one: `sandbox`; `serving`.

<a id="field-vars"></a>

## vars

Object contents are defined by the native component or linked usage reference.


<a id="field-sandbox"></a>

## sandbox

Each map value: object · [fields](#field-sandbox-additionalproperties)

Map keys: complete ASCII identifier


<a id="field-sandbox-additionalproperties"></a>

## sandbox.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `provider` | string | yes | — | length ≥ 1 | Provider selected before execution. |
| `template` | object · [fields](#field-sandbox-additionalproperties-template) | yes | — | — | Environment source, image or existing reference. |
| `volumes` | object · [fields](#field-sandbox-additionalproperties-volumes) | no | — | — | Named static volume resources. |
| `actions` | object · [fields](#field-sandbox-additionalproperties-actions) | no | — | — | Native Devs lifecycle actions. |

- Other fields are rejected.
- [When provider=alicloud-express](#field-sandbox-additionalproperties-allof-0-then)

<a id="field-sandbox-additionalproperties-template"></a>

## sandbox.<name>.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | no | — | length ≥ 1 | Existing Provider-native template ID; never translated across Providers. |
| `region` | string | no | — | length ≥ 1 | Matching target region. |
| `image` | string | no | — | length ≥ 1 | Container image input. |
| `buildConfig` | object · [fields](#field-sandbox-additionalproperties-template-buildconfig) | no | — | — | Dockerfile/context or native steps. |

- At least one: `reference`; `image`; `buildConfig`.

<a id="field-sandbox-additionalproperties-template-buildconfig"></a>

## sandbox.<name>.template.buildConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | no | — | length ≥ 1 | Dockerfile inside the template directory. |
| `context` | string | no | Dockerfile directory | length ≥ 1 | Build context rooted in the template directory. |
| `steps` | array of object · [fields](#field-sandbox-additionalproperties-template-buildconfig-steps-items) | no | — | items ≥ 1 | Ordered native template preparation steps. |

- Other fields are rejected.
- Choose exactly one: `dockerfile`; `steps`.

<a id="field-sandbox-additionalproperties-template-buildconfig-steps-items"></a>

## sandbox.<name>.template.buildConfig.steps[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `type` | string | yes | — | `"USER"`, `"WORKDIR"`, `"ENV"`, `"RUN"` | Declared application or hook type. |
| `args` | array of string | yes | — | items ≥ 1 | Native step arguments. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-volumes"></a>

## sandbox.<name>.volumes

Each map value: object · [fields](#field-sandbox-additionalproperties-volumes-additionalproperties)

Map keys: complete ASCII identifier


<a id="field-sandbox-additionalproperties-volumes-additionalproperties"></a>

## sandbox.<name>.volumes.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | no | — | length ≥ 1 | Existing Provider-native template ID; never translated across Providers. |
| `retain` | boolean | no | — | — | Keep an owned volume on resource removal. |
| `props` | object · [fields](#field-sandbox-additionalproperties-volumes-additionalproperties-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |

- Other fields are rejected.
- Choose exactly one: `reference`; `props`.

<a id="field-sandbox-additionalproperties-volumes-additionalproperties-props"></a>

## sandbox.<name>.volumes.<name>.props

Object contents are defined by the native component or linked usage reference.


<a id="field-sandbox-additionalproperties-actions"></a>

## sandbox.<name>.actions

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `pre-deploy` | array of object · [fields](#field-sandbox-additionalproperties-actions-pre-deploy-items) | no | — | — | Host actions before resource deployment. |
| `success-deploy` | array of object · [fields](#field-sandbox-additionalproperties-actions-success-deploy-items) | no | — | — | Host actions after resource readiness. |
| `fail-deploy` | array of object · [fields](#field-sandbox-additionalproperties-actions-fail-deploy-items) | no | — | — | Host actions on deployment failure. |
| `complete-deploy` | array of object · [fields](#field-sandbox-additionalproperties-actions-complete-deploy-items) | no | — | — | Host actions on either deployment outcome. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-actions-pre-deploy-items"></a>

## sandbox.<name>.actions.pre-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-sandbox-additionalproperties-actions-success-deploy-items"></a>

## sandbox.<name>.actions.success-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-sandbox-additionalproperties-actions-fail-deploy-items"></a>

## sandbox.<name>.actions.fail-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-sandbox-additionalproperties-actions-complete-deploy-items"></a>

## sandbox.<name>.actions.complete-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-sandbox-additionalproperties-allof-0-then"></a>

## sandbox.<name> — provider=alicloud-express

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `template` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template) | yes | — | — | Environment source, image or existing reference. |
| `volumes` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes) | no | — | — | Named static volume resources. |


<a id="field-sandbox-additionalproperties-allof-0-then-template"></a>

## sandbox.<name> — provider=alicloud-express.template

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | no | — | length ≥ 1 | Existing Provider-native template ID; never translated across Providers. |
| `region` | string | no | — | length ≥ 1 | Matching target region. |
| `image` | string | no | — | length ≥ 1 | Container image input. |
| `buildConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-buildconfig) | no | — | — | Dockerfile/context or native steps. |
| `registryConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig) | no | — | — | Optional image pull registry overrides. |
| `generation` | string or [native expression](#type-expression) | no | — | literal: `1`, `2` | Sandbox runtime generation, not API version. |
| `cpu` | number or [native expression](#type-expression) | no | — | — | vCPU count for this stage. |
| `memorySize` | integer or [native expression](#type-expression) | no | — | literal: ≥ 1 | Sandbox memory, MB. |
| `diskSize` | integer or [native expression](#type-expression) | no | — | literal: ≥ 0 | Sandbox disk, MB. |
| `internetAccess` | boolean or [native expression](#type-expression) | no | — | — | Allow outgoing public network access. |
| `logConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-logconfig) | no | — | — | Existing log delivery destination. |
| `vpcConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-vpcconfig) | no | — | — | Existing FC network configuration; see the Managed reference. |
| `startCommand` | string | no | — | length ≥ 1 | Native template preparation startup command. |
| `readyCommand` | string | no | — | length ≥ 1 | Native template preparation readiness command. |
| `resourceTags` | array of object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-resourcetags-items) | no | — | — | Template resource tags. |

- Other fields are rejected.
- At least one: `reference`; `image`; `buildConfig`.

<a id="field-sandbox-additionalproperties-allof-0-then-template-buildconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.buildConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | no | — | length ≥ 1 | Dockerfile inside the template directory. |
| `context` | string | no | Dockerfile directory | length ≥ 1 | Build context rooted in the template directory. |
| `steps` | array of object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-buildconfig-steps-items) | no | — | items ≥ 1 | Ordered native template preparation steps. |

- Other fields are rejected.
- Choose exactly one: `dockerfile`; `steps`.

<a id="field-sandbox-additionalproperties-allof-0-then-template-buildconfig-steps-items"></a>

## sandbox.<name> — provider=alicloud-express.template.buildConfig.steps[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `type` | string | yes | — | `"USER"`, `"WORKDIR"`, `"ENV"`, `"RUN"` | Declared application or hook type. |
| `args` | array of string | yes | — | items ≥ 1 | Native step arguments. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `authConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-authconfig) | no | — | — | Registry authentication. |
| `certConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-certconfig) | no | — | — | Registry TLS verification settings. |
| `networkConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-networkconfig) | no | — | — | Network used to access the registry. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-authconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.authConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `userName` | string | no | — | length ≥ 1 | Registry login username. |
| `password` | string | no | — | length ≥ 1 | Private registry password or access token. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-certconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.certConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `insecure` | boolean or [native expression](#type-expression) | no | — | — | Skip registry HTTPS certificate verification. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-networkconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.networkConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `vpcId` | string | no | — | length ≥ 1 | Existing VPC ID. |
| `vSwitchId` | string | no | — | length ≥ 1 | Existing virtual switch ID. |
| `securityGroupId` | string | no | — | length ≥ 1 | Existing security group ID. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-logconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.logConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `logstore` | string | no | — | length ≥ 1 | Existing Logstore name. |
| `project` | string | no | — | length ≥ 1 | Existing log Project name. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-vpcconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.vpcConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `role` | string | no | — | length ≥ 1 | Existing execution role ARN. |
| `vpcId` | string | no | — | length ≥ 1 | Existing VPC ID. |
| `securityGroupId` | string | no | — | length ≥ 1 | Existing security group ID. |
| `vSwitchIds` | array of string | no | — | each: length ≥ 1 | Existing virtual switch IDs. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-template-resourcetags-items"></a>

## sandbox.<name> — provider=alicloud-express.template.resourceTags[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `key` | string | yes | — | length ≥ 1 | Tag key. |
| `value` | string | yes | — | — | Tag value. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes"></a>

## sandbox.<name> — provider=alicloud-express.volumes

Each map value: object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties)


<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props) | no | — | — | Selected Provider preparation inputs; see its conditional fields. |


<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `agenticBucketVolumeConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticbucketvolumeconfig) | no | — | — | AgenticBucket backend. |
| `agenticFSVolumeConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticfsvolumeconfig) | no | — | — | AgenticFS backend. |
| `juiceFSVolumeConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-juicefsvolumeconfig) | no | — | — | JuiceFS backend. |
| `ossVolumeConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-ossvolumeconfig) | no | — | — | OSS backend. |
| `mountConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig) | no | — | — | Native volume mount network and role. |
| `volumeName` | string | no | — | length ≥ 1 | Native volume name, unique within Team. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticbucketvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.agenticBucketVolumeConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `agenticBucket` | string | no | — | length ≥ 1 | AgenticBucket name. |
| `bucketName` | string | no | — | length ≥ 1 | Existing OSS bucket name. |
| `bucketPath` | string | no | — | length ≥ 1 | Path prefix within the bucket. |
| `endpoint` | string | no | — | length ≥ 1 | Storage service endpoint. |
| `readOnly` | boolean or [native expression](#type-expression) | no | — | — | Mount storage read-only. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticfsvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.agenticFSVolumeConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `groupID` | integer or [native expression](#type-expression) | no | — | — | Mount group ID. |
| `userID` | integer or [native expression](#type-expression) | no | — | — | Mount user ID. |
| `serverAddr` | string | no | — | length ≥ 1 | Storage server or access-point address. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-juicefsvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.juiceFSVolumeConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `baseURL` | string | no | — | length ≥ 1 | Storage access-point base URL. |
| `remoteDir` | string | no | — | length ≥ 1 | Remote directory. |
| `token` | string | no | — | length ≥ 1 | Referenced private internal token. |
| `volumeName` | string | no | — | length ≥ 1 | Native volume name, unique within Team. |
| `args` | array of string | no | — | — | Native step arguments. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-ossvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.ossVolumeConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `bucketName` | string | no | — | length ≥ 1 | Existing OSS bucket name. |
| `bucketPath` | string | no | — | length ≥ 1 | Path prefix within the bucket. |
| `endpoint` | string | no | — | length ≥ 1 | Storage service endpoint. |
| `readOnly` | boolean or [native expression](#type-expression) | no | — | — | Mount storage read-only. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.mountConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `role` | string | no | — | length ≥ 1 | Existing execution role ARN. |
| `vpcConfig` | object · [fields](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig-vpcconfig) | no | — | — | Existing FC network configuration; see the Managed reference. |

- Other fields are rejected.

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig-vpcconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.mountConfig.vpcConfig

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `vpcId` | string | no | — | length ≥ 1 | Existing VPC ID. |
| `securityGroupId` | string | no | — | length ≥ 1 | Existing security group ID. |
| `vSwitchIds` | array of string | no | — | each: length ≥ 1 | Existing virtual switch IDs. |

- Other fields are rejected.

<a id="field-serving"></a>

## serving

Each map value: object · [fields](#field-serving-additionalproperties)

Map keys: complete ASCII identifier


<a id="field-serving-additionalproperties"></a>

## serving.<name>

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `component` | string | yes | — | complete ASCII identifier | Actual native component identifier and version. |
| `props` | object · [fields](#field-serving-additionalproperties-props) | yes | — | — | Native component-owned props; not a duplicated FC schema. |
| `actions` | object · [fields](#field-serving-additionalproperties-actions) | no | — | — | Native Devs lifecycle actions. |

- Other fields are rejected.

<a id="field-serving-additionalproperties-props"></a>

## serving.<name>.props

Object contents are defined by the native component or linked usage reference.


<a id="field-serving-additionalproperties-actions"></a>

## serving.<name>.actions

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `pre-deploy` | array of object · [fields](#field-serving-additionalproperties-actions-pre-deploy-items) | no | — | — | Host actions before resource deployment. |
| `success-deploy` | array of object · [fields](#field-serving-additionalproperties-actions-success-deploy-items) | no | — | — | Host actions after resource readiness. |
| `fail-deploy` | array of object · [fields](#field-serving-additionalproperties-actions-fail-deploy-items) | no | — | — | Host actions on deployment failure. |
| `complete-deploy` | array of object · [fields](#field-serving-additionalproperties-actions-complete-deploy-items) | no | — | — | Host actions on either deployment outcome. |

- Other fields are rejected.

<a id="field-serving-additionalproperties-actions-pre-deploy-items"></a>

## serving.<name>.actions.pre-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-serving-additionalproperties-actions-success-deploy-items"></a>

## serving.<name>.actions.success-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-serving-additionalproperties-actions-fail-deploy-items"></a>

## serving.<name>.actions.fail-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="field-serving-additionalproperties-actions-complete-deploy-items"></a>

## serving.<name>.actions.complete-deploy[]

| Field | Type | Required | Default | Constraints | Purpose |
| --- | --- | --- | --- | --- | --- |
| `run` | string | no | — | length ≥ 1 | Host shell command. |
| `component` | string | no | — | length ≥ 1 | Actual native component identifier and version. |
| `path` | string | no | — | length ≥ 1 | Custom-domain root route. |

- Other fields are rejected.
- Choose exactly one: `run`; `component`.

<a id="type-expression"></a>

## expression

string; native `${...}`; evaluated by Devs
