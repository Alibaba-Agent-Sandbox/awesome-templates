# qm

## 做什么

在一台自有极速版计算机运行未修改的 QM0.1.0 原版 Pi harness 与工具上下文，并通过自编后端接入真实 Agent Sandbox Node.js HTTP SDK。编码使用显式批准的兼容模型。 不启动或验证完整多人核心、web/Slack、Postgres 持久化、cron 或订阅功能，不使用原版 Docker 默认后端。本模板是原版库的有界集成；没有冒充名为 qm 的系统命令，也没有替换原版代理引擎。 [固定原版源码](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255)。

## 技术栈

阿里云generation2 basev0.0.49/Linuxx64/Python3.13；原版Node24.16.0归档/可执行文件SHA256固定，完整QM源码0.1.0、不可变提交和原版npm完整性锁。原版Node SDK0.1.0源码90b5187dca84fca78d75d3045896482540641c72使用原锁和build脚本编译；2026-10-21查询npm0.1.0返回404，不假设已发布。server源码e2cb27e24fde0a67112f82b8d44af463445a5d1a。[Dockerfile](Dockerfile)、[来源](upstream.json)、[QM锁](package-lock.json)、[SDK锁](sdk-package-lock.json)、[设计](../docs/design/qm.md)。

## 解决的问题

在不嵌套Docker、不向模型工具传入云凭据的情况下运行真实QM导出功能和SDK后端。原版包/源码/导入检查、真实SDK往返和模型任务分别验收。Node SDK仅提供沙箱内HTTP客户端；外层创建/销毁由调用方Python Sandbox SDK负责。每个后端绑定一个调用方项目；attach/provision不会新建另一台云机器。

## 快速开始（CLI）

按[原生CLI说明](../docs/platform-steps.zh-CN.md)配置授权的极速版访问，并替换全部尖括号占位符。不可变公共COPY准备前先发布准确提交。按下面代码为生成manifest设置独占名称；等待官方READY后再创建。同一无需模型任务供CLI、SDK及HTTP调用。CLI0.4.1通过 `abx --native run` 使用 `abx run`。

```bash
python scripts/prepare_steps.py qm --output /tmp/qm-steps-<unique-run> \
  --asset-transport parallel --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/qm-steps-<unique-run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "qm-<unique-run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/qm-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> qm_sdk_smoke
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```
规范验证入口：`ABX='abx --native' python scripts/run_steps_e2e.py qm --sandbox-create sdk --http --asset-transport oss`，负责独占资源、恢复和私有OSS缓存清理。手动调用者清理自身已知ID；steps通过不代表Docker镜像部署通过。

## 快速开始（Python SDK）

按[配套源码说明](../docs/python-client-installation.md)安装发行包 `agent-sandbox-client`，导入 `agent_sandbox`。示例只做语法检查，不构成提供方通过；本示例负责清理，默认命令服务token为空。任何端口如配置Bearer，都使用 `sb.server_at(9000,token=...)`（或实际端口）的命令客户端并关闭。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        result = await sb.run("qm_sdk_smoke", timeout=200)
        assert result == "Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK"
    finally:
        await sb.kill()

asyncio.run(main())
```
真实编码前在命令服务启动时配置QM_MODEL_API_KEY/QM_MODEL_BASE_URL/QM_MODEL，检查qm_setup_check后调用 `await sb.run("qm", prompt="Fix existing source and preserve its tests", cwd="project", command_timeout=300, timeout=380)`。直接返回结构化缓冲结果、最终回复与计数，不流式输出或导出推理。原生终态以及独立文件/测试检查同时通过，才接受编码结论。

[预热服务配置](../docs/runtime-environment.zh-CN.md)：后续create环境变量不会重配已有9000进程。单独启动9010服务时显式配置QM_SANDBOX_BASE_URL=http://127.0.0.1:9010及匹配SDK Bearer。通过sb.server_at(port,token=...)调用并关闭客户端；停止、排空/取消本次服务流，最后销毁外层沙箱。禁止把密钥/token值放入argv。

## 快速开始（HTTP POST）

ABX_SERVER_URL来自 `sb.network.get_url(9000)`；命令服务Bearer、可选提供方入口头、SDK Bearer和模型凭据分别配置。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/qm_sdk_smoke" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```
HTTP200返回 `{"result":"Original QM tools and actual Agent Sandbox SDK round trip/owned cleanup OK"}`。参数为直接JSON对象，不包args。缺失/未知/类型错误400，鉴权401，未知命令404，语义/原生异常500及 `{error,type}`。执行结果分别保留真实code和timedOut；命令自己exit124不会自动算超时。断开HTTP请求不取消有界原生操作。

## 命令参考

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| qm_version | none | Actual checked `{qm_version:"0.1.0",node_version:"24.16.0",sdk_version:"0.1.0"}`; no model/network |
| qm_native_check | none | `{original_qm_harness:true,original_tool_context:true,actual_sdk_client:true}`; real original imports, no backend/model request |
| qm_setup_check | none | Read-only mode `original-qm-agent-sandbox-sdk-slice`, SDK base/token presence and optional model presence booleans; never secret values |
| qm_sdk_smoke | none | Exact string after original QM tool context/actual SDK file+execution+listing+removal round trip and owned fixture absence; no model; private transient files |
| qm | prompt: required nonempty string1..32768UTF8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300, booleans rejected | Original final reply as stdout, actual source/qm/node/sdk identities, native_completed, original model_calls/native_tool_calls/native_tool_results, completed sdk_calls, stopped/pending_approvals and exit_code0; native tool file changes persist |

