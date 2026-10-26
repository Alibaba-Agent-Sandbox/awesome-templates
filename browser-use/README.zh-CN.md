# Browser-use

[English](README.md)

## 做什么

在私有本地Chromium上运行真实browser-use0.13.11 Agent，读取文本DOM、操作网页，返回实际PNG、最终URL和结果。它补充无需模型的Playwright原语，不使用Browser Use Cloud或远程浏览器。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

FC v0.0.49、generation2、非root user、Linux x86_64、Python3.13。[requirements.lock](requirements.lock)固定browser-use0.13.11及全部传递依赖版本/SHA256，由[requirements.in](requirements.in)通过uv0.11.28生成。该版本依赖CDP-use，并非Python Playwright；显式Playwright1.58.0安装器选定Chromium1208/Google Chrome for Testing145.0.7632.6，--no-shell不再安装第二份headless shell。

## 解决的问题

让真实模型在自有沙箱使用本地浏览器，独立取回产物并清理进程。use_vision=false文本DOM不要求视觉模型。本模板不接云浏览器账号/计费、扩展或任意本地文件/shell操作。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Chat Completions**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export BROWSER_USE_API_KEY='<your-model-api-key>'
export BROWSER_USE_BASE_URL='https://model.example.invalid/v1'
export BROWSER_USE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//browser-use --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" browser_use --json-args '{"task":"Read the heading of this page and return it.","url":"https://example.com","max_steps":8,"command_timeout":300}'
```

返回 Agent 结果、`done`、`success` 和新的 `screenshot_path`。请检查完成标志，不能仅凭文本判断成功。

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
            result = await client.commands.run('browser_use', task='Read the heading of this page and return it.', url='https://example.com', max_steps=8, command_timeout=300)
            print(result)
            Path('browser-use.png').write_bytes(await sb.files.read_bytes(result['screenshot_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/browser_use`

```json
{
  "task": "Read the heading of this page and return it.",
  "url": "https://example.com",
  "max_steps": 8,
  "command_timeout": 300
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| browser_use_version | none | actual installed0.13.11 string |
| browser_use_setup_check | none | installed/version/browser_installed and api_key_set/base_url_set/model_set flags |
| browser_use_self_test | none | BROWSER_USE_NATIVE_OK only after native CDP navigation/title/PNG and cleanup; no model |
| browser_use | task:str required, nonempty/no NUL/max256KiB UTF-8; url:str="", HTTP(S)/no userinfo/max8192 UTF-8 bytes; max_steps:int=8,1..20; command_timeout:int=300,1..900seconds | {result:str,final_url:str,screenshot_path:str,bytes:int,steps:int,done:bool,success:bool} |

真实worker显式使用Agent/BrowserSession/BrowserProfile/ChatOpenAI，不自动连接云。通过原生add_schema_to_system_prompt=true、dont_force_structured_output=true把schema放入系统提示并由库解析文本JSON，不要求模型服务支持特定strict response_format。

仅15项原生动作：done/navigate/click/input/scroll/wait/go_back/switch/close/find_text/find_elements/search_page/select_dropdown/dropdown_options/send_keys。构造Agent前后检查工具表。禁用文件/shell/evaluate/extract/upload/PDF/search及Agent截图动作；完成时封装自行获取真实截图。产物名随机且不能由调用者指定/覆盖。PNG16MiB为渲染后限制。最终URL直接查询实际目标信息，模型自述不是独立验证。

## 配置

此入口调用兼容 Chat Completions API，base 包含供应商要求的前缀（常见 `/v1`），不要额外添加 `/chat/completions`。此入口使用文本 DOM，模型需要按原生提示返回结构化 JSON；不使用 Browser Use Cloud 账号。

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| BROWSER_USE_API_KEY | model turns | empty | explicitly supplied compatible-model credential, not Browser Use Cloud |
| BROWSER_USE_BASE_URL | model turns | empty | HTTP(S) model API; no userinfo/query/fragment |
| BROWSER_USE_MODEL | model turns | empty | explicit compatible chat model ID |
| BROWSER_USE_PYTHON | no | /opt/browser-use/bin/python | hash-locked native environment; actual0.13.11 checked |
| PLAYWRIGHT_BROWSERS_PATH | no | /opt/playwright | installed Chromium1208 cache |
| BROWSER_USE_BROWSER_BINARY | diagnostics | Chromium1208/chrome-linux64/chrome | executable override; actual145.0.7632.6 still required |
| WORKSPACE | no | /home/user/app | owned root for new browser-use-artifacts PNGs |
| ABX_SERVER_TOKEN | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

模型配置只通过私有文件stdin进入，不继承到Chromium。每次独立HOME/XDG/profile/原生文件目录，关闭遥测/云同步/默认扩展/use_cloud，不导入调用者账号或已保存浏览器。CDP启动显式请求回环地址，只公布命令9000。此容器模板显式设置chromium_sandbox=false，使用自有沙箱提供OS隔离，不依赖Docker自动探测。浏览器和模型仍有沙箱用户权限及网络，这不是额外OS隔离。结果和PNG可能含网页私密信息；返回字符串替换模型密钥/地址的完整值。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 screenshot_path
abx download "$SANDBOX_ID" '<returned-path>' ./browser-use.png
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU/2048MB，命令端口9000。--disable-dev-shm-usage避免依赖大/dev/shm。每个服务只运行一个浏览器任务，并发重操作返回busy500。max_steps1..20，每步最多3动作；模型90秒/零重试/4096 token，原生动作30秒/步骤120秒/LLM100秒门禁；外层1..900秒另加有限清理。每路输出256KiB，PNG16MiB渲染后检查。正常成功/失败/期限均删除私有浏览器配置/文件并清理自有进程，PNG交由调用者保存。服务突然丢失或同用户恶意代码仍以删除自有沙箱为最终边界。镜像根文件系统8GiB构建门禁。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/browser-use.md)。

## 问题反馈

[Issue51](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/51)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码[Apache-2.0](../LICENSE)。Browser-use为MIT，保留[上游原许可](upstream-LICENSE)。保留Playwright发行的未修改Chrome for Testing二进制及捆绑许可/声明；Playwright为Apache-2.0。哈希固定依赖保留各自安装声明，不能把整个镜像统一重标Apache-2.0。不包含模型权重或云服务账号。

原生步骤失败时最多返回20条错误摘要，配置的模型密钥和端点精确脱敏后，每条限制为1024个 UTF-8 字节。
