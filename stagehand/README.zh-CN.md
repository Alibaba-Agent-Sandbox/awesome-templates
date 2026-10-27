# stagehand

[English](README.md)

## 做什么

使用真实 Node.js `@browserbasehq/stagehand@4.3.0` SDK、随包浏览器扩展和私有本地 Chromium。每次有界调用执行一条上游 `act` 指令，可选原生 `extract` 提取 `{text: string}`，并生成新 PNG。这里只提供本地浏览器切片，不承诺 Browserbase 托管会话、持久登录、完整自主规划或任意提取 schema。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Alibaba generation2 base v0.0.49、SHA256 固定的 Node24.16.0、npm integrity 锁定的 Stagehand4.3.0/Zod4.4.3，以及明确披露、精确源码校验的连接参数补丁、Playwright1.58.0 Chromium1208/145.0.7632.6、Python3.13，已发布服务端包。以非 root user 运行，目录 `/home/user/app`、端口9000。[Dockerfile](Dockerfile)、[锁文件](package-lock.json)、[设计](../docs/design/stagehand.md)。

## 解决的问题

通过 Agent Sandbox 命名命令执行真实 Stagehand 语义浏览器动作，无需 Browserbase 账号。固定4.3.0的 ModelConfig 不接受自定义 base URL；使用上游支持的 ClientLLM 回调，将结构化文本／图片请求交给显式配置的 OpenAI 兼容 Chat Completions 端点。DOM 解释、选择器、浏览器动作和提取仍由真实 SDK／扩展完成，不安装替代 agent 或假 CLI。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Chat Completions**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export STAGEHAND_API_KEY='<your-model-api-key>'
export STAGEHAND_BASE_URL='https://model.example.invalid/v1'
export STAGEHAND_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//stagehand --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" stagehand --json-args '{"task":"Click the More information link.","url":"https://example.com","extract_instruction":"Return the visible heading.","command_timeout":180}'
```

返回原生 `action`、`extracted`、最终 URL 和新的 `screenshot_path`；请检查 `action.success`，模型可能未完成操作。

浏览器使用沙箱内的新私有 profile，不会导入本机登录或 cookies。需要登录的网站应在相应远端浏览器会话中处理；browser-use/Stagehand 的单次调用结束即删除私有会话，不提供账号会话持久化承诺。示例访问公网，需要沙箱能够出网。

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
            result = await client.commands.run('stagehand', task='Click the More information link.', url='https://example.com', extract_instruction='Return the visible heading.', command_timeout=180)
            print(result)
            Path('stagehand.png').write_bytes(await sb.files.read_bytes(result['screenshot_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/stagehand`

```json
{
  "task": "Click the More information link.",
  "url": "https://example.com",
  "extract_instruction": "Return the visible heading.",
  "command_timeout": 180
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| stagehand_version | 无 | 实际 SDK 版本 `4.3.0`，不启动浏览器／模型 |
| stagehand_setup_check | 无 | 仅 `api_key_set`／`base_url_set`／`model_set` 布尔值、mode、`browserbase_account_required:false`，无网络／秘密 |
| stagehand_self_test | 无 | `STAGEHAND_NATIVE_OK`；全新私有离线浏览器／扩展、标题、PNG 和清理；60秒期限 |
| stagehand | `task`：必填非空字符串；`url`：必填 HTTP(S)，不含用户信息／控制符／空白；`extract_instruction`：可选字符串，默认空；`command_timeout`：整数1..600秒，默认180 | 一次原生动作，可选文本提取、新 PNG；每次私有浏览器 |

task／提取指令各最多32768 UTF-8字节，URL最多8192。结果含 `version`、`sdk_sha256`、`title`、`final_url`、`action:{success,message,actionDescription,actions}`、`extracted:null`或`{text}`、`model_calls`（最多8）、`screenshot_path`、`png_bytes`。产物为 WORKSPACE 下 `stagehand-artifacts/<random>.png`，最多8MiB；用 `sb.files.read_bytes` 读取，使用后只删除返回的自有路径，不覆盖原文件。操作串行，并发直接报 busy。stdout／stderr 各限256KiB，省略上游私有错误；非零退出、超时或无法确认清理均失败。

## 配置

此入口调用兼容 Chat Completions API，base 包含供应商要求的前缀（常见 `/v1`），不要额外添加 `/chat/completions`。模型须能返回符合 JSON schema 的结构化结果，并支持原生流程实际发送的图像内容。

| 环境变量 | 必需／默认 | 含义 |
| --- | --- | --- |
| STAGEHAND_API_KEY | 模型必需，空 | 授权兼容模型端点密钥，不是 Browserbase token |
| STAGEHAND_BASE_URL | 模型必需，空 | HTTPS API base，包含实际 API 前缀，追加 `/chat/completions`；仅本地开发可用 literal localhost HTTP；无用户信息／query／fragment |
| STAGEHAND_MODEL | 模型必需，空 | 实际模型名，最多200个允许的标识字符 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| WORKSPACE | `/home/user/app` | 已存在产物根目录 |

上游 ClientLLM 结构化请求支持文本和图片，必须完整返回 JSON-schema 结果；请求最多2MiB、响应1MiB，每次推理60秒，不自动重定向、重试或切换提供方。配置在服务 import 时读取。模型秘密只经匿名 stdin 内存传入 Node，不写文件、不进 argv／浏览器环境。浏览器只继承选定运行时／证书变量以及全新私有 HOME／cache／profile。明确在外层一次性沙箱中关闭 Chromium 内层 sandbox；这不构成租户安全边界。页面能访问沙箱可达网络，命令调用者需要受信任且认证。


固定兼容配置：SDK4.3.0 的 local connect schema 接受 extensionId，但工厂未转发。[patch_sdk.py](patch_sdk.py) 强制校验原始源码 SHA25638ec56a2a1af1fb72c3e361a66b256def8e3665cca527e0d337f8a76a8308bd1，只改一处转发。自有 Chrome 只预加载原 npm 包随附、未修改的扩展，观察真实 service-worker ID，再使用原生 localBrowser.connect／Stagehand.create／act／extract。运行时与独立控制器强制校验补丁后 SDK SHA256bdf3cd62126c1529e8a889cae17fd098303e24e962e491a4b20786de72c369e0。这是明确披露的上游补丁发行配置。失败诊断仅返回允许的阶段／HTTP状态／调用次数，不返回上游响应正文、私有端点或密钥。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 screenshot_path
abx download "$SANDBOX_ID" '<returned-path>' ./stagehand.png
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU、4096MB、端口9000、Express约10GiB rootfs。沙箱内不需要 Docker／KVM／GPU，镜像校验8GiB rootfs预算。需要本地浏览器／扩展以及兼容结构化输出的模型。无需、也未验证 Browserbase 云服务／缓存／托管浏览器。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/stagehand.md)。

## 问题反馈

[模板 Issue68](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/68)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 与 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不附凭据或私有日志。

## 许可证

包装代码：[Apache-2.0](../LICENSE)。Stagehand 和 Zod：MIT；保留 [Stagehand 上游许可](UPSTREAM-LICENSE.md)。Chromium／Node 和依赖保持原发行包许可与声明；不暗示 SaaS 源码或账号授权。


## 验证入口

必选业务验证：`E2E_REQUIRE_LLM=1` 对已经启动并配置好的公开应用提交独立 nonce 页面任务，随后独立检查实际页面状态与下载 PNG；不启动第二个命令服务器，也不把模型 Key 复制给 host 控制器。原生 SDK 模型脚本仍可作为独立借用实例的检查。
