# muse

[English](README.md)

## 做什么

在一个自建Express计算机中运行官方原版Meta Muse Code1.4.11-R6667.1无头agent、原版miniswe工具与原生运行记录。编码显式选择兼容Responses模型。自编本地代理补充所选模型目录，将上游密钥留在父进程，原样转发Responses请求与流；使用原版二进制。[官方文档](https://dev.meta.ai/docs/muse-code)。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云generation2 basev0.0.49/Linuxx64/Python3.13；root所有的原版ELF384809176字节及官方SHA256，Python标准库代理/进程控制，已发布服务端包，无新增Python/Node依赖。[Dockerfile](Dockerfile)、[来源](upstream.json)、[上游声明](UPSTREAM-NOTICE.md)、[设计](../docs/design/muse.md)。模板源码许可证不重新授权原版上游文件。

## 解决的问题

通过SDK/HTTP命名命令提供原版Muse文件与工具执行，采用逐次私有配置及所有权清理。普通兼容网关没有原版CLI必需的`/muse-code/models`；本地代理补充目录，随后将原版`/responses`字节转发到明确配置的端点，不转换模型/工具协议，不回退到厂商默认账号或订阅。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Responses**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export MUSE_MODEL_API_KEY='<your-model-api-key>'
export MUSE_MODEL_BASE_URL='https://model.example.invalid/v1'
export MUSE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//muse --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" muse --json-args '{"prompt":"Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.","command_timeout":300}'
```

返回原生完成状态、模型/工具调用计数和缓冲输出；请独立读取生成的 `hello.py`。

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
            result = await client.commands.run('muse', prompt='Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.', command_timeout=300)
            print(result)
            Path('hello.py').write_bytes(await sb.files.read_bytes('/home/user/app/hello.py'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/muse`

```json
{
  "prompt": "Create hello.py in the current directory. It must print Hello from Muse. Run it and report the output.",
  "command_timeout": 300
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| 命令 | 参数 | 结果与副作用 |
| --- | --- | --- |
| muse_version | 无 | 校验原版ELF后返回`Muse Code 1.4.11 (1.4.11-R6667.1)`，不调用模型 |
| muse_native_check | 无 | 原版无头帮助对应`{original_native:true,headless_json:true,anonymous_api_key_stdin:true,no_session_log:true}`，不调用模型 |
| muse_setup_check | 无 | mode为`original-native-muse-explicit-responses`；native_present/model_key_set/model_base_set/model_set存在性标志；model_account_verified:false/provider_default_fallback:false/catalog_relay:true；不返回配置值、不访问网络 |
| muse | prompt：必填非空字符串1..32768UTF8字节、无NUL；cwd：可选字符串、默认空、最长4096字节、解析后必须是WORKSPACE内已有目录；command_timeout：整数1..600秒、默认300、拒绝布尔值 | 原版最终stdout、native_completed、真实model_calls/native_tool_results、exit_code0、原版二进制/版本/模型/协议及完成的relay_calls计数；原版工具可修改调用方项目，不返回原始轨迹 |

固定原版argv：`exec --json --api-key-stdin --provider meta --model <configured> --preset miniswe --reasoning-effort minimal --max-model-steps16 --no-session-log --disable-reminders --no-foreign-personal-context --disable-web-tools --yolo --workspace <contained-project>`。逐次私有配置包含schema_version1、endpoint_transport base_url/auth bearer和agents.execution_capacity1。原版miniswe没有可用subagent_spawn，不选择委派模型/工具树。显式信任后可能加载调用方项目指令。

完成判定要求原版模型/usage/终态记录精确关联，完成模型调用数为正，无失败/取消/子调用，最终文本非空。使用模型修改前请独立检查生成文件。代理最多32个模型请求，每请求2MiB、每响应4MiB，原版最多16模型步；原生stdout/stderr各256KiB。已发代理请求须排空后才判完成。自建关闭/进程清理最多额外50秒，SDK timeout建议至少command_timeout+80。并发模型调用返回busy。

## 配置

Muse 要求支持流式 Responses API 的模型服务，base 后由代码追加 `/responses`；只提供 `/chat/completions` 的网关不能用于这个入口。

| 变量 | 默认与要求 | 含义 |
| --- | --- | --- |
| MUSE_MODEL_API_KEY | 空；编码必需 | 明确选择的兼容端点密钥，仅留在父代理中 |
| MUSE_MODEL_BASE_URL | 空；编码必需 | 显式HTTPS Responses基址，最长2048字符，无userinfo/query/fragment；自编fixture仅可用字面loopback HTTP |
| MUSE_MODEL | 空；编码必需 | 实际上游模型标识，1..200个允许字符 |
| WORKSPACE | `/home/user/app` | 调用方已有项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

commands.py导入时捕获配置；存在标志不证明账号有效。key最长8192且无控制字符。原生进程仅通过匿名stdin取得逐次随机本地代理token。父代理只向固定授权Responses端点使用上游密钥，拒绝重定向及错误路由/token/model，不留轨迹。原版工具采用最小环境及私有HOME/缓存/配置，调用方项目产物保留。同一用户仍有OS访问权限，cwd检查和环境过滤不构成额外租户边界；`--yolo`选择自建外层沙箱作为执行边界。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx download "$SANDBOX_ID" /home/user/app/hello.py ./hello.py
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

声明2vCPU/2048MB/Linuxx64、9000端口、8GiB镜像rootfs预算，无KVM/Docker/GPU/额外权限。原版下载384.8MB；模型需授权出口。内存占用取决于任务。其他提供方、交互/保留会话恢复、voice/本地权重、MCP/plugin服务与Meta托管订阅不在本流程内。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/muse.md)。

## 问题反馈

[模板Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71)跟踪交付。[模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)分别归属对应仓库；原版Muse行为向其上游支持反馈。不附凭据或原始私有轨迹。

## 许可证

自编模板代码与文档使用[Apache-2.0](../LICENSE)。Meta原版文件条款与声明单列，见[来源说明](UPSTREAM-NOTICE.md)；不据此声明上游开源授权、厂商背书或已具备托管模型账号。
