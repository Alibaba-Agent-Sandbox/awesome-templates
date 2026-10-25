# appworld

[English](README.md)

## 做什么

运行原版 AppWorld0.1.3.post1 训练任务、API、SQLite 状态及原版评分器，配合自编的兼容模型 API 连接层。连接层提供原版 API 文档和真实 API 调用；不声称复现论文基线。结果保持上游加密 bundle 格式。范围是单个训练任务，不代表排行榜成绩。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

Alibaba generation2 basev0.0.49、Linuxx64/Python3.13；独立[完整哈希依赖锁](requirements.lock)、原版 appworld0.1.3.post1 wheel 和34,280,074字节加密数据。服务端源码 e2cb27e24fde0a67112f82b8d44af463445a5d1a，user 运行、9000端口。[Dockerfile](Dockerfile)、[来源记录](upstream.json)、[设计](../docs/design/appworld.md)。可分发镜像内受保护源码和数据保持加密。



Python3.13 兼容：原版 SQLAlchemy1.4.54 无对应 wheel，使用其未修改、SHA256 固定的源码及上游 DISABLE_SQLALCHEMY_CEXT=1 纯 Python 构建。先用独立哈希锁安装 setuptools80.9.0/wheel0.45.1，再 --no-build-isolation 安装完整固定依赖，不替换为不兼容的 SQLAlchemy2。

## 解决的问题

无需嵌套 Docker 或在操作者环境安装基准，即可在一次性沙箱评估真实 AppWorld 任务。[固定上游](https://github.com/StonyBrookNLP/appworld/tree/66ad8099e12188ece0d3fe45e661dbc01880813b)支持直接 Python 执行，Docker 可选。保留原版执行安全默认值，评分使用原版 evaluator。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./appworld --yes
abx run <sandbox-id> appworld_native_smoke --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('appworld_native_smoke'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/appworld_native_smoke`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "original AppWorld0.1.3.post1 native API and private cleanup OK"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters / bounds | Result / effects |
| --- | --- | --- |
| appworld_version | none | native_version0.1.3.post1, source_commit, data_sha256, protected_bundles_encrypted:true; actual fixed package/data hashes, no unpack/model |
| appworld_setup_check | none | mode, base_url_set/api_key_set/model_set booleans; no network/setup |
| appworld_native_smoke | none | Exact smoke string after original training-world initialization/native API and owned private-process cleanup; no model |
| appworld_run | task:string default empty, max64 safe identifier characters; empty selects first original train task; max_steps:int1..40 default30; command_timeout:int30..900seconds default600; booleans rejected | score0.0/1.0 (all native tests), success, num_tests/pass_count, task, original native/source/data identity, model/model_steps, bridge_api_calls/native_api_calls, task_completed, artifact_path/log_path aliases, artifact_bytes/artifact_sha256/artifact_encrypted, training_task_count; owns one new result directory |
| appworld_verify_artifact | path:required workspace-contained existing encrypted file, max4096UTF8 bytes,1..64MiB; task:string default empty uses bound artifact task, otherwise original train task ID | verified:true, task, original_evaluator:true, model_credentials_used:false, score/success/num_tests/pass_count; independent original evaluator on reloaded saved databases, no model call |

原生操作串行化，重叠调用报忙。请求最大32KiB，stdout/stderr 各256KiB。成功、失败、超时或输出超限都会清理独占进程组、nonce/pidfd 后代及私有 HOME/包副本/数据/缓存。结果缓冲返回。成功加密产物位于独占0700工作目录、文件0600，调用方或销毁沙箱负责删除；失败会删除本次不完整结果目录。验证限制加密文件64MiB、ZIP4096成员、展开512MiB，拒绝越界路径、符号链接及其他实验目录。

## 配置

| 变量 | 要求/默认值 | 用途 |
| --- | --- | --- |
| APPWORLD_MODEL_API_KEY | 模型必需；空 | 兼容地址密钥，通过匿名 stdin 进入私有内存，不进入 argv/子进程环境 |
| APPWORLD_MODEL_BASE_URL | 模型必需；空 | 显式 HTTPS；自编测试仅允许回环 HTTP；无用户信息/查询/片段，最长2048字符 |
| APPWORLD_MODEL | 模型必需；空 | 实际模型标识，1..200安全字符 |
| WORKSPACE | /home/user/workspace | 已存在结果根目录，服务启动读取 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

密钥最长8192字符，不含 CR/LF/NUL。原生子进程不继承操作者云/GitHub/模型令牌；配置由匿名 stdin 传入。保留 AppWorld 原版安全默认值。连接层校验原版 app/API 范围，将 JSON 参数转为 Python 字面量，不接受可执行模型 Python。每回复最多执行16工具调用；17..64项批次逐项反馈拒绝且不执行API，更多则失败。每任务空choices最多3次，回复8192token，最多160原生交互，每交互50API调用，原生执行30秒，模型 HTTP60秒且 SDK 不重试，工具输出有界、模型上下文最大1MiB。

## 资源

声明2vCPU/2048MB、Linuxx64、9000端口，镜像根目录限制8GiB；无需 Docker/KVM/GPU。每次调用在私有环境复制并解密原版受保护内容，可分发镜像不包含解密的受保护 app/数据。实际依赖及一个原版极速版任务已通过，任务峰值内存尚未测量。模型需要已授权的兼容 Chat Completions/工具调用和网络访问；不声明其他提供方或全任务通过。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

同步维护原版 wheel、加密 bundle/数据哈希、版本、manifest 和原版评分器。公开源码 tag66ad8099e12188ece0d3fe45e661dbc01880813b 只表明版本对应，不证明 wheel 可复现构建。只开放训练任务，避免污染保留评测集。新增模型/任务/资源配置均需真实验收。结果使用原版加密格式及上游公开解密机制，不代表保密能力。

## 贡献

遵守[贡献规范](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.md)、[文档规范](../docs/documentation-standards.md)和[设计](../docs/design/appworld.md)，保留历史成功/失败收据和独立清理证据。

## 问题反馈

[Issue70](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70) 跟踪本模板。模板/控制器问题提交此仓库，客户端/服务端问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

自编包装代码及上游公开源码 Apache-2.0。受保护的 AppWorld app/任务/API/数据及衍生物另有加密公开分发要求；见[上游声明](UPSTREAM-NOTICE.md)和原版 bundle 许可证。不要公开解密源码、数据库、任务细节或轨迹。不暗示论文基线或排行榜成绩。
