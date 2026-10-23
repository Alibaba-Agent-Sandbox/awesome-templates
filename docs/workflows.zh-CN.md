# 模板工作流与验证

模板提供软件和应用服务，Provider 提供沙箱操作与端点解析，CLI/SDK 提供特定协议客户端。工作流显式描述贯穿这些层的完整调用路径。[English](workflows.md)。

## 当前机器契约

所有源码及应用清单使用 `spec_version: 4`、`workflow_contract_version: 1`，目录索引使用 `schema_version: 2`。旧 schema 及机器字段 `capabilities`、`tested_on`、`providers` 明确拒绝，不保留兼容模式。

规范 schema 位于 [template-v4.schema.json](../spec/template-v4.schema.json)。[共享操作契约](../spec/contracts/workflow-v1.json)、[验收 profiles](../spec/contracts/verification-profiles.json) 和[收据 schema](../spec/contracts/receipt.schema.json) 是 [Python 契约归属仓库](https://github.com/Alibaba-Agent-Sandbox/python-sdk/tree/main/contracts)的离线副本。锁文件绑定来源提交与内容摘要；通过 `scripts/sync_workflow_contracts.py` 同步，不手改副本。

| 字段 | 含义 |
| --- | --- |
| `provides` | 命名服务的精确协议、版本、端口和操作；普通 Python 不表示具备解释器协议 |
| `workflows` | 命名完整路径，明确输入种类、启动策略、绑定、选中操作及附加要求 |
| `default_workflow` | 唯一默认工作流 ID，即使只有一条路径也必须显式声明 |
| `binding` | 传输、端点来源、调用位置和认证受众；host 与 guest 是不同路径 |
| `required_operations` | 只能增加共享已知操作，不能删掉推导出的创建、删除、准备、启动或端点要求 |

应用工作流选择已提供服务及其中一个操作。Exec 工作流选择 `exec.run` 或 `exec.stream`。解释器工作流选择精确代码操作，例如无状态 `code.execute`、持久默认上下文 `code.default-context.execute` 或 `code.context.execute`。上下文创建、删除和实时流都是独立操作；缓冲结束后的回调不算实时流。

源码输入需要准备；OCI 镜像不是 E2B、Cube 或容器版的原生模板 ID。托管输入绑定其声明的 Provider。产生副作用前检查 Provider 接受的输入种类和启动方式。`startup: exec` 需要显式启动命令和 exec；`entrypoint` 需要平台真实支持，不能暗中替换为 exec。外部服务有独立绑定，不由此获得云生命周期能力。

## 部署拓扑

可选 `application` 保留外部/沙箱内 runtime、网关、部署 adapter、hooks、durable state、bindings 与 limits。部署 hooks 是主机部署动作，不在模板检查、导入、镜像准备或沙箱启动时执行。[本地](examples/application-local/template.yaml)及[外部](examples/application-external/template.yaml)示例均使用新工作流 schema，并保留原拓扑。

## 规划与执行

规划器按选中路径和真实消费入口判断：CLI、Python Provider、独立 ServerClient 或原生 SDK。平台原生能力不证明项目 adapter 或语言桥接已实现。应用 HTTP 不依赖统一解释器；解释器失败不得静默改为 shell 脚本。

静态结果区分满足、不支持和未知。配置、认证、网络、runtime 就绪与协议故障分别记录。执行 payload 前必须通过本地检查解决本阶段必需未知项。目录页面无法检查访问者的凭据或部署。

源码准备保留 Dockerfile 的 FROM、USER、COPY、ENTRYPOINT；占位符未解析时检查失败。执行快照先绑定源码、有效配置和 Provider 代码，后续修改使计划失效。平台 API key、网关头与服务 token 分离。端点拼接保留代理前缀和查询参数，拒绝重定向及匿名重试。

推送、注册和创建前持久写入资源 intent，响应后记录 ID。未知响应先对账，不盲重试。仅删除本轮拥有的资源。需人工删除的镜像或模板属于残留，不能宣称完全清理。

## 证据与项目认证

每份收据绑定 workflow、binding、消费入口及版本、契约/profile 摘要、源码/清单/构建/产物/Provider 身份、时间、检查 ID 和清理。可更新的模板 ID 不能单独证明不可变产物。源码镜像 guest 测试不能认证 host HTTP、统一 CLI launch 或 Python Provider 调用。

规范 profile 有稳定必需检查。源码应用需准备、创建、启动、协议、操作、端点和独立清理。缺项、失败或必需 SKIP 均不能通过。作者只能增加检查，不能削弱最小集合。模型和外部服务范围分别报告。

作者报告、本地可复现报告、项目认可 CI 证据分开。仅独立认证且由维护者认可的 workflow/runner/revision/artifact 来源可推导项目验证。手写 PASS、`cleanup_verified: true`、runner 名称或伪造 hash 不能获取信任；模板不能自行扩大可信 runner 列表。

历史收据保持不可变及原范围，不转换 schema，也不随默认工作流指针转移。当前 README 不把旧提供方通过表当新工作流认证。托管目录 `historical_evidence` 仅链接原报告，不承诺当前支持。

Provider 的 Beta/Stable 成熟度仍由维护者独立判断。缺少统一解释器操作表示该接口尚未适配，不能据此断言模板 Python 或应用服务不能运行。

## 检查

按 `scripts/requirements-spec.txt` 固定版本安装依赖，运行 `scripts/test_spec_tools.py`、`scripts/check_template.py --all`、`scripts/check_managed_catalog.py`、工作流回归和 `scripts/check_docs.py`。这些只是本地检查。真实后端声明还需精确路径实测及独立清理确认；schema 更新本身不会认证任何当前模板。

## 显式构建方案

源码可声明 `build_profiles.<id>: {dockerfile: Dockerfile.<id>, context: "."}`。
调用方通过 `--build-profile <id>` 明确选择，不根据 Provider 名称推断。默认 Express
构建文件保持平台基础镜像及其契约，独立方案可采用摘要固定的其他基础镜像，同时
保持非 root 执行及运行时依赖固定。所有选中文件均进入不可变源码/构建身份；Provider
保留 FROM、USER、COPY 与 ENTRYPOINT 的原始字节。`python-hello` 的 `portable` 是
首个显式方案。声明方案或通过源码检查，不等于镜像/原生后端已经验收。
