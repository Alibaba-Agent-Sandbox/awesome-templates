# qm-sandbox

## 做什么

为一台已拥有的极速版计算机实现原版 QM Sandbox 接口后端，使用真实 Agent Sandbox Node.js HTTP SDK。原版 QM 工具上下文完成真实文件和命令操作，无需模型账号。 不启动或验证完整多人核心、web/Slack、Postgres 持久化、cron 或订阅功能，不使用原版 Docker 默认后端。本模板是原版库的有界集成；没有冒充名为 qm 的系统命令，也没有替换原版代理引擎。 [固定原版源码](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255)。

## 技术栈

阿里云generation2 basev0.0.49/Linuxx64/Python3.13；原版Node24.16.0归档/可执行文件SHA256固定，完整QM源码0.1.0、不可变提交和原版npm完整性锁。原版Node SDK0.1.0源码90b5187dca84fca78d75d3045896482540641c72使用原锁和build脚本编译；2026-10-21查询npm0.1.0返回404，不假设已发布。server源码34e7e011c5569f77b7f605e65313be7498f6cf02。[Dockerfile](Dockerfile)、[来源](upstream.json)、[QM锁](package-lock.json)、[SDK锁](sdk-package-lock.json)、[设计](../docs/design/qm-sandbox.md)。

## 解决的问题

在不嵌套Docker、不向模型工具传入云凭据的情况下运行真实QM导出功能和SDK后端。原版包/源码/导入检查、真实SDK往返和模型任务分别验收。Node SDK仅提供沙箱内HTTP客户端；外层创建/销毁由调用方Python Sandbox SDK负责。每个后端绑定一个调用方项目；attach/provision不会新建另一台云机器。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./qm-sandbox --workflow application --yes
abx run <sandbox-id> qm_sandbox_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('qm_sandbox_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/qm_sandbox_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"qm_version": "0.1.0", "node_version": "24.16.0", "sdk_version": "0.1.0"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result / side effects |
| --- | --- | --- |
| qm_sandbox_version | none | Actual checked `{qm_version:"0.1.0",node_version:"24.16.0",sdk_version:"0.1.0"}`; no model/network |
| qm_sandbox_native_check | none | `{original_qm_harness:true,original_tool_context:true,actual_sdk_client:true}`; real original imports, no backend/model request |
| qm_sandbox_setup_check | none | Read-only mode `original-qm-agent-sandbox-sdk-slice`, SDK base/token presence and optional model presence booleans; never secret values |
| qm_sandbox_sdk_smoke | none | Exact string after original QM tool context/actual SDK file+execution+listing+removal round trip and owned fixture absence; no model; private transient files |
| qm_sandbox_exec | command: required nonempty string1..32768UTF8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing contained directory; command_timeout: integer1..120seconds default60, booleans rejected | Original QM `{stdout,stderr,code,timedOut}`, completed sdk_calls and original_qm_tools:true; actual bounded native execution |
| qm_sandbox_file | action: required read/write/list/remove; path: string default empty, max4096UTF8 bytes, contained resolved target; text: string default empty, max32768UTF8 bytes; cwd: existing contained string default empty/max4096bytes | `{result,sdk_calls,original_qm_tools:true}`. read returns original `{content:string|null,sourceScopeId}`; write/remove returntrue; list returns names. write/remove cannot target project root. Public read32KiB; write persists caller bytes; remove deletes only selected contained target |

调用串行化，重叠报忙。原生stdout/stderr各256KiB，匿名请求256KiB。每次SDK工具命令显式使用Bash、最小环境、私有HOME，返回流各64KiB，执行1..120秒，并用进程组/nonce/pidfd清理后代。后端exec另有最多50秒启动/清理，模型封装90秒；后端exec客户端至少多给80秒，qm至少多给130秒。库层文件最大1MiB；公开命名文本写入/读取32KiB；目录最多1024名称且JSON不超过32KiB。超限报错，不静默截断。解析后的文件路径须在选定项目内；SDK助手再次拒绝路径/符号链接越界及删除根目录。shell具有外层用户OS权限，cwd并非额外OS隔离。

## 配置

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/app | Existing caller project root, captured at startup |
| QM_SANDBOX_BASE_URL | http://127.0.0.1:9000 | Actual SDK data-plane server on the same owned computer; literal local HTTP only, no userinfo/query/fragment/path |
| QM_SANDBOX_TOKEN | empty; optional | SDK server's independent Bearer token; falls back to ABX_SERVER_TOKEN for the default same server |
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

commands.py加载时捕获配置；存在性不证明连通。SDK token最长8192且不含CR/LF/NUL，模型key最长8192且无控制字符。Node工作进程仅通过匿名stdin接收配置，不在环境继承模型/云/GitHub凭据；工具Bash另用最小环境和私有HOME，同一用户仍有OS访问权限。每次调用删除私有HOME/缓存/配置/模型目录/临时workspace镜像。返回文本脱敏密钥、base、token及JSON转义值。原版QM禁用Pi默认内置工具，使用原版QM工具；不加载扩展、skill、上下文文件或子会话，只批准execute/files读写，不启动委派、Slack/邮件或控制服务。调用方项目/产物保留到调用方删除或销毁外层沙箱。

## 资源

声明2vCPU/2048MB/Linuxx64、9000端口、强制8GiB rootfs预算；无需Docker/KVM/GPU/额外root能力。实际依赖与有界Express流程通过下方验收；未测量峰值内存，声明内存不是负载测量。需下载包/源码及访问SDK服务；编码另需授权模型工具调用和出口。不声明其他提供方或完整多人持久化。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q qm-sandbox/test_runtime.py qm-sandbox/test_commands.py
python -m pytest -q qm/test_terminal.py
python scripts/check_template.py qm-sandbox --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py qm-sandbox --sandbox-create sdk --http --asset-transport oss
```

SDK HTTP fixture先执行 `python qm-sandbox/prepare_sdk_tests.py /tmp/qm-sdk-tests-<unique-run>`，再执行 `ABX_QM_TEST_SDK_ENTRY=/tmp/qm-sdk-tests-<unique-run>/dist/index.js node --test qm-sandbox/test_adapter.mjs`。SDK单元fixture可用Node>=20，真实QM使用固定Node24.16.0；未显式构建原版SDK时这些fixture会跳过，不构成原生/后端通过。

以原版源码/锁/声明为准。原生实际验收仅在新建自有一次性云端目标执行；源码模式明确跳过缺失原生环境，不默认调用模型。编码控制器要求原版模型/工具正计数和完成的SDK操作、原测试字节不变、源文件修改、新报告/精确nonce、返回后原始3项加4项隐藏用例及新ACK。标记、配置或版本本身不算通过。后端验收另检查原版工具上下文/真实SDK及独立目标字节和清理。

## 贡献

遵守[贡献规范](../CONTRIBUTING.zh-CN.md)、项目/文档规范和源码绑定证据规则，双语README、设计、目录、API、不可变版本及工程索引一同维护，保留全部失败和独立恢复记录。

## 问题反馈

跟踪[Issue45](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/45)。模板/适配问题在本仓库；Python客户端/服务端到[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，Node HTTP客户端到[nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues)，CLI到[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附脱敏版本/层级，不附密钥、私有端点、原始提示或推理。

## 许可证

自编封装/后端Apache-2.0，原版QM为MIT，Node和SDK保留原许可证及NOTICE。[发行说明](UPSTREAM-NOTICE.md)、[QM许可证](UPSTREAM-QM-LICENSE)。镜像保留完整声明，不改变第三方许可证。
