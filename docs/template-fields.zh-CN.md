# YAML v1 字段全表

字段按 YAML 路径分组。必填表示使用该对象或分支时必须填写；默认值来自共享 normalizer，破折号表示未声明默认值。

[用法和单位](template-spec.zh-CN.md) · [托管应用语义](managed-agent-applications.zh-CN.md) · [机器规范](../spec/template-v1.schema.json)

这里列出已接入的高层输入子集。原生 Devs/FC 对象的内部字段由所选组件定义；本表不复制其 schema，也不声称已接入其他 Provider API。

<a id="template"></a>

## template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `specVersion` | integer | 是 | — | = `1` | 公开资源格式版本。 |
| `name` | string | 是 | — | ASCII kebab-case，1–63字符 | 资源名称。 |
| `vars` | object · [子字段](#field-vars) | 否 | — | — | 原生项目变量。 |
| `sandbox` | object · [子字段](#field-sandbox) | 否 | — | fields ≥ 1 | 命名 Sandbox 资源。 |
| `serving` | object · [子字段](#field-serving) | 否 | — | fields ≥ 1 | 命名原生组件资源。 |

- 不接受其他字段。
- 至少填写一个：`sandbox`; `serving`.

<a id="field-vars"></a>

## vars

对象内部字段由原生组件或对应使用参考定义。


<a id="field-sandbox"></a>

## sandbox

每个映射值：object · [子字段](#field-sandbox-additionalproperties)

映射键：完整ASCII标识


<a id="field-sandbox-additionalproperties"></a>

## sandbox.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `provider` | string | 是 | — | length ≥ 1 | 执行前选定的 Provider。 |
| `template` | object · [子字段](#field-sandbox-additionalproperties-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |
| `volumes` | object · [子字段](#field-sandbox-additionalproperties-volumes) | 否 | — | — | 命名静态卷资源。 |
| `actions` | object · [子字段](#field-sandbox-additionalproperties-actions) | 否 | — | — | 原生 Devs 生命周期 actions。 |

- 不接受其他字段。
- [当 provider=alicloud-express](#field-sandbox-additionalproperties-allof-0-then)

<a id="field-sandbox-additionalproperties-template"></a>

## sandbox.<name>.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | 否 | — | length ≥ 1 | 已有 Provider 原生模板 ID，不跨 Provider 转换。 |
| `region` | string | 否 | — | length ≥ 1 | 与目标资源一致的地域。 |
| `image` | string | 否 | — | length ≥ 1 | 容器镜像输入。 |
| `buildConfig` | object · [子字段](#field-sandbox-additionalproperties-template-buildconfig) | 否 | — | — | Dockerfile/context 或原生步骤。 |

- 至少填写一个：`reference`; `image`; `buildConfig`.

<a id="field-sandbox-additionalproperties-template-buildconfig"></a>

## sandbox.<name>.template.buildConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | 否 | — | length ≥ 1 | 模板目录内的 Dockerfile。 |
| `context` | string | 否 | Dockerfile 所在目录 | length ≥ 1 | 以模板目录为根的构建上下文。 |
| `steps` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-template-buildconfig-steps-items) | 否 | — | items ≥ 1 | 有序的原生模板准备步骤。 |

- 不接受其他字段。
- 以下字段仅选一个：`dockerfile`; `steps`.

<a id="field-sandbox-additionalproperties-template-buildconfig-steps-items"></a>

## sandbox.<name>.template.buildConfig.steps[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `type` | string | 是 | — | `"USER"`, `"WORKDIR"`, `"ENV"`, `"RUN"` | 应用或 hook 的声明类型。 |
| `args` | 数组，每项为 string | 是 | — | items ≥ 1 | 原生步骤参数。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-volumes"></a>

## sandbox.<name>.volumes

每个映射值：object · [子字段](#field-sandbox-additionalproperties-volumes-additionalproperties)

映射键：完整ASCII标识


<a id="field-sandbox-additionalproperties-volumes-additionalproperties"></a>

## sandbox.<name>.volumes.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | 否 | — | length ≥ 1 | 已有 Provider 原生模板 ID，不跨 Provider 转换。 |
| `retain` | boolean | 否 | — | — | 移除资源时保留拥有卷。 |
| `props` | object · [子字段](#field-sandbox-additionalproperties-volumes-additionalproperties-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |

- 不接受其他字段。
- 以下字段仅选一个：`reference`; `props`.

<a id="field-sandbox-additionalproperties-volumes-additionalproperties-props"></a>

## sandbox.<name>.volumes.<name>.props

对象内部字段由原生组件或对应使用参考定义。


<a id="field-sandbox-additionalproperties-actions"></a>

## sandbox.<name>.actions

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `pre-deploy` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-actions-pre-deploy-items) | 否 | — | — | 资源部署前本机动作。 |
| `success-deploy` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-actions-success-deploy-items) | 否 | — | — | 资源就绪后本机动作。 |
| `fail-deploy` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-actions-fail-deploy-items) | 否 | — | — | 部署失败时本机动作。 |
| `complete-deploy` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-actions-complete-deploy-items) | 否 | — | — | 部署结束时本机动作。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-actions-pre-deploy-items"></a>

## sandbox.<name>.actions.pre-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-sandbox-additionalproperties-actions-success-deploy-items"></a>

## sandbox.<name>.actions.success-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-sandbox-additionalproperties-actions-fail-deploy-items"></a>

## sandbox.<name>.actions.fail-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-sandbox-additionalproperties-actions-complete-deploy-items"></a>

## sandbox.<name>.actions.complete-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-sandbox-additionalproperties-allof-0-then"></a>

## sandbox.<name> — provider=alicloud-express

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `template` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |
| `volumes` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes) | 否 | — | — | 命名静态卷资源。 |


<a id="field-sandbox-additionalproperties-allof-0-then-template"></a>

## sandbox.<name> — provider=alicloud-express.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `reference` | string | 否 | — | length ≥ 1 | 已有 Provider 原生模板 ID，不跨 Provider 转换。 |
| `region` | string | 否 | — | length ≥ 1 | 与目标资源一致的地域。 |
| `image` | string | 否 | — | length ≥ 1 | 容器镜像输入。 |
| `buildConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-buildconfig) | 否 | — | — | Dockerfile/context 或原生步骤。 |
| `registryConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig) | 否 | — | — | 可选镜像拉取仓库覆盖。 |
| `generation` | string / [原生表达式](#type-expression) | 否 | — | 字面值：`1`, `2` | 沙箱运行代际，不是 API 版本。 |
| `cpu` | number / [原生表达式](#type-expression) | 否 | — | — | 当前阶段的 vCPU 数。 |
| `memorySize` | integer / [原生表达式](#type-expression) | 否 | — | 字面值：≥ 1 | 沙箱内存，MB。 |
| `diskSize` | integer / [原生表达式](#type-expression) | 否 | — | 字面值：≥ 0 | 沙箱磁盘，MB。 |
| `internetAccess` | boolean / [原生表达式](#type-expression) | 否 | — | — | 允许访问公网。 |
| `logConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-logconfig) | 否 | — | — | 已有日志投递目标。 |
| `vpcConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-vpcconfig) | 否 | — | — | 已有 FC 网络配置，结构见托管应用参考。 |
| `startCommand` | string | 否 | — | length ≥ 1 | 原生模板准备阶段启动命令。 |
| `readyCommand` | string | 否 | — | length ≥ 1 | 原生模板准备阶段就绪命令。 |
| `resourceTags` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-resourcetags-items) | 否 | — | — | 模板资源标签。 |

- 不接受其他字段。
- 至少填写一个：`reference`; `image`; `buildConfig`.

<a id="field-sandbox-additionalproperties-allof-0-then-template-buildconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.buildConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | 否 | — | length ≥ 1 | 模板目录内的 Dockerfile。 |
| `context` | string | 否 | Dockerfile 所在目录 | length ≥ 1 | 以模板目录为根的构建上下文。 |
| `steps` | 数组，每项为 object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-buildconfig-steps-items) | 否 | — | items ≥ 1 | 有序的原生模板准备步骤。 |

- 不接受其他字段。
- 以下字段仅选一个：`dockerfile`; `steps`.

<a id="field-sandbox-additionalproperties-allof-0-then-template-buildconfig-steps-items"></a>

## sandbox.<name> — provider=alicloud-express.template.buildConfig.steps[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `type` | string | 是 | — | `"USER"`, `"WORKDIR"`, `"ENV"`, `"RUN"` | 应用或 hook 的声明类型。 |
| `args` | 数组，每项为 string | 是 | — | items ≥ 1 | 原生步骤参数。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `authConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-authconfig) | 否 | — | — | 镜像仓库认证。 |
| `certConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-certconfig) | 否 | — | — | 仓库 TLS 校验配置。 |
| `networkConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-template-registryconfig-networkconfig) | 否 | — | — | 访问仓库使用的网络。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-authconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.authConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `userName` | string | 否 | — | length ≥ 1 | 镜像仓库登录用户名。 |
| `password` | string | 否 | — | length ≥ 1 | 私有仓库密码或访问令牌。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-certconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.certConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `insecure` | boolean / [原生表达式](#type-expression) | 否 | — | — | 跳过仓库 HTTPS 证书校验。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-registryconfig-networkconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.registryConfig.networkConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `vpcId` | string | 否 | — | length ≥ 1 | 已有 VPC ID。 |
| `vSwitchId` | string | 否 | — | length ≥ 1 | 已有交换机 ID。 |
| `securityGroupId` | string | 否 | — | length ≥ 1 | 已有安全组 ID。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-logconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.logConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `logstore` | string | 否 | — | length ≥ 1 | 已有 Logstore 名称。 |
| `project` | string | 否 | — | length ≥ 1 | 已有日志 Project 名称。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-vpcconfig"></a>

## sandbox.<name> — provider=alicloud-express.template.vpcConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `role` | string | 否 | — | length ≥ 1 | 已有执行角色 ARN。 |
| `vpcId` | string | 否 | — | length ≥ 1 | 已有 VPC ID。 |
| `securityGroupId` | string | 否 | — | length ≥ 1 | 已有安全组 ID。 |
| `vSwitchIds` | 数组，每项为 string | 否 | — | 每项：length ≥ 1 | 已有交换机 ID 列表。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-template-resourcetags-items"></a>

## sandbox.<name> — provider=alicloud-express.template.resourceTags[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `key` | string | 是 | — | length ≥ 1 | 标签键。 |
| `value` | string | 是 | — | — | 标签值。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes"></a>

## sandbox.<name> — provider=alicloud-express.volumes

每个映射值：object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties)


<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `agenticBucketVolumeConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticbucketvolumeconfig) | 否 | — | — | AgenticBucket 存储后端。 |
| `agenticFSVolumeConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticfsvolumeconfig) | 否 | — | — | AgenticFS 存储后端。 |
| `juiceFSVolumeConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-juicefsvolumeconfig) | 否 | — | — | JuiceFS 存储后端。 |
| `ossVolumeConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-ossvolumeconfig) | 否 | — | — | OSS 存储后端。 |
| `mountConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig) | 否 | — | — | 原生卷挂载网络与角色。 |
| `volumeName` | string | 否 | — | length ≥ 1 | 原生卷名称，Team 内唯一。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticbucketvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.agenticBucketVolumeConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `agenticBucket` | string | 否 | — | length ≥ 1 | AgenticBucket 名称。 |
| `bucketName` | string | 否 | — | length ≥ 1 | 已有 OSS Bucket 名称。 |
| `bucketPath` | string | 否 | — | length ≥ 1 | Bucket 内路径前缀。 |
| `endpoint` | string | 否 | — | length ≥ 1 | 存储服务接入点。 |
| `readOnly` | boolean / [原生表达式](#type-expression) | 否 | — | — | 以只读方式挂载存储。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-agenticfsvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.agenticFSVolumeConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `groupID` | integer / [原生表达式](#type-expression) | 否 | — | — | 挂载组 ID。 |
| `userID` | integer / [原生表达式](#type-expression) | 否 | — | — | 挂载用户 ID。 |
| `serverAddr` | string | 否 | — | length ≥ 1 | 存储服务或接入点地址。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-juicefsvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.juiceFSVolumeConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `baseURL` | string | 否 | — | length ≥ 1 | 存储接入点基础 URL。 |
| `remoteDir` | string | 否 | — | length ≥ 1 | 远程目录。 |
| `token` | string | 否 | — | length ≥ 1 | 通过引用提供的内部令牌。 |
| `volumeName` | string | 否 | — | length ≥ 1 | 原生卷名称，Team 内唯一。 |
| `args` | 数组，每项为 string | 否 | — | — | 原生步骤参数。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-ossvolumeconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.ossVolumeConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `bucketName` | string | 否 | — | length ≥ 1 | 已有 OSS Bucket 名称。 |
| `bucketPath` | string | 否 | — | length ≥ 1 | Bucket 内路径前缀。 |
| `endpoint` | string | 否 | — | length ≥ 1 | 存储服务接入点。 |
| `readOnly` | boolean / [原生表达式](#type-expression) | 否 | — | — | 以只读方式挂载存储。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.mountConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `role` | string | 否 | — | length ≥ 1 | 已有执行角色 ARN。 |
| `vpcConfig` | object · [子字段](#field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig-vpcconfig) | 否 | — | — | 已有 FC 网络配置，结构见托管应用参考。 |

- 不接受其他字段。

<a id="field-sandbox-additionalproperties-allof-0-then-volumes-additionalproperties-props-mountconfig-vpcconfig"></a>

## sandbox.<name> — provider=alicloud-express.volumes.<name>.props.mountConfig.vpcConfig

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `vpcId` | string | 否 | — | length ≥ 1 | 已有 VPC ID。 |
| `securityGroupId` | string | 否 | — | length ≥ 1 | 已有安全组 ID。 |
| `vSwitchIds` | 数组，每项为 string | 否 | — | 每项：length ≥ 1 | 已有交换机 ID 列表。 |

- 不接受其他字段。

<a id="field-serving"></a>

## serving

每个映射值：object · [子字段](#field-serving-additionalproperties)

映射键：完整ASCII标识


<a id="field-serving-additionalproperties"></a>

## serving.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `component` | string | 是 | — | 完整ASCII标识 | 实际原生组件标识与版本。 |
| `props` | object · [子字段](#field-serving-additionalproperties-props) | 是 | — | — | 原生组件定义的 props，不复制 FC schema。 |
| `actions` | object · [子字段](#field-serving-additionalproperties-actions) | 否 | — | — | 原生 Devs 生命周期 actions。 |

- 不接受其他字段。

<a id="field-serving-additionalproperties-props"></a>

## serving.<name>.props

对象内部字段由原生组件或对应使用参考定义。


<a id="field-serving-additionalproperties-actions"></a>

## serving.<name>.actions

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `pre-deploy` | 数组，每项为 object · [子字段](#field-serving-additionalproperties-actions-pre-deploy-items) | 否 | — | — | 资源部署前本机动作。 |
| `success-deploy` | 数组，每项为 object · [子字段](#field-serving-additionalproperties-actions-success-deploy-items) | 否 | — | — | 资源就绪后本机动作。 |
| `fail-deploy` | 数组，每项为 object · [子字段](#field-serving-additionalproperties-actions-fail-deploy-items) | 否 | — | — | 部署失败时本机动作。 |
| `complete-deploy` | 数组，每项为 object · [子字段](#field-serving-additionalproperties-actions-complete-deploy-items) | 否 | — | — | 部署结束时本机动作。 |

- 不接受其他字段。

<a id="field-serving-additionalproperties-actions-pre-deploy-items"></a>

## serving.<name>.actions.pre-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-serving-additionalproperties-actions-success-deploy-items"></a>

## serving.<name>.actions.success-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-serving-additionalproperties-actions-fail-deploy-items"></a>

## serving.<name>.actions.fail-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="field-serving-additionalproperties-actions-complete-deploy-items"></a>

## serving.<name>.actions.complete-deploy[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `run` | string | 否 | — | length ≥ 1 | 部署发起端 Shell 命令。 |
| `component` | string | 否 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `path` | string | 否 | — | length ≥ 1 | 自定义域名的根路由。 |

- 不接受其他字段。
- 以下字段仅选一个：`run`; `component`.

<a id="type-expression"></a>

## expression

string; 原生 `${...}`，由 Devs 求值
