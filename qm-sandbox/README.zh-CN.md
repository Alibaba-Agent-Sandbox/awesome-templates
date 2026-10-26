# qm-sandbox

[English](README.md)

## 做什么

为一台已拥有的极速版计算机实现原版 QM Sandbox 接口后端，使用真实 Agent Sandbox Node.js HTTP SDK。原版 QM 工具上下文完成真实文件和命令操作，无需模型账号。 不启动或验证完整多人核心、web/Slack、Postgres 持久化、cron 或订阅功能，不使用原版 Docker 默认后端。本模板是原版库的有界集成；没有冒充名为 qm 的系统命令，也没有替换原版代理引擎。 [固定原版源码](https://github.com/yc-software/qm/tree/deef9b8b1e2b85bd4166dd833604bb31bcb8e255)。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云generation2 basev0.0.49/Linuxx64/Python3.13；原版Node24.16.0归档/可执行文件SHA256固定，完整QM源码0.1.0、不可变提交和原版npm完整性锁。原版Node SDK0.1.0源码63d7cd8ece221b9f968eef51eeb932ea334c90d3使用原锁和build脚本编译；npm 包尚未发布；镜像从已审核的不可变 SDK 源码构建。已发布服务端包。[Dockerfile](Dockerfile)、[来源](upstream.json)、[QM锁](package-lock.json)、[SDK锁](sdk-package-lock.json)、[设计](../docs/design/qm-sandbox.md)。

## 解决的问题

在不嵌套 Docker、不向工具进程传入云凭据的情况下运行 QM 原始工具和 SDK 后端。Node SDK仅提供沙箱内HTTP客户端；外层创建/销毁由调用方Python Sandbox SDK负责。每个后端绑定一个调用方项目；attach/provision不会新建另一台云机器。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//qm-sandbox --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" qm_sandbox_file --json-args '{"action":"write","path":"note.txt","text":"Hello from QM tools\n"}'
```

返回 `result: true`、`sdk_calls` 和 `original_qm_tools: true`；文本写入 `note.txt`。

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
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('qm_sandbox_file', action='write', path='note.txt', text='Hello from QM tools\n')
            print(result)
            Path('note.txt').write_bytes(await sb.files.read_bytes('/home/user/app/note.txt'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/qm_sandbox_file`

```json
{
  "action": "write",
  "path": "note.txt",
  "text": "Hello from QM tools\n"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

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

这是 QM 原始工具与 SDK 后端切片，不运行模型；无需模型 endpoint、API Key 或 QM 登录。`QM_SANDBOX_BASE_URL` 是同一个沙箱内的 SDK 数据面地址，不是模型地址。

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| WORKSPACE | /home/user/app | Existing caller project root, captured at startup |
| QM_SANDBOX_BASE_URL | http://127.0.0.1:9000 | Actual SDK data-plane server on the same owned computer; literal local HTTP only, no userinfo/query/fragment/path |
| QM_SANDBOX_TOKEN | empty; optional | SDK server's independent Bearer token; falls back to ABX_SERVER_TOKEN for the default same server |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

commands.py加载时捕获配置；存在性不证明连通。SDK token最长8192且不含CR/LF/NUL，模型key最长8192且无控制字符。Node工作进程仅通过匿名stdin接收配置，不在环境继承模型/云/GitHub凭据；工具Bash另用最小环境和私有HOME，同一用户仍有OS访问权限。每次调用删除私有HOME/缓存/配置/模型目录/临时workspace镜像。返回文本脱敏密钥、base、token及JSON转义值。原版QM禁用Pi默认内置工具，使用原版QM工具；不加载扩展、skill、上下文文件或子会话，只批准execute/files读写，不启动委派、Slack/邮件或控制服务。调用方项目/产物保留到调用方删除或销毁外层沙箱。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx download "$SANDBOX_ID" /home/user/app/note.txt ./note.txt
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB，Linux x64，命令端口 9000。运行时不需要嵌套 Docker、KVM、GPU 或 root 能力；镜像构建限制 rootfs 为 8 GiB。本地 SDK 服务必须可达，工作区与产物随外层沙箱生命周期保留。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/qm-sandbox.md)。

## 问题反馈

跟踪[Issue45](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/45)。模板/适配问题在本仓库；Python客户端/服务端到[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，Node HTTP客户端到[nodejs-sdk](https://github.com/Alibaba-Agent-Sandbox/nodejs-sdk/issues)，CLI到[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附脱敏版本/层级，不附密钥、私有端点、原始提示或推理。

## 许可证

自编封装/后端Apache-2.0，原版QM为MIT，Node和SDK保留原许可证及NOTICE。[发行说明](UPSTREAM-NOTICE.md)、[QM许可证](UPSTREAM-QM-LICENSE)。镜像保留完整声明，不改变第三方许可证。
