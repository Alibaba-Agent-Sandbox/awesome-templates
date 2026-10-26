# appworld

[English](README.md)

## 做什么

运行原版 AppWorld0.1.3.post1 训练任务、API、SQLite 状态及原版评分器，配合自编的兼容模型 API 连接层。连接层提供原版 API 文档和真实 API 调用；不声称复现论文基线。结果保持上游加密 bundle 格式。范围是单个训练任务，不代表排行榜成绩。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Alibaba generation2 basev0.0.49、Linuxx64/Python3.13；独立[完整哈希依赖锁](requirements.lock)、原版 appworld0.1.3.post1 wheel 和34,280,074字节加密数据。已发布服务端包，user 运行、9000端口。[Dockerfile](Dockerfile)、[来源记录](upstream.json)、[设计](../docs/design/appworld.md)。可分发镜像内受保护源码和数据保持加密。



Python3.13 兼容：原版 SQLAlchemy1.4.54 无对应 wheel，使用其未修改、SHA256 固定的源码及上游 DISABLE_SQLALCHEMY_CEXT=1 纯 Python 构建。先用独立哈希锁安装 setuptools80.9.0/wheel0.45.1，再 --no-build-isolation 安装完整固定依赖，不替换为不兼容的 SQLAlchemy2。

## 解决的问题

无需嵌套 Docker 或在操作者环境安装基准，即可在一次性沙箱评估真实 AppWorld 任务。[固定上游](https://github.com/StonyBrookNLP/appworld/tree/66ad8099e12188ece0d3fe45e661dbc01880813b)支持直接 Python 执行，Docker 可选。保留原版执行安全默认值，评分使用原版 evaluator。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Chat Completions**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export APPWORLD_MODEL_API_KEY='<your-model-api-key>'
export APPWORLD_MODEL_BASE_URL='https://model.example.invalid/v1'
export APPWORLD_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=750
abx template launch Alibaba-Agent-Sandbox/awesome-templates//appworld --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" appworld_run --json-args '{"max_steps":30,"command_timeout":600}'
```

返回选中的训练任务、原生 `score`、`success` 和加密的 `artifact_path`；模型不保证解题成功。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

在完成上述 CLI 启动、设置 `SANDBOX_ID` 后，将以下保存为 `use_template.py`，执行 `python3 use_template.py`。它连接同一实例，不另建沙箱。对于需要输入的示例，先在本机准备上面的文件。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=750
        )
        try:
            result = await client.commands.run('appworld_run', max_steps=30, command_timeout=600)
            print(result)
            Path('appworld-result.zip').write_bytes(await sb.files.read_bytes(result['artifact_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/appworld_run`

```json
{
  "max_steps": 30,
  "command_timeout": 600
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 750 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

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

此入口调用兼容 Chat Completions API，base 包含供应商要求的前缀（常见 `/v1`），不要额外添加 `/chat/completions`。模型和端点须支持 Chat Completions 的 tool calls。

| 变量 | 要求/默认值 | 用途 |
| --- | --- | --- |
| APPWORLD_MODEL_API_KEY | 模型必需；空 | 兼容地址密钥，通过匿名 stdin 进入私有内存，不进入 argv/子进程环境 |
| APPWORLD_MODEL_BASE_URL | 模型必需；空 | 显式 HTTPS；自编测试仅允许回环 HTTP；无用户信息/查询/片段，最长2048字符 |
| APPWORLD_MODEL | 模型必需；空 | 实际模型标识，1..200安全字符 |
| WORKSPACE | /home/user/workspace | 已存在结果根目录，服务启动读取 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

密钥最长8192字符，不含 CR/LF/NUL。原生子进程不继承操作者云/GitHub/模型令牌；配置由匿名 stdin 传入。保留 AppWorld 原版安全默认值。连接层校验原版 app/API 范围，将 JSON 参数转为 Python 字面量，不接受可执行模型 Python。每回复最多执行16工具调用；17..64项批次逐项反馈拒绝且不执行API，更多则失败。每任务空choices最多3次，回复8192token，最多160原生交互，每交互50API调用，原生执行30秒，模型 HTTP60秒且 SDK 不重试，工具输出有界、模型上下文最大1MiB。

工作目录为 `/home/user/workspace`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 artifact_path
abx download "$SANDBOX_ID" '<returned-path>' ./appworld-result.zip
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB，Linux x64、端口 9000。不需要 Docker、KVM 或 GPU。每次调用初始化私有运行环境；模型任务需要外部兼容服务及网络。仅支持训练任务切片，未提供全 benchmark 排行榜含义。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/appworld.md)。

## 问题反馈

[Issue70](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70) 跟踪本模板。模板/控制器问题提交此仓库，客户端/服务端问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

自编包装代码及上游公开源码 Apache-2.0。受保护的 AppWorld app/任务/API/数据及衍生物另有加密公开分发要求；见[上游声明](UPSTREAM-NOTICE.md)和原版 bundle 许可证。不要公开解密源码、数据库、任务细节或轨迹。不暗示论文基线或排行榜成绩。
