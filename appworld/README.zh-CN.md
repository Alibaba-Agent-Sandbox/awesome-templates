# appworld

[English](README.md)

## 做什么

运行原版 AppWorld0.1.3.post1 训练任务、API、SQLite 状态及原版评分器，配合自编的兼容模型 API 连接层。连接层提供原版 API 文档和真实 API 调用；不声称复现论文基线。结果保持上游加密 bundle 格式。范围是单个训练任务，不代表排行榜成绩。

## 技术栈

Alibaba generation2 basev0.0.49、Linuxx64/Python3.13；独立[完整哈希依赖锁](requirements.lock)、原版 appworld0.1.3.post1 wheel 和34,280,074字节加密数据。服务端源码 e2cb27e24fde0a67112f82b8d44af463445a5d1a，user 运行、9000端口。[Dockerfile](Dockerfile)、[来源记录](upstream.json)、[设计](../docs/design/appworld.md)。可分发镜像内受保护源码和数据保持加密。



Python3.13 兼容：原版 SQLAlchemy1.4.54 无对应 wheel，使用其未修改、SHA256 固定的源码及上游 DISABLE_SQLALCHEMY_CEXT=1 纯 Python 构建。先用独立哈希锁安装 setuptools80.9.0/wheel0.45.1，再 --no-build-isolation 安装完整固定依赖，不替换为不兼容的 SQLAlchemy2。

## 解决的问题

无需嵌套 Docker 或在操作者环境安装基准，即可在一次性沙箱评估真实 AppWorld 任务。[固定上游](https://github.com/StonyBrookNLP/appworld/tree/66ad8099e12188ece0d3fe45e661dbc01880813b)支持直接 Python 执行，Docker 可选。保留原版执行安全默认值，评分使用原版 evaluator。

## 快速开始（CLI）

按[平台 steps](../docs/platform-steps.md)安装 CLI0.4.1 原生入口并配置已授权的极速版。该版本通过 `abx --native run` 使用 `abx run`。尖括号占位值替换为独占资源；不可变 COPY 需要先发布对应提交。等待官方 READY 后创建。以下无需模型的任务初始化原版世界并调用真实 API。

```bash
python scripts/prepare_steps.py appworld --output /tmp/appworld-steps-<unique-run> \
  --asset-transport parallel --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/appworld-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> appworld_native_smoke
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

完整验证：`ABX="abx --native" python scripts/run_steps_e2e.py appworld --sandbox-create sdk --http --asset-transport oss`。私有 OSS 仅缓存精确原版加密数据，并独立确认清理；steps 不能证明 Docker 镜像验收。配置模型后使用 `abx --native run <owned-sandbox-id> appworld_run --json-args '{"task":"","max_steps":40,"command_timeout":900}'`，并检查原生分数和产物。

## 快速开始（Python SDK）

按[配套源码安装](../docs/python-client-installation.md)安装 `agent-sandbox-client`。示例完成同一个无需模型的 CLI/HTTP 任务，并清理本次沙箱；已做语法检查，实际云端与模型证据见下文。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        result = await sb.run("appworld_native_smoke", timeout=150)
        assert result == "original AppWorld0.1.3.post1 native API and private cleanup OK"
    finally:
        await sb.kill()

asyncio.run(main())
```

在命令服务启动前配置 APPWORLD_MODEL_API_KEY/BASE_URL/MODEL 并检查 setup 后，可调用 `await sb.run("appworld_run", task="", max_steps=40, command_timeout=900, timeout=1000)`，用 `sb.files.read_bytes(result["artifact_path"], max_bytes=64*1024**2)` 下载加密产物，再调用 `await sb.run("appworld_verify_artifact", path=result["artifact_path"], task=result["task"], timeout=200)`。按[预热服务配置](../docs/runtime-environment.md)显式启动所需进程；创建时变量不会重配现有9000服务。单独 Bearer 服务使用 `sb.server_at(port, token=...)` 的命令客户端，并在 finally 关闭客户端、停止本次进程、排空/取消流及销毁沙箱。不要打印密钥、私有地址或解密任务内容。

## 快速开始（HTTP POST）

ABX_SERVER_URL 为 `sb.network.get_url(9000)`；可选 ABX_SERVER_TOKEN 需在服务启动前配置。按所选提供方要求同时设置网关访问头。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/appworld_native_smoke" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```

HTTP200 返回 `{"result":"original AppWorld0.1.3.post1 native API and private cleanup OK"}`。run 直接传 `{task,max_steps,command_timeout}`，verify 传 `{path,task}`，不使用 args 包装。参数缺失/类型错误400、服务端认证失败401、未知命令404、语义/执行错误500并含 `{error,type}`。未完成的原生运行失败；完成但答案错误的任务可以返回0.0。请求超时不会取消有界工作进程。

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
| ABX_SERVER_TOKEN | 可选；空 | 独立命令服务 Bearer |

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
