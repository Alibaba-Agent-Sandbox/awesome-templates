# Tau2 零售基准

[English](README.md)

## 做什么

运行原版 Tau2 v1.0.1 文本零售任务，由原生智能体与用户模拟器共同完成，返回原版评分及脱敏轨迹，再通过不携带模型密钥的原版评估器独立严格重放。支持范围为零售子集；其他领域、语音、知识任务及需要自然语言裁判的任务均拒绝。单个任务成绩不能代表完整基准。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

MIT 许可的[固定原版源码](https://github.com/sierra-research/tau2-bench/tree/fc0055dc4e0a316c3f83133267fbd6faaa770992)、Python3.13、隔离且按哈希锁定的依赖、LiteLLM1.81.11 与 Agent Sandbox server。
查看 [Dockerfile](Dockerfile)、[requirements.lock](requirements.lock)、[upstream.json](upstream.json) 和[设计](../docs/design/tau2-bench.md)。官方源码归档为92,081,935字节；固定 SHA256 记录在 `upstream.json`，来自控制端测量，并非上游发布的校验和。固定 `PYTHONPATH=/opt/tau2/src` 从源码运行，不声称 PyPI 已发布 Tau2 包。

[原始冻结导出](requirements.upstream.lock)完整保留平台标记；`python tau2-bench/select_lock.py` 选择 Linux CPython3.13 对应条目，不修改版本和哈希，镜像强制检查 Python 配置。

另由[兼容锁文件](requirements.compat.lock)明确新增 PSF-2.0 的 `audioop-lts==0.2.2`：Python3.13 已移除 `audioop`，但此版上游文本任务也会导入它；保留[许可证](AUDIOOP-LICENSE.txt)。

选取数据同时包含原版共享用户模拟器指引和零售领域数据，不使用替代指引。

## 解决的问题

为原版任务提供有界执行、原生评估、可单独下载的轨迹和独立严格重放。智能体与用户模拟器均使用明确配置的模型服务。

`tau2_run(domain)` 按需求返回 `score` 和 `log_path`，`artifact_path` 是同一份所属脱敏轨迹路径，同时提供字节数和 SHA256。

文本通信采用原生默认 `enforce_communication_protocol=False`，完成状态和原生重放结果分别报告。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Chat Completions**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export TAU2_MODEL_API_KEY='<your-model-api-key>'
export TAU2_MODEL_BASE_URL='https://model.example.invalid/v1'
export TAU2_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=750
abx template launch Alibaba-Agent-Sandbox/awesome-templates//tau2-bench --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" tau2_run --json-args '{"domain":"retail","task_id":"0","max_steps":30,"command_timeout":600}'
```

返回原生 `score`、终止原因和脱敏轨迹 `artifact_path`；Agent 与模拟用户均会产生模型调用费用，不能保证奖励为 1。

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
            result = await client.commands.run('tau2_run', domain='retail', task_id='0', max_steps=30, command_timeout=600)
            print(result)
            Path('tau2-trajectory.json').write_bytes(await sb.files.read_bytes(result['artifact_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/tau2_run`

```json
{
  "domain": "retail",
  "task_id": "0",
  "max_steps": 30,
  "command_timeout": 600
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 750 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| 命令 | 参数 | 返回及副作用 |
| --- | --- | --- |
| `tau2_version` | 无 | 原版源码版本、提交、零售领域及原版任务数；不调用模型。 |
| `tau2_setup_check` | 无 | 配置是否存在的布尔值及 `native-retail-agent-and-user` 模式；不返回密钥、不调用模型。 |
| `tau2_run` | `domain: str="retail"`（仅零售）；`task_id: str="0"`（1–3位十进制数字且任务须存在）；`max_steps: int=30`（5–60，拒绝 bool）；`command_timeout: int=600` 秒（30–900，拒绝 bool） | 原生 `score`、`log_path`/`artifact_path` 同路径、终止原因、消息及工具次数、源码提交、轨迹字节数/SHA256；调用两个模型并写入独占私有结果目录。含非空自然语言断言的任务在模型调用前拒绝。 |
| `tau2_verify_artifact` | 必填 `path: str`（最多4096个 UTF-8 字节，工作区内已有常规轨迹文件，1–8MiB）；`task_id: str="0"` | 无模型密钥的原版严格重放、匹配评分和轨迹 SHA256；不修改文件；期限120秒。 |

版本命令期限60秒，输入走匿名 stdin，每条输出流限256KiB。原版进程使用串行化独占进程组、nonce 和 pidfd 清理。超时、非零退出、未完成轨迹、错误源码/任务、评分不一致或畸形输出均失败。

## 配置

此入口调用兼容 Chat Completions API，base 包含供应商要求的前缀（常见 `/v1`），不要额外添加 `/chat/completions`。Agent 和模拟用户共用此模型设置，端点须支持工具调用。

| 变量 | 必填/默认 | 含义 |
| --- | --- | --- |
| `TAU2_MODEL_API_KEY` | 运行任务必填；空 | 模型密钥，最多8192字符，禁止 CR/LF/NUL。 |
| `TAU2_MODEL_BASE_URL` | 运行任务必填；空 | 显式 HTTPS 兼容接口，最多2048字符；仅本地字面地址允许 HTTP 合成测试；禁止 userinfo、query、fragment。 |
| `TAU2_MODEL` | 运行任务必填；空 | 明确模型标识，最多200个允许的标识字符。 |
| `WORKSPACE` | `/home/user/workspace` | 已有且可写的结果根目录。 |
| `ABX_SERVER_TOKEN` | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在服务导入时捕获。双方原生模型均设置相同 `openai/` 模型和显式 `api_base`，密钥只经匿名 stdin 进入私有工作进程环境，不写入 argv 或配置文件。排除操作端云凭据、GitHub 凭据和二进制覆盖变量。所有路径清理私有 HOME、临时原生日志和子进程；成功轨迹归调用者管理，失败的部分结果删除。轨迹的键和值递归移除实际密钥和接口字符串；重放不携带模型密钥。禁用遥测及模型价格网络刷新；未知价格返回零不代表免费或准确账单。

工作目录为 `/home/user/workspace`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 artifact_path
abx download "$SANDBOX_ID" '<returned-path>' ./tau2-trajectory.json
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048MiB RAM、9000端口、非 root `user`；无需 Docker daemon、KVM、GPU 或额外权限。根文件系统约10GiB，构建拒绝超过8GiB。92MB 源归档仅保留约38MB 源码/零售数据及依赖。智能体与模拟用户都产生模型费用；步骤5–60，每次模型请求60秒超时，命令期限30–900秒。成功轨迹不超过8MiB，保留于独占 `abx_tau2_result_<nonce>` 目录；读取后只删除本次目录，并销毁、独立确认自己的外层云资源不存在。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/tau2-bench.md)。

## 问题反馈

[模板需求59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59)。
模板问题：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)；
SDK/server：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)；
CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装为 [Apache-2.0](../LICENSE)，原版 Tau2 源码与选取的零售数据保留 [MIT 声明](UPSTREAM-LICENSE.md)。分发时保留上游声明。
Python3.13 兼容依赖保留 [audioop-lts PSF-2.0 许可证](AUDIOOP-LICENSE.txt)。
