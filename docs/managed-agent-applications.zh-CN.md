# 托管 Agent 应用

[English](managed-agent-applications.md)

[Agents API 模板](../agents-api/README.zh-CN.md)提供稳定 Gateway，每个活跃 Session 使用独占 Sandbox，模型、CLI 与工具循环在其中运行。本分支使用 YAML v1 和匹配的开发构建；已发布 CLI0.5.10 不接受新格式。

## 运行时与生命周期

声明 `application.type: agents-api`，用 `application.roles.gateway/worker/dispatcher` 引用三个不同的原生 FC 资源。协调器补齐私有桥接启动、就绪和服务定义；作者不再重复协议、版本和 operations 常量。

首次输入分配计算，后续轮次保留同一原生 thread 和工作区。`sandbox.instance.timeout` 是唯一最长寿命，Managed 默认3600秒。`application.sessions.idleTimeoutSeconds` 默认900秒，必须小于最长寿命；轮次/工具预算默认600/60秒，必须适合实例寿命。逻辑 Session、存活 Sandbox、队列和保留存储分别限额，详见[字段全表](template-fields.zh-CN.md)。

close 释放计算并保留已提交结果；delete 撤下公开数据，同时完成清理。不确定的提交或资源删除需要协调恢复；队列新轮次不等于 steering 当前轮次。能力接口列出 OpenAI 风格子集及显式扩展，不表示实现 OpenAI 托管 harness。

## 配置与绑定

资源配置都在 [template.yaml](../agents-api/template.yaml)。`${env('NAME')}` 引用本地未提交的 `.env` 或进程环境。无须另一份 bindings JSON；Registry 提问也不是运行必填文件。

| 路径 | 取值及来源 |
| --- | --- |
| application.state.databaseUrl | 数据库管理员提供的已有 PostgreSQL URL。 |
| application.state.vpcConfig | 可选已有 vpcId、不同的 vSwitchIds 和 securityGroupId；只借用，不创建。 |
| application.state.databaseCa | 可选私有 CA 证书 PEM，使用原生表达式；保留数据库主机名验证。 |
| application.bindings.sandboxAccess | 已有平台 apiKey/baseUrl/domain/region；供 Server 管理实例。 |
| application.bindings.model | 模型 apiKey/baseUrl/model 和 codex 或 qwen-code 适配器；Worker 向 Session Sandbox 提供模型配置。 |
| application.bindings.clientAuth | 默认 generate:true，自动生成并在本机安全保留业务凭据；可显式提供支持的哈希、owner、scopes。 |
| application.bindings.internalAuth | 单独生成内部认证；执行角色权威来自一致的原生 role 字段。 |
| application.bindings.ingress | 选择支持的 Gateway alias/domain 入口；不是 Sandbox 域名。 |

Guest 应用认证令牌自动生成，与平台、云账号、模型凭据分开。额外 Sandbox env/metadata/volumes 受 Managed 所有权约束：不能覆盖系统、模型、认证变量和托管 metadata；挂载不能遮盖工作区和状态目录。协调器不支持 pause/resume 生命周期。自定义实例环境值只交给 Worker。

同 UID Agent 工具可读取明确注入的模型凭据。Server 的数据库、管理权限及业务/内部认证不属于 Guest 环境配置。计划不得暴露解析后的凭据和原生环境值。

## Server 构建与部署

Server 配方固定 SDK 开发源码提交 `1079841307f1f63253ae68fdda6e6d2d1e77e851`，Guest 保留已发布 Server0.4.0a7。源码包元信息仍为 a7，仅凭版本号不能识别 v1 运行时。

`deployment` 是原生 Serverless Devs edition3 项目。使用真实 `component: fc3@<版本>` 和原生 props；cpu、memorySize、timeout、role、logConfig、vpcConfig 的名称和单位不另造一层。三个 Managed 角色采用相同固定组件版本、地域和执行角色权威。用户填写的原生 memory4096 不被改回协调器常量。

`application.server` 在 source 配方 `{source: {dockerfile, context}}` 和 digest 固定 image 中二选一，提供真实 Server 镜像输入。协调器负责生成函数名、revision 说明、容器启动和内部控制配置。域名等额外资源及 output 依赖仍放在原生项目。

构建、部署、配置解析、持久化、版本路由与清理仍由实际运行时承接。静态检查不求值 Devs 表达式，也不证明云部署可用。普通 Sandbox 与 Serving 可独立并列声明；未接入的联合执行会在副作用前拒绝，不自动选择本协调器。

## Hooks 与输出

可选 beforeApply/afterReady hooks 为有界 custom argv/cwd/timeout/envAllowlist 或 Serverless Devs 角色 info 检查。源码初始化和普通 Sandbox 启动不执行它们。[模板](../agents-api/template.yaml)带部署后双轮业务检查，需要已说明的模型服务并可能产生费用。

协调器提供稳定 endpoint 和安全保留的客户端凭据。更新时旧 Session 继续路由原 revision；关闭 Session 后再删未使用版本。借用的数据库、网络、域名和外部镜像仍由资源拥有者管理。

## 调用与资源使用

客户端使用 HTTP，不访问私有桥接或单个 Sandbox 地址。见 [API 参考](managed-agents-api.zh-CN.md)和模板里的完整 Python HTTP/URL 示例。项目没有专用 Gateway SDK；能力接口明确支持范围，路径相似不代表任意 SDK 互操作。
