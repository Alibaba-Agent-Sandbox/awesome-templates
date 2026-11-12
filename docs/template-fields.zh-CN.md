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
| `sandbox` | object · [子字段](#field-sandbox) | 否 | — | — | Sandbox 模板与实例设置。 |
| `deployment` | object · [子字段](#field-deployment) | 否 | — | — | 原生 Serverless Devs 项目。 |
| `application` | object · [子字段](#field-application) | 否 | — | — | 选择 Agents API 协调器。 |

- 不接受其他字段。
- 至少填写一个：`sandbox`; `deployment`.
- `application` 要求同时提供 `sandbox`, `deployment`.

<a id="field-sandbox"></a>

## sandbox

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `provider` | string | 否 | CLI/调用上下文；agents-api: alicloud-express | 完整ASCII标识 | 执行前选定的 Provider。 |
| `template` | object · [子字段](#field-sandbox-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |
| `instance` | object · [子字段](#field-sandbox-instance) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `start` | string | 否 | — | length ≥ 1 | 工作负载的一次启动命令。 |
| `ready` | string | 否 | — | length ≥ 1 | 工作负载就绪检查命令。 |
| `services` | object · [子字段](#field-sandbox-services) | 否 | — | — | 有名称的业务服务契约。 |
| `ports` | 数组，每项为 integer | 否 | — | 元素不重复; 每项：≥ 1; ≤ 65535 | 额外访问端口，不承诺监听已启动或存在特定协议。 |

- 不接受其他字段。
- [当 provider=alicloud-express](#field-sandbox-allof-0-then)
- [当 provider=opensandbox](#field-sandbox-allof-1-then)
- [当 provider=e2b](#field-sandbox-allof-2-then)
- [当 provider=cubesandbox](#field-sandbox-allof-3-then)
- [当 provider=alicloud-container](#field-sandbox-allof-4-then)

<a id="field-sandbox-template"></a>

## sandbox.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `source` | [source](#type-source) | 否 | — | — | 模板目录内的源码构建配方。 |
| `image` | string | 否 | — | length ≥ 1 | 容器镜像输入。 |
| `reference` | string | 否 | — | length ≥ 1 | 已有 Provider 原生模板 ID，不跨 Provider 转换。 |
| `aliases` | 数组，每项为 string | 否 | — | 元素不重复; 每项：length ≥ 1 | 模板查找别名。 |
| `props` | object · [子字段](#field-sandbox-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |

- 不接受其他字段。
- 以下字段仅选一个：`source`; `image`; `reference`.

<a id="field-sandbox-template-props"></a>

## sandbox.template.props

按所选 Provider 查看准备字段：

- [provider=alicloud-express](#field-sandbox-allof-0-then-template-props)
- [provider=opensandbox](#field-sandbox-allof-1-then-template-props)
- [provider=e2b](#field-sandbox-allof-2-then-template-props)
- [provider=cubesandbox](#field-sandbox-allof-3-then-template-props)
- [provider=alicloud-container](#field-sandbox-allof-4-then-template-props)


<a id="field-sandbox-instance"></a>

## sandbox.instance

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#field-sandbox-instance-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#field-sandbox-instance-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |
| `disk` | [非负整数或表达式](#type-nonnegativeintegerinput) | 否 | — | — | 实例磁盘数量，单位 MB。 |
| `gpu` | string | 否 | — | length ≥ 1 | Provider GPU 规格；OpenSandbox 要求数量字符串。 |
| `secure` | [布尔值或表达式](#type-booleaninput) | 否 | — | — | OpenSandbox 安全模式设置。 |
| `volume_mounts` | object · [子字段](#field-sandbox-instance-volume-mounts) | 否 | — | — | Guest 挂载路径到已有卷名称的映射，不创建卷。 |
| `lifecycle` | object · [子字段](#field-sandbox-instance-lifecycle) | 否 | — | — | 实例超时后的处理策略。 |
| `provider_options` | object · [子字段](#field-sandbox-instance-provider-options) | 否 | — | — | 所选 Provider 已接入的创建选项。 |

- 不接受其他字段。

<a id="field-sandbox-instance-envs"></a>

## sandbox.instance.envs

每个映射值：string


<a id="field-sandbox-instance-metadata"></a>

## sandbox.instance.metadata

每个映射值：string


<a id="field-sandbox-instance-volume-mounts"></a>

## sandbox.instance.volume_mounts

每个映射值：string

映射键：绝对挂载路径，排除系统目录


<a id="field-sandbox-instance-lifecycle"></a>

## sandbox.instance.lifecycle

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `onTimeout` | string | 是 | — | `"pause"`, `"kill"` | 超时后暂停或删除实例。 |
| `autoResume` | [布尔值或表达式](#type-booleaninput) | 否 | — | — | 自动恢复，仅适用于 onTimeout=pause。 |

- 不接受其他字段。

<a id="field-sandbox-instance-provider-options"></a>

## sandbox.instance.provider_options

[OpenSandbox 选项](#type-opensandboxoptions)


<a id="field-sandbox-services"></a>

## sandbox.services

每个映射值：[service](#type-service)

映射键：完整ASCII标识


<a id="field-sandbox-allof-0-then"></a>

## sandbox — provider=alicloud-express

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_alicloud-express](#type-instance-alicloud-express) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `template` | object · [子字段](#field-sandbox-allof-0-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |


<a id="field-sandbox-allof-0-then-template"></a>

## sandbox — provider=alicloud-express.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-allof-0-then-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-allof-0-then-template-props"></a>

## sandbox — provider=alicloud-express.template.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2` | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2048`；agents-api:4096 | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |

- 不接受其他字段。
- 项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。

<a id="field-sandbox-allof-1-then"></a>

## sandbox — provider=opensandbox

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_opensandbox](#type-instance-opensandbox) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `template` | object · [子字段](#field-sandbox-allof-1-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |


<a id="field-sandbox-allof-1-then-template"></a>

## sandbox — provider=opensandbox.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-allof-1-then-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-allof-1-then-template-props"></a>

## sandbox — provider=opensandbox.template.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2` | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2048`；agents-api:4096 | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |

- 不接受其他字段。
- 项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。

<a id="field-sandbox-allof-2-then"></a>

## sandbox — provider=e2b

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_e2b](#type-instance-e2b) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `template` | object · [子字段](#field-sandbox-allof-2-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |


<a id="field-sandbox-allof-2-then-template"></a>

## sandbox — provider=e2b.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-allof-2-then-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-allof-2-then-template-props"></a>

## sandbox — provider=e2b.template.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2` | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2048`；agents-api:4096 | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |

- 不接受其他字段。
- 项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。

<a id="field-sandbox-allof-3-then"></a>

## sandbox — provider=cubesandbox

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_cubesandbox](#type-instance-cubesandbox) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `template` | object · [子字段](#field-sandbox-allof-3-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |


<a id="field-sandbox-allof-3-then-template"></a>

## sandbox — provider=cubesandbox.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-allof-3-then-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-allof-3-then-template-props"></a>

## sandbox — provider=cubesandbox.template.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2` | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2048`；agents-api:4096 | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |

- 不接受其他字段。
- 项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。

<a id="field-sandbox-allof-4-then"></a>

## sandbox — provider=alicloud-container

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `instance` | [instance_alicloud-container](#type-instance-alicloud-container) | 否 | — | — | 实例创建设置，与模板准备分开。 |
| `template` | object · [子字段](#field-sandbox-allof-4-then-template) | 是 | — | — | 运行环境的源码、镜像或已有引用。 |


<a id="field-sandbox-allof-4-then-template"></a>

## sandbox — provider=alicloud-container.template

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `props` | object · [子字段](#field-sandbox-allof-4-then-template-props) | 否 | — | — | 所选 Provider 的准备参数，见对应条件字段。 |


<a id="field-sandbox-allof-4-then-template-props"></a>

## sandbox — provider=alicloud-container.template.props

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2` | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | `2048`；agents-api:4096 | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |

- 不接受其他字段。
- 项目准备阶段要求 memory ≥128 且为64的倍数；Express 还要求每 vCPU 对应1024–4096。原生表达式求值后检查数值；后端限制仍以 Provider 为准。

<a id="field-deployment"></a>

## deployment

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `edition` | string | 是 | — | = `"3.0.0"` | 原生 Devs 项目规范版本。 |
| `name` | string | 否 | 根 name | length ≥ 1 | 原生项目名称。 |
| `access` | string | 否 | `"default"` | length ≥ 1 | 已有 Serverless Devs 凭据别名。 |
| `vars` | object · [子字段](#field-deployment-vars) | 否 | — | — | 原生项目变量。 |
| `resources` | object · [子字段](#field-deployment-resources) | 是 | — | fields ≥ 1 | 按项目资源 ID 声明的原生组件资源。 |
| `flow` | object · [子字段](#field-deployment-flow) | 否 | — | — | 原生 Devs 执行顺序。 |
| `actions` | 原生 JSON 值 | 否 | — | — | 原生 Devs 生命周期 actions。 |
| `template` | object · [子字段](#field-deployment-template) | 否 | — | — | 原生 Devs 项目的 template 设置。 |
| `validation` | boolean | 否 | — | — | 原生项目校验设置。 |

- 不接受其他字段。

<a id="field-deployment-vars"></a>

## deployment.vars

对象内部字段由原生组件或对应使用参考定义。


<a id="field-deployment-resources"></a>

## deployment.resources

每个映射值：object · [子字段](#field-deployment-resources-additionalproperties)

映射键：完整ASCII标识


<a id="field-deployment-resources-additionalproperties"></a>

## deployment.resources.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `component` | string | 是 | — | length ≥ 1 | 实际原生组件标识与版本。 |
| `props` | [原生对象或表达式](#type-componentprops) | 是 | — | — | 原生组件定义的 props，不复制 FC schema。 |
| `actions` | 原生 JSON 值 | 否 | — | — | 原生 Devs 生命周期 actions。 |

- 不接受其他字段。

<a id="field-deployment-flow"></a>

## deployment.flow

对象内部字段由原生组件或对应使用参考定义。


<a id="field-deployment-template"></a>

## deployment.template

对象内部字段由原生组件或对应使用参考定义。


<a id="field-application"></a>

## application

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `type` | string | 是 | — | = `"agents-api"` | 应用或 hook 的声明类型。 |
| `roles` | object · [子字段](#field-application-roles) | 是 | — | — | 引用三个不同的原生 FC 资源。 |
| `server` | object · [子字段](#field-application-server) | 是 | — | — | Server 镜像源码或固定 digest 的镜像。 |
| `sessions` | object · [子字段](#field-application-sessions) | 否 | — | — | 托管 Session 准入和结果保留设置。 |
| `storage` | object · [子字段](#field-application-storage) | 否 | — | — | 文件和产物存储上限。 |
| `limits` | object · [子字段](#field-application-limits) | 否 | — | — | 运行、排队、事件和输出预算。 |
| `state` | object · [子字段](#field-application-state) | 是 | — | — | 已有持久数据库及可选连接设置。 |
| `bindings` | object · [子字段](#field-application-bindings) | 是 | — | — | 本地业务及凭据配置。 |
| `hooks` | object · [子字段](#field-application-hooks) | 否 | — | — | 可选的有界部署检查。 |

- 不接受其他字段。

<a id="field-application-roles"></a>

## application.roles

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `gateway` | string | 是 | — | length ≥ 1 | 公开 Gateway 的资源 ID。 |
| `worker` | string | 是 | — | length ≥ 1 | 私有 Worker 的资源 ID。 |
| `dispatcher` | string | 是 | — | length ≥ 1 | 私有 Dispatcher 的资源 ID。 |

- 不接受其他字段。

<a id="field-application-server"></a>

## application.server

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `source` | [recipe](#type-recipe) | 否 | — | — | 模板目录内的源码构建配方。 |
| `image` | string | 否 | — | image@sha256:64位小写十六进制 | 固定 digest 的 Server 镜像，与 source 二选一。 |

- 不接受其他字段。
- 以下字段仅选一个：`source`; `image`.

<a id="field-application-sessions"></a>

## application.sessions

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `idleTimeoutSeconds` | integer / [原生表达式](#type-expression) | 否 | `900` | 字面值：≥ 1 | Session 空闲超时秒数。 |
| `maxLogicalSessionsPerOwner` | integer / [原生表达式](#type-expression) | 否 | `100` | 字面值：≥ 1 | 每个 owner 的逻辑 Session 上限。 |
| `maxActiveSessions` | integer / [原生表达式](#type-expression) | 否 | `20` | 字面值：≥ 1 | 活跃 Session 准入上限。 |
| `maxQueuedTurnsPerSession` | integer / [原生表达式](#type-expression) | 否 | `8` | 字面值：≥ 1 | 每个 Session 的排队轮次上限。 |
| `resultRetentionSeconds` | integer / [原生表达式](#type-expression) | 否 | `86400` | 字面值：≥ 1 | 已提交结果的保留秒数。 |

- 不接受其他字段。

<a id="field-application-storage"></a>

## application.storage

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `maxFileBytes` | integer / [原生表达式](#type-expression) | 否 | `10485760` | 字面值：≥ 1 | 输入文件大小上限，单位字节。 |
| `maxArtifactBytes` | integer / [原生表达式](#type-expression) | 否 | `10485760` | 字面值：≥ 1 | 单个产物大小上限，单位字节。 |
| `maxTurnArtifactBytes` | integer / [原生表达式](#type-expression) | 否 | `10485760` | 字面值：≥ 1 | 每轮产物总字节数上限。 |
| `maxRetainedBytesPerOwner` | integer / [原生表达式](#type-expression) | 否 | `104857600` | 字面值：≥ 1 | 每个 owner 的保留总字节数上限。 |

- 不接受其他字段。

<a id="field-application-limits"></a>

## application.limits

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `maxRunSeconds` | integer / [原生表达式](#type-expression) | 否 | `600` | 字面值：≥ 1 | 运行时间预算，单位秒。 |
| `maxToolSeconds` | integer / [原生表达式](#type-expression) | 否 | `60` | 字面值：≥ 1 | 工具调用时间预算，单位秒。 |
| `maxConcurrentRuns` | integer / [原生表达式](#type-expression) | 否 | `10` | 字面值：≥ 1 | 并发运行准入预算。 |
| `maxQueuedRuns` | integer / [原生表达式](#type-expression) | 否 | `80` | 字面值：≥ 1 | 排队运行准入预算。 |
| `maxRunsPerMinute` | integer / [原生表达式](#type-expression) | 否 | `60` | 字面值：≥ 1 | 每分钟运行准入预算。 |
| `maxEventsPerRun` | integer / [原生表达式](#type-expression) | 否 | `10000` | 字面值：≥ 5 | 每次运行的事件数量上限。 |
| `maxOutputBytes` | integer / [原生表达式](#type-expression) | 否 | `8388608` | 字面值：≥ 1024 | 采集输出的字节数上限。 |
| `maxSubscribersPerSession` | integer / [原生表达式](#type-expression) | 否 | `4` | 字面值：≥ 1; ≤ 100 | 每个 Session 的并发事件订阅数上限。 |

- 不接受其他字段。

<a id="field-application-state"></a>

## application.state

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `databaseUrl` | [秘密值表达式](#type-secret) | 是 | — | — | 已有 PostgreSQL 连接 URL，仅供 Server 使用。 |
| `vpcConfig` | object · [子字段](#field-application-state-vpcconfig) | 否 | — | — | 已有 FC 网络配置，结构见托管应用参考。 |
| `databaseCa` | [秘密值表达式](#type-secret) | 否 | — | — | 可选的数据库私有 CA 证书 PEM。 |

- 不接受其他字段。

<a id="field-application-state-vpcconfig"></a>

## application.state.vpcConfig

已有网络 ID 结构见[配置与绑定](managed-agent-applications.zh-CN.md#配置与绑定)。


<a id="field-application-bindings"></a>

## application.bindings

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `sandboxAccess` | object · [子字段](#field-application-bindings-sandboxaccess) | 是 | — | — | 仅供 Server 管理 Sandbox 生命周期的配置。 |
| `model` | object · [子字段](#field-application-bindings-model) | 是 | — | — | 允许使用的模型标识或模型访问配置。 |
| `clientAuth` | object · [generate=true](#field-application-bindings-clientauth-oneof-0) / object · [显式令牌](#field-application-bindings-clientauth-oneof-1) / [原生表达式](#type-expression) | 否 | 自动生成凭据 | — | 自动生成的业务凭据或显式令牌哈希。 |
| `internalAuth` | object · [generate=true](#field-application-bindings-internalauth-oneof-0) / object · [显式令牌](#field-application-bindings-internalauth-oneof-1) / [原生表达式](#type-expression) | 否 | 自动生成凭据 | — | 独立的内部控制认证。 |
| `ingress` | object · [子字段](#field-application-bindings-ingress) | 是 | — | — | 稳定的 Gateway 别名或域名路由。 |

- 不接受其他字段。

<a id="field-application-bindings-sandboxaccess"></a>

## application.bindings.sandboxAccess

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `apiKey` | [秘密值表达式](#type-secret) | 是 | — | — | 通过引用提供的服务 API Key。 |
| `baseUrl` | string | 是 | — | length ≥ 1 | 明确的服务 API 基础 URL。 |
| `domain` | string | 是 | — | length ≥ 1 | 所选平台提供的 Sandbox 访问域名。 |
| `region` | string | 是 | — | length ≥ 1 | 与目标资源一致的地域。 |

- 不接受其他字段。

<a id="field-application-bindings-model"></a>

## application.bindings.model

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `apiKey` | [秘密值表达式](#type-secret) | 是 | — | — | 通过引用提供的服务 API Key。 |
| `baseUrl` | string | 是 | — | length ≥ 1 | 明确的服务 API 基础 URL。 |
| `model` | string | 是 | — | length ≥ 1 | 允许使用的模型标识或模型访问配置。 |
| `adapter` | string | 是 | — | `"codex"`, `"qwen-code"` | 与模型 API 对应的 Agent CLI 适配器。 |

- 不接受其他字段。

<a id="field-application-bindings-clientauth"></a>

## application.bindings.clientAuth

object · [generate=true](#field-application-bindings-clientauth-oneof-0) / object · [显式令牌](#field-application-bindings-clientauth-oneof-1) / [原生表达式](#type-expression)


<a id="field-application-bindings-clientauth-oneof-0"></a>

## application.bindings.clientAuth — generate=true

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `generate` | boolean | 是 | `true` | = `true` | 自动生成并安全复用本机凭据。 |
| `owner` | string | 否 | `"default"` | length ≥ 1 | 业务凭据所属 owner。 |

- 不接受其他字段。

<a id="field-application-bindings-clientauth-oneof-1"></a>

## application.bindings.clientAuth — 显式令牌

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `tokens` | 数组，每项为 object · [子字段](#field-application-bindings-clientauth-oneof-1-tokens-items) | 是 | — | items ≥ 1 | 显式允许的业务令牌哈希列表。 |

- 不接受其他字段。

<a id="field-application-bindings-clientauth-oneof-1-tokens-items"></a>

## application.bindings.clientAuth — 显式令牌.tokens[]

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `sha256` | string | 是 | — | 64位小写十六进制 | 业务令牌的小写 SHA256，不是令牌明文。 |
| `owner` | string | 是 | — | length ≥ 1 | 业务凭据所属 owner。 |
| `scopes` | 数组，每项为 string | 是 | — | items ≥ 1; 元素不重复; 每项：`"agents:read"`, `"agents:write"` | 允许的业务 API 权限范围。 |
| `expiresAt` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 凭据过期时间戳。 |

- 不接受其他字段。

<a id="field-application-bindings-internalauth"></a>

## application.bindings.internalAuth

object · [generate=true](#field-application-bindings-internalauth-oneof-0) / object · [显式令牌](#field-application-bindings-internalauth-oneof-1) / [原生表达式](#type-expression)


<a id="field-application-bindings-internalauth-oneof-0"></a>

## application.bindings.internalAuth — generate=true

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `generate` | boolean | 是 | `true` | = `true` | 自动生成并安全复用本机凭据。 |
| `roleArn` | string | 否 | — | length ≥ 1 | 已有 FC 执行角色，须与原生 role 声明一致。 |

- 不接受其他字段。

<a id="field-application-bindings-internalauth-oneof-1"></a>

## application.bindings.internalAuth — 显式令牌

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `token` | [秘密值表达式](#type-secret) | 是 | — | — | 通过引用提供的内部令牌。 |
| `roleArn` | string | 否 | — | length ≥ 1 | 已有 FC 执行角色，须与原生 role 声明一致。 |

- 不接受其他字段。

<a id="field-application-bindings-ingress"></a>

## application.bindings.ingress

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `kind` | string | 是 | — | `"function-alias"`, `"custom-domain"` | Gateway 入口模式。 |
| `aliasName` | string | 否 | `"prod"` | length ≥ 1 | 稳定的 FC 别名。 |
| `allowTestDomain` | boolean | 否 | — | — | 显式允许使用 FC 测试域名。 |
| `domainName` | string | 否 | — | length ≥ 1 | 配置的 HTTPS 自定义域名。 |
| `protocol` | string | 否 | — | = `"HTTPS"` | 服务协议；自定义域名入口使用 HTTPS。 |
| `path` | string | 否 | — | = `"/"` | 自定义域名的根路由。 |

- 不接受其他字段。
- [当 kind=function-alias](#field-application-bindings-ingress-allof-0-then)
- [当 kind=custom-domain](#field-application-bindings-ingress-allof-1-then)

<a id="field-application-bindings-ingress-allof-0-then"></a>

## application.bindings.ingress — kind=function-alias

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `allowTestDomain` | boolean | 是 | — | = `true` | 显式允许使用 FC 测试域名。 |

- 不得填写：`domainName`, `protocol`, `path`.

<a id="field-application-bindings-ingress-allof-1-then"></a>

## application.bindings.ingress — kind=custom-domain

- 必填的上层字段：`domainName`, `protocol`.
- 不得填写：`allowTestDomain`.

<a id="field-application-hooks"></a>

## application.hooks

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `beforeApply` | [hooks](#type-hooks) | 否 | — | — | 应用部署变更前的检查。 |
| `afterReady` | [hooks](#type-hooks) | 否 | — | — | 候选部署就绪后的检查。 |

- 不接受其他字段。

<a id="type-expression"></a>

## expression

string; 原生 `${...}`，由 Devs 求值


<a id="type-positiveintegerinput"></a>

## positiveIntegerInput

integer / [原生表达式](#type-expression)

字面值：≥ 1; ≤ 9007199254740991


<a id="type-nonnegativeintegerinput"></a>

## nonnegativeIntegerInput

integer / [原生表达式](#type-expression)

字面值：≥ 0; ≤ 9007199254740991


<a id="type-booleaninput"></a>

## booleanInput

boolean / [原生表达式](#type-expression)


<a id="type-secret"></a>

## secret

string; 原生 `${...}`，由 Devs 求值


<a id="type-componentprops"></a>

## componentProps

object · [分支 1](#type-componentprops-oneof-0) / [原生表达式](#type-expression)


<a id="type-componentprops-oneof-0"></a>

## componentProps — 分支 1

对象内部字段由原生组件或对应使用参考定义。


<a id="type-source"></a>

## source

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | 否 | `"Dockerfile"` | length ≥ 1 | 模板目录内的 Dockerfile。 |
| `context` | string | 否 | `"."` | = `"."` | 以模板目录为根的构建上下文。 |
| `profiles` | object · [子字段](#type-source-properties-profiles) | 否 | — | — | 显式选择的替代源码配方。 |

- 不接受其他字段。

<a id="type-source-properties-profiles"></a>

## source.profiles

每个映射值：object · [子字段](#type-source-properties-profiles-additionalproperties)

映射键：完整ASCII标识


<a id="type-source-properties-profiles-additionalproperties"></a>

## source.profiles.<name>

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | 否 | `"Dockerfile"` | length ≥ 1 | 模板目录内的 Dockerfile。 |
| `context` | string | 否 | `"."` | = `"."` | 以模板目录为根的构建上下文。 |

- 不接受其他字段。

<a id="type-recipe"></a>

## recipe

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `dockerfile` | string | 否 | `"Dockerfile"` | length ≥ 1 | 模板目录内的 Dockerfile。 |
| `context` | string | 否 | `"."` | = `"."` | 以模板目录为根的构建上下文。 |

- 不接受其他字段。

<a id="type-service"></a>

## service

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `protocol` | string | 是 | — | length ≥ 1 | 服务协议；自定义域名入口使用 HTTPS。 |
| `version` | integer | 是 | — | ≥ 1; ≤ 9007199254740991 | 服务协议的契约版本。 |
| `port` | integer | 是 | — | ≥ 1; ≤ 65535 | 服务访问端口。 |
| `operations` | 数组，每项为 string | 否 | empty list | 元素不重复; 每项：length ≥ 1 | 描述的服务操作，不授予权限。 |

- 不接受其他字段。

<a id="type-opensandboxoptions"></a>

## openSandboxOptions

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `entrypoint` | string | 否 | — | length ≥ 1 | OpenSandbox 容器启动命令。 |
| `ready_timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | OpenSandbox 就绪等待秒数。 |
| `network_policy` | string | 否 | — | length ≥ 1 | OpenSandbox 网络策略选择值。 |
| `platform` | string | 否 | — | `"linux/amd64"`, `"linux/arm64"`, `"windows/amd64"`, `"windows/arm64"` | 容器操作系统与架构。 |
| `secure_access` | [布尔值或表达式](#type-booleaninput) | 否 | — | — | OpenSandbox 安全访问选项。 |

- 不接受其他字段。

<a id="type-instance-alicloud-express"></a>

## instance_alicloud-express

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#type-instance-alicloud-express-properties-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#type-instance-alicloud-express-properties-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |
| `disk` | [非负整数或表达式](#type-nonnegativeintegerinput) | 否 | — | — | 实例磁盘数量，单位 MB。 |
| `gpu` | string | 否 | — | length ≥ 1 | Provider GPU 规格；OpenSandbox 要求数量字符串。 |
| `volume_mounts` | object · [子字段](#type-instance-alicloud-express-properties-volume-mounts) | 否 | — | — | Guest 挂载路径到已有卷名称的映射，不创建卷。 |
| `lifecycle` | object · [子字段](#type-instance-alicloud-express-properties-lifecycle) | 否 | — | — | 实例超时后的处理策略。 |

- 不接受其他字段。

<a id="type-instance-alicloud-express-properties-envs"></a>

## instance_alicloud-express.envs

每个映射值：string


<a id="type-instance-alicloud-express-properties-metadata"></a>

## instance_alicloud-express.metadata

每个映射值：string


<a id="type-instance-alicloud-express-properties-volume-mounts"></a>

## instance_alicloud-express.volume_mounts

每个映射值：string

映射键：绝对挂载路径，排除系统目录


<a id="type-instance-alicloud-express-properties-lifecycle"></a>

## instance_alicloud-express.lifecycle

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `onTimeout` | string | 是 | — | `"pause"`, `"kill"` | 超时后暂停或删除实例。 |
| `autoResume` | [布尔值或表达式](#type-booleaninput) | 否 | — | — | 自动恢复，仅适用于 onTimeout=pause。 |

- 不接受其他字段。

<a id="type-instance-opensandbox"></a>

## instance_opensandbox

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#type-instance-opensandbox-properties-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#type-instance-opensandbox-properties-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |
| `cpu` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 当前阶段的 vCPU 数。 |
| `memory` | [正整数或表达式](#type-positiveintegerinput) | 否 | — | — | 内存数量；Express 使用 MB，其他适配器按对应输入单位。 |
| `gpu` | string | 否 | — | length ≥ 1 | Provider GPU 规格；OpenSandbox 要求数量字符串。 |
| `secure` | [布尔值或表达式](#type-booleaninput) | 否 | — | — | OpenSandbox 安全模式设置。 |
| `provider_options` | [openSandboxOptions](#type-opensandboxoptions) | 否 | — | — | 所选 Provider 已接入的创建选项。 |

- 不接受其他字段。

<a id="type-instance-opensandbox-properties-envs"></a>

## instance_opensandbox.envs

每个映射值：string


<a id="type-instance-opensandbox-properties-metadata"></a>

## instance_opensandbox.metadata

每个映射值：string


<a id="type-instance-e2b"></a>

## instance_e2b

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#type-instance-e2b-properties-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#type-instance-e2b-properties-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |

- 不接受其他字段。

<a id="type-instance-e2b-properties-envs"></a>

## instance_e2b.envs

每个映射值：string


<a id="type-instance-e2b-properties-metadata"></a>

## instance_e2b.metadata

每个映射值：string


<a id="type-instance-cubesandbox"></a>

## instance_cubesandbox

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#type-instance-cubesandbox-properties-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#type-instance-cubesandbox-properties-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |

- 不接受其他字段。

<a id="type-instance-cubesandbox-properties-envs"></a>

## instance_cubesandbox.envs

每个映射值：string


<a id="type-instance-cubesandbox-properties-metadata"></a>

## instance_cubesandbox.metadata

每个映射值：string


<a id="type-instance-alicloud-container"></a>

## instance_alicloud-container

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `timeout` | [正整数或表达式](#type-positiveintegerinput) | 否 | 300；agents-api:3600 | — | 实例最长寿命，单位秒，最大86400。 |
| `envs` | object · [子字段](#type-instance-alicloud-container-properties-envs) | 否 | 空映射 | — | 声明的 Guest 环境变量值。 |
| `metadata` | object · [子字段](#type-instance-alicloud-container-properties-metadata) | 否 | 空映射 | — | Provider 实例元数据。 |

- 不接受其他字段。

<a id="type-instance-alicloud-container-properties-envs"></a>

## instance_alicloud-container.envs

每个映射值：string


<a id="type-instance-alicloud-container-properties-metadata"></a>

## instance_alicloud-container.metadata

每个映射值：string


<a id="type-refname"></a>

## refName

string; ASCII引用标识，1–128字符


<a id="type-relativepath"></a>

## relativePath

string; length ≥ 1; length ≤ 1024; 不越界的相对路径


<a id="type-hooks"></a>

## hooks

数组，每项为 object · [type=custom](#type-hooks-items-oneof-0) / object · [type=serverless-devs](#type-hooks-items-oneof-1); items ≤ 8


<a id="type-hooks-items"></a>

## hooks[]

object · [type=custom](#type-hooks-items-oneof-0) / object · [type=serverless-devs](#type-hooks-items-oneof-1)

- 以下字段仅选一个：`id`, `type`, `argv`, `cwd`, `timeoutSeconds`, `envAllowlist`; `id`, `type`, `step`, `command`, `timeoutSeconds`.

<a id="type-hooks-items-oneof-0"></a>

## hooks[] — type=custom

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `id` | [refName](#type-refname) | 是 | — | — | 跨阶段唯一的 hook 标识。 |
| `type` | string | 是 | — | = `"custom"` | 应用或 hook 的声明类型。 |
| `argv` | 数组，每项为 string | 是 | — | items ≥ 1; items ≤ 64; 每项：length ≥ 1; length ≤ 4096 | 可执行文件与参数，不隐式启动 shell。 |
| `cwd` | [relativePath](#type-relativepath) | 是 | — | — | 相对模板目录且不越界的工作目录。 |
| `timeoutSeconds` | integer | 是 | — | ≥ 1; ≤ 900 | hook 时间预算，单位秒。 |
| `envAllowlist` | 数组，每项为 string | 是 | — | 元素不重复; 每项：完整ASCII标识 | 允许传入此 hook 的主机变量名。 |

- 不接受其他字段。

<a id="type-hooks-items-oneof-1"></a>

## hooks[] — type=serverless-devs

| 字段 | 类型 | 必填 | 默认值 | 约束 | 用途 |
| --- | --- | --- | --- | --- | --- |
| `id` | [refName](#type-refname) | 是 | — | — | 跨阶段唯一的 hook 标识。 |
| `type` | string | 是 | — | = `"serverless-devs"` | 应用或 hook 的声明类型。 |
| `step` | string | 是 | — | `"gateway"`, `"worker"`, `"dispatcher"` | 由原生 info 命令检查的托管角色。 |
| `command` | string | 是 | — | = `"info"` | 只读的原生组件命令。 |
| `timeoutSeconds` | integer | 是 | — | ≥ 1; ≤ 900 | hook 时间预算，单位秒。 |

- 不接受其他字段。
