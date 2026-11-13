# 托管 Agent 应用

[English](managed-agent-applications.md)

[Agents API 模板](../agents-api/README.zh-CN.md)通过一个 Gateway 提供逻辑 Session、文件上传、Agent 任务和结果下载。每个活跃 Session 独占一个运行模型、CLI 和工具的 Sandbox。此 YAML v1 配方需要匹配的开发版 CLI。

## 资源与生命周期

[template.yaml](../agents-api/template.yaml)声明一个命名 Sandbox 模板和三个原生 FC Serving 资源：Gateway、Worker、Dispatcher。Gateway 接收业务请求，Dispatcher 将任务投递到 Session 对应的 Worker 版本，Worker 创建和清理动态 Sandbox。部署准备可复用模板和函数，不创建常驻 Sandbox 实例。

Worker 创建实例时注入独立应用令牌和模型环境，再启动 managed bridge；模板快照准备阶段不提前启动需要认证的 bridge。后续轮次复用 Session 的原生线程和工作区。Close 释放计算并保留已提交结果；Delete 删除公开数据并继续完成清理。不确定的执行或删除需要协调处理。

本配方的 `vars.policy.instance.timeout` 和 `vars.policy.sessions.maxLifetimeSeconds` 都为 3600 秒，且必须一致。空闲期限为 900 秒，轮次/工具预算为 600/60 秒。部署脚本检查预算适合实例寿命，并限制一个 Session 同时执行一轮。其他接收和存储预算见同一个 policy 对象；这些是模板选择，不是 YAML 保留字段。

## 配置

资源值放在 `template.yaml`。原生 `${env('NAME')}` 表达式读取私有项目 `.env` 或进程值，进程值优先。`registry.yaml.parameters` 引导初始化，后续本地运行不依赖它；`vars` 键名由模板作者选择。

| 配置 | 用途与来源 |
| --- | --- |
| `vars.region` | 复用于 `sandbox.agent.template.region` 和各原生 FC `props.region`。 |
| `vars.adapter` | qwen-code 或 codex，与已授权模型服务匹配。 |
| `AGENTS_SERVER_IMAGE` | 可写 OCI 仓库及本次 Server 构建唯一 tag。 |
| `ABX_MANAGED_DATABASE_URL` | 已有 PostgreSQL URL，三个 FC 角色都能访问。 |
| `AGENTS_DATABASE_CA_PEM` | 可选数据库 CA 证书 PEM，保留主机名验证。 |
| `serving.<role>.props.vpcConfig` | 该函数可选的已有 VPC、交换机、安全组 ID。 |
| `SANDBOX_API_KEY`、`SANDBOX_BASE_URL`、`SANDBOX_DOMAIN`、`SANDBOX_REGION` | 匹配的 Sandbox 平台凭据和地址，供 Worker/Dispatcher 使用。 |
| `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` | 已授权模型 Key、HTTPS 地址和模型 ID。仅 Worker 接收 Key 并提供给 Session Sandbox。 |
| `AGENTS_FC_ROLE_ARN` | 已有 FC 执行角色，包含调用私有 Worker 的权限。 |

首次部署生成不同的业务及内部令牌，在本机私有存储中复用。客户端使用 `.abx/agents-api/credentials.json` 中的 `businessKey`，不要分享 `internalToken`。可选的 `AGENTS_BUSINESS_KEY` 和 `AGENTS_INTERNAL_TOKEN` 进程覆盖不复制到凭据存储，各不少于 32 字符且必须不同。内部令牌轮换需要协调迁移保留的版本。

每个 Sandbox 的 `ABX_SERVER_TOKEN` 由运行时生成，与云账号、平台、模型和业务凭据不同，无需手工申请云控制台 Key。同 UID 的 Agent 工具可读取明确注入的模型 Key；数据库和 Server 认证凭据不进入 Sandbox。

## 构建、部署与更新

按模板 README 激活 Python 虚拟环境并安装 `scripts/requirements.txt`。配方使用原生 `serverless-devs/fc3@0.1.26` 构建和部署动作，保留 cpu、memorySize、timeout、role、logConfig、vpcConfig 等原生 props。Guest 和 Server 分别通过各自 Dockerfile 定义镜像。

```bash
abx deploy . --plan
abx deploy . --yes
python scripts/release.py status
```

Plan 预览资源准备，不执行动作。Deploy 运行模板的准备和发布动作；候选 Gateway 必须完成真实模型的两轮文件任务，才切换稳定 `prod` 别名。任务可能产生模型和 Sandbox 费用。新 Dispatcher 在候选任务开始前接管新旧 Worker 路由。

发布成功后，业务 endpoint 位于 `.abx/agents-api/release.json`。更新时选择新的 Server 镜像 tag，再执行 deploy。已有 Session 保留原 Worker revision；历史 Worker 保留到应用删除，本模板不自动清理旧版本。

发布失败或结果不确定时，保留本机记录，先查看阶段和状态再操作。候选任务失败后，新 Dispatcher 继续服务旧 Session。本配方不提供不确定发布的自动回滚和自动续跑。计划、Schema 校验或本地测试不代表托管发布已成功。

## 访问与清理

稳定入口使用 FC 测试 URL。配方不创建自定义域名、DNS、数据库或网络资源。已有自定义域名另行指向 Gateway `prod` 别名，并实际验证数据库、仓库、Sandbox 和模型服务的网络可达性。

业务客户端使用 endpoint 和业务 Key 通过 HTTP 调用；项目没有专用 Gateway 客户端 SDK。见 [API 参考](managed-agents-api.zh-CN.md)及模板完整 Python HTTP、curl 示例。Capabilities 列出 OpenAI 风格子集及托管扩展；路径相似不意味着 OpenAI 托管 harness 或任意 SDK 兼容。

关闭 Session，下载结果并删除不需要的公开数据，再用带排空检查的脚本删除应用：

```bash
python scripts/release.py destroy
```

脚本核对当前 Dispatcher 和数据库身份，停止新请求接入，只有活跃 Session、待完成清理和不确定资源都为零时，才调用 `abx delete agents-api --yes`。排空未完成时保留资源，处理剩余任务后重试。若部分删除已移除 Dispatcher，应独立确认业务清理后再完成资源删除。已有数据库、网络、角色、域名、镜像 tag 及保留的数据库历史仍由你管理。