调用串行化，重叠报忙。原生stdout/stderr各256KiB，匿名请求256KiB。每次SDK工具命令显式使用Bash、最小环境、私有HOME，返回流各64KiB，执行1..120秒，并用进程组/nonce/pidfd清理后代。后端exec另有最多50秒启动/清理，模型封装40秒；客户端至少多给80秒。库层文件最大1MiB；公开命名文本写入/读取32KiB；目录最多1024名称且JSON不超过32KiB。超限报错，不静默截断。解析后的文件路径须在选定项目内；SDK助手再次拒绝路径/符号链接越界及删除根目录。shell具有外层用户OS权限，cwd并非额外OS隔离。

## 配置

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/app | Existing caller project root, captured at startup |
| QM_SANDBOX_BASE_URL | http://127.0.0.1:9000 | Actual SDK data-plane server on the same owned computer; literal local HTTP only, no userinfo/query/fragment/path |
| QM_SANDBOX_TOKEN | empty; optional | SDK server's independent Bearer token; falls back to ABX_SERVER_TOKEN for the default same server |
| ABX_SERVER_TOKEN | empty; optional | Command server's independent Bearer credential |
| QM_MODEL_API_KEY | empty; required for qm | Approved compatible model key; anonymous stdin/private native memory |
| QM_MODEL_BASE_URL | empty; required for qm | Explicit HTTPS compatible Chat Completions API base; local HTTP for authored fixtures only; no userinfo/query/fragment, max2048characters |
| QM_MODEL | empty; required for qm | Actual model identifier, max200allowed characters; no default vendor fallback |

commands.py加载时捕获配置；存在性不证明连通。SDK token最长8192且不含CR/LF/NUL，模型key最长8192且无控制字符。Node工作进程仅通过匿名stdin接收配置，不在环境继承模型/云/GitHub凭据；工具Bash另用最小环境和私有HOME，同一用户仍有OS访问权限。每次调用删除私有HOME/缓存/配置/模型目录/临时workspace镜像。返回文本脱敏密钥、base、token及JSON转义值。原版QM禁用Pi默认内置工具，使用原版QM工具；不加载扩展、skill、上下文文件或子会话，只批准execute/files读写，不启动委派、Slack/邮件或控制服务。调用方项目/产物保留到调用方删除或销毁外层沙箱。

## 资源

声明2vCPU/2048MB/Linuxx64、9000端口、强制8GiB rootfs预算；无需Docker/KVM/GPU/额外root能力。实际依赖、任务可行性和峰值内存等待带日期验收，声明内存不是负载测量。需下载包/源码及访问SDK服务；编码另需授权模型工具调用和出口。不声明其他提供方或完整多人持久化。

## 已验证

尚未记录任何通过的提供方测试。

自编SDK/HTTP/路径/进程/终态fixture仅是前置检查，不是原版QM、极速版或模型通过。当前镜像、原生SDK往返、SDK创建Express、完整HTTP及独立清理待完成；qm另需真实原生编码。[带日期研究](../.agents/evidence/verify/2026-10-21-qm-native-research.md)。

## 二次开发

```bash
python -m pytest -q qm-sandbox/test_runtime.py qm-sandbox/test_commands.py
python -m pytest -q qm/test_terminal.py
python scripts/check_template.py qm --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py qm --sandbox-create sdk --http --asset-transport oss
```

SDK HTTP fixture先执行 `python qm-sandbox/prepare_sdk_tests.py /tmp/qm-sdk-tests-<unique-run>`，再执行 `ABX_QM_TEST_SDK_ENTRY=/tmp/qm-sdk-tests-<unique-run>/dist/index.js node --test qm-sandbox/test_adapter.mjs`。SDK单元fixture可用Node>=20，真实QM使用固定Node24.16.0；未显式构建原版SDK时这些fixture会跳过，不构成原生/后端通过。

以原版源码/锁/声明为准。原生实际验收仅在新建自有一次性云端目标执行；源码模式明确跳过缺失原生环境，不默认调用模型。编码控制器要求原版模型/工具正计数和完成的SDK操作、原测试字节不变、源文件修改、新报告/精确nonce、返回后原始3项加4项隐藏用例及新ACK。标记、配置或版本本身不算通过。后端验收另检查原版工具上下文/真实SDK及独立目标字节和清理。

## 贡献

遵守[贡献规范](../CONTRIBUTING.zh-CN.md)、项目/文档规范和源码绑定证据规则，双语README、设计、目录、API、不可变版本及工程索引一同维护，保留全部失败和独立恢复记录。

## 问题反馈

跟踪[Issue44](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/44)。模板/适配问题在本仓库；Python客户端/服务端到[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，Node HTTP客户端到[nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues)，CLI到[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附脱敏版本/层级，不附密钥、私有端点、原始提示或推理。

## 许可证

自编封装/后端Apache-2.0，原版QM为MIT，Node和SDK保留原许可证及NOTICE。[发行说明](UPSTREAM-NOTICE.md)、[QM许可证](UPSTREAM-QM-LICENSE)。镜像保留完整声明，不改变第三方许可证。
