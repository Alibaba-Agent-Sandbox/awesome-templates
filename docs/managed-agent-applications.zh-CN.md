# 托管 Agent 应用

规范 6 描述一个稳定公开 Gateway 与每会话独占 Sandbox 的应用。Agent 的模型、工具循环和 CLI 在 Sandbox 内运行；业务调用方使用 Gateway URL 与业务凭据，Sandbox 地址和管理凭据留在内部。

封闭契约是 [template-v6.schema.json](../spec/template-v6.schema.json)。规范 5 保留既有生命周期与部署语义。应用部署必须显式执行；导入、构建或创建 Sandbox 不会部署 Server 资源或运行主机 hooks。

## 运行时与生命周期

支持的组合为：

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

私有桥接协议与 `server-core-agents` 不同。它使用 `python -m agent_sandbox.server.managed --port 9000` 启动，以自动生成的应用令牌保护能力发现和托管操作，保留只读 `/health` 就绪探测。根级 `provides.app` 声明 `protocol: agent-sandbox-managed-bridge`、`version: 1` 和端口 9000。

根级 smoke 声明桥接操作及预期，例如：

```yaml
smoke:
  - operation: health
    expect: {status: ok, protocol: agent-sandbox-managed-bridge/v1}
```

第一次输入按需分配计算，后续轮次保留同一个原生 thread 与工作区。每会话同时最多一个执行或采集中的轮次。逻辑会话、存活及不确定 Sandbox、队列和保留存储分别限额。读取状态或事件不延长空闲期；新任务必须适合 Sandbox 剩余最大寿命及采集、清理余量。

close 停止接收任务并释放计算，已提交结果按保留期可读。delete 撤下公开数据，只保留完成清理所需的内部记录。提交、重启或删除结果未知时，不自动重放，也不当作资源已不存在。

## 配置与绑定

`application.api.protocol` 为 `agent-sandbox-managed-agents/v1`。Gateway 通过能力发现说明受支持的 OpenAI 风格子集及托管扩展。不支持的 steering、工具和设置明确报错；排队新轮次不能静默冒充引导当前轮。

binding 保存引用名，不写密钥值或连接 URL，并声明允许的目标角色：

| 绑定 | 目标 | 用途与来源 |
| --- | --- | --- |
| 状态（`state.bindingRef`） | gateway、worker、dispatcher | 部署环境解析的已有 PostgreSQL 服务引用。 |
| `sandboxAccess` | worker、dispatcher | 用于生命周期和核查的已有 Sandbox 访问配置。 |
| `model` | sandbox-creation | 有权限的模型 Key、base、model 引用，仅由 Worker 解析并注入 guest。 |
| `clientAuth` | gateway | 业务认证配置；生成的令牌安全交付调用方。 |
| `internalAuth` | gateway、worker、dispatcher | 独立的私有控制身份或签名配置。 |
| 入口（`deployment.ingressBindingRef`） | deployment-publisher | 有归属记录的稳定路由、alias 或域名配置。 |

`model` 要求 `resolverRole: worker`，以及显式 `allowedEnv`，仅允许 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`CODEX_API_KEY` 的子集。云、数据库和业务认证配置不复制进 Sandbox。每会话应用 token 自动生成，不是云控制台申请的 API Key。

部署解析器检查 binding 实际值类型与归属，缺少必需值阻止发布。状态 binding 的实际值可以是 PostgreSQL URL 字符串，或 `{databaseUrl, vpcConfig?, databaseCa?}` 对象。可选 `vpcConfig` 只包含 `vpcId`、不同的 `vSwitchIds` 和 `securityGroupId`，用于三个 FC 角色的部署网络，不注入 guest。网络资源均为借用，不自动创建 NAT/路由，也不证明 endpoint 可达。可选 `databaseCa` 接受有界的纯证书 PEM 字符串、环境引用或 CLI 宿主机文件引用，保留数据库主机名验证；它仅配置 Server 信任，不进入镜像、计划、收据或 guest。CLI 内部固定数据库持久身份，用户无需手工提供该身份。同 UID 的 Agent 工具可以访问有意注入该 Sandbox 的模型凭据，但不获得 Server 控制凭据。

## Server 构建与部署

`application.deployment` 选择 `profile: fc-managed-agents`，精确的已发布 `fc3@X.Y.Z` 组件、部署 `accessRef`、地域、入口引用和 `revisionStrategy: immutable-workers-with-drain`。

Server 产物二选一：

```yaml
serverBuildRecipe:
  dockerfile: server/Dockerfile
  context: .
```

或提供带 `@sha256:<64位小写十六进制>` 的不可变 `serverImage`。构建输入限于模板上下文。CLI 构建并解析镜像后，才冻结计划和自动生成的工具链完整性锁。本 profile 不接受任意 `deployment.steps` 或另一套工作流 DSL。

profile 准备 Sandbox Template，创建 revision 专属 Worker，部署候选 Gateway/Dispatcher，验证后发布稳定入口。生产 timer 关闭期间，验证使用受限私有派发。公开 endpoint 来自实际验证的入口，不猜测组件返回字段。function-alias 与 custom-domain binding 有不同提供商要求；测试函数 URL 不等于生产域名保证。

更新时 Session 固定原 revision；旧 Worker 和兼容 Server 产物保留到会话排空。清理失败保留归属记录和可继续工作的清理路径；借用的数据库和模型服务不会自动删除。尚未参与 Apply 且归属已确认的 owned Server 构建可通过 `abx app clean-build BUILD --yes` 清理；参与 Apply 后由应用 Destroy/Retire 在引用排空后清理。借用的 Server 镜像不删除。Sandbox 构建镜像可能仍列在 `retained_build_artifacts` 中，需要显式按仓库说明清理。

## Hooks 与输出

`beforeApply`、`afterReady` 每阶段最多八个 hook，ID 全局唯一。`custom` 声明 argv、安全相对 cwd、1–900 秒期限和显式环境变量白名单。`serverless-devs` 引用 `gateway`、`worker` 或 `dispatcher`，只支持有界的 `command: info` 查询。部署和销毁属于受管理步骤，不能靠无记录的 hook 副作用实现。

输出是已验证的 `publish.outputs.endpoint` 和协议 `agent-sandbox-managed-agents/v1`。健康、语法、URL 解析和 hook 成功不替代业务任务实际完成。

## 调用与资源使用

先向 Gateway 上传输入，再引用不透明 file ID。文件在轮次边界持有会话执行权时安装进工作区。发布产物是带 turn、path、digest 身份的不可变捕获副本；删除发布副本不删除活工作区原文件。

重试受支持的创建或提交调用时复用已保存的幂等键。流重连读取已提交事件，不取消或重新启动 Agent。以具体 turn 及其已保存 items 判定结果。close 释放计算，过期前下载需保留的输出，不再需要时删除公开数据。

用户操作写入模板 README；实现审查、验证证据及确切测试版本保留在所属仓库工程记录。
