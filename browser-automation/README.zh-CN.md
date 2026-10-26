# browser-automation

[English](README.md)

## 做什么

Python 的 browse/scrape/fill_form 每次独立创建浏览器；原生MCP调用有意共享一个自有浏览器会话，直到停止或空闲关闭。mcp_stop删除其私有配置和输出。

用无头 Chromium 导航、保存 PNG 截图、提取正文和链接、填写表单。
每个命名命令独立创建并关闭浏览器，并发请求不共享 cookie、DOM 或表单值。
填表时内部校验输入值，只返回成功填写数量，不提交表单。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云 runtime 基础镜像（默认 `v0.0.49`，Python 3.13）、Playwright `1.58.0`
与其匹配的 Chromium revision，以及 Dockerfile 中精确提交钉住的
`agent-sandbox-server`。浏览器加 `--disable-dev-shm-usage`，适配极速版 64 MB
共享内存。开放命名命令、文件与进程 API；不启用可选 `/browser/*` 原语端点。

## 解决的问题

为 Agent 提供可复现的浏览器操作与可下载产物，不需要 Docker、KVM、桌面、
模型密钥或持久化浏览器会话。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//browser-automation --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" browse --json-args '{"url":"data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>","action":"extract"}'
```

返回 `action: extract`、`title: Invoice`，以及包含 `Total: 51.30` 的可见文本。

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
            result = await client.commands.run('browse', url='data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>', action='extract')
            print(result)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/browse`

```json
{
  "url": "data:text/html,<title>Invoice</title><h1>Total: 51.30</h1>",
  "action": "extract"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

所有命令通过 `POST /commands/<name>` 调用，返回 `{"result": ...}`。
命令完成后整体返回，不流式输出。

| 命令 | 参数（类型；必填/默认；范围） | 返回 |
|---|---|---|
| `browse` | `url`：字符串，必填；`action`：字符串，默认 `screenshot`，枚举 `screenshot`/`extract`/`links`/`full`；`timeout_s`：整数，默认30，1–120 | 总有 `action`、`title`；截图加 PNG 绝对路径 `path`；正文加 `text`；链接加 `count`、`links:[{href,text}]`；full 加 `screenshot` 与前500字符 `text_preview` |
| `scrape` | `url`：字符串，必填；`selector`：非空 CSS 字符串，必填；`timeout_s`：整数，默认30，1–120 | `{count,texts:[string]}`；未匹配返回0 |
| `fill_form` | `url`：字符串，必填；`fields_json`：字符串，必填，编码为1–100个 `{selector:非空字符串,value:字符串}` 对象的 JSON 数组，不可含其他键；`timeout_s`：整数，默认30，1–120 | `{fields_filled:integer}`；不回显值、选择器、URL、标题、DOM |
| `run` | `script`：字符串，默认 `main.py`，工作目录内已有 Python 文件，解析符号链接后也不可越界；`timeout_s`：整数，默认120，1–120，子进程截止时间 | 成功返回 stdout 字符串；非零退出/超时抛错，不返回捕获的输出 |

浏览器 URL 允许 `http`、`https` 和内联 `data:text/html,` 页面。不允许 URL
内嵌用户名/密码或 `file:`。重定向和子资源由浏览器处理，本模板不是网络白名单。
`fill_form` 用 Playwright `locator.fill` 后通过 `input_value` 校验，支持文本输入框
和 textarea，不执行 checkbox/select/submit。

表单参数示例（仅使用虚构值）：

```json
{"url":"https://example.com/login","fields_json":"[{\"selector\":\"#email\",\"value\":\"sample@example.invalid\"}]"}
```

### 原生 Playwright MCP

镜像包含官方 `@playwright/mcp@0.0.83` 和 lockfile 固定的 JavaScript Playwright1.64.0-alpha-1790635538000，复用现有 Chromium1208，不再安装第二份浏览器或模型凭据。原 Python API 继续使用 Playwright1.58.0；

| 命令 | 参数 | 结果 |
| --- | --- | --- |
| mcp_start | 无 | running、8931端口、mcp_version及协商的protocol_version |
| mcp_status | 无 | running:false或本进程拥有的MCP状态 |
| mcp_call | 必填method:str，仅tools/list、tools/call或ping；params_json:str="{}"，最大64KiB的JSON对象 | 真实MCP结果对象；工具失败检查isError |
| mcp_stop | 无 | 自有进程、浏览器和监听端口清理确认后返回running:false |
| mcp_self_test | 无 | 真正初始化、列工具、由独立HTTP fixture确认两次浏览器点击、生成真实PNG并完成清理后才返回PLAYWRIGHT_MCP_OK |

执行 `abx run <sandbox-id> mcp_start`，再执行 `abx run <sandbox-id> mcp_call --arg method=tools/list`。同一沙箱内的标准 MCP 客户端访问 `http://127.0.0.1:8931/mcp`，使用原生MCP会话及协议头。8931仅监听沙箱回环，不是带认证的公网网关。外部通过 SDK 的 `await client.commands.run("mcp_call", method="tools/list")` 使用命令服务配置的 bearer 认证。固定上游的 browser_click 使用新 browser_snapshot 中的 `target`，不是旧版ref参数。

诊断设置 `MCP_NODE_MODULES` 可选择独立安装且版本完全匹配的依赖树；镜像默认 /opt/playwright-mcp/node_modules。MCP HOME、浏览器配置和输出独立，停止后删除，不加载保存的浏览器配置或扩展。原生动作/导航时限10/20秒，HTTP响应4MiB、输出文件达到10MiB时触发旧文件淘汰（不是硬磁盘配额）、浏览器空闲60秒。调用串行；原生沙箱内端点保留MCP流式传输，命名mcp_call缓冲返回。子进程不继承云端、模型、服务密钥及Node注入变量。浏览器仍使用沙箱网络权限，没有额外SSRF策略。请求、页面和返回值可能含隐私，不公开记录。

### PDF及有界工作区脚本

`pdf(url:str, landscape:bool=false, print_background:bool=true, timeout_s:int=30) -> {path,bytes,format:"PDF"}` 使用固定真实Chromium输出A4 PDF。URL协议同browse，最大256KiB且无NUL。渲染后文件上限16MiB，不是峰值内存上限。布尔参数有类型检查。通过 SDK `await sb.files.read_bytes(result["path"])` 读取，导出后删除。`abx run <sandbox-id> pdf --arg url='data:text/html,<h1>PDF proof</h1>'` 调用真实渲染器。不覆盖调用者文件名，拒绝符号链接产物目录。

PDF在独立HOME子进程执行，执行时限1–120秒并有有界清理。通用run也保留进程身份，在成功、失败、输出超限或超时后停止自有普通及带标记的脱离进程。stdout/stderr各256KiB，错误不返回原生诊断。run保留调用者HOME，仅转发PATH、语言、浏览器和CA设置，不继承服务/云端/模型密钥及加载器注入。需要显式长期后台或环境设置时使用SDK进程接口。这是进程卫生措施，不是另一层沙箱安全边界。构建以实际du数据执行8GiB根文件系统预算，可用磁盘容量是另一指标。

## 配置

| 变量 | 默认值 | 用途 |
|---|---|---|
| `PLAYWRIGHT_BROWSERS_PATH` | 镜像内 `/opt/playwright` | 共享可读 Chromium 安装目录 |
| `WORKSPACE` | `/home/user/app` | 脚本根和 `browser-artifacts/` 产物根，与服务端文件策略对齐 |
| `ABX_SERVER_TOKEN` | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `ABX_SERVER_PORT` | `9000` | 本地 `python3 commands.py` 启动端口 |

正文、截图、链接和用户脚本输出可能包含页面敏感信息。产物应按私有文件处理，
不要输出到共享日志。禁止把凭据写入镜像或 YAML。填表成功与错误响应都不回显
输入值；用户脚本自行保证 stdout 安全。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB 内存、9000端口。Chromium 用 `/tmp` 替代小容量 `/dev/shm`。
并发请求增加内存占用，通过文件 API 删除旧 `browser-artifacts/` 释放根文件系统。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/browser-automation.md)。

## 问题反馈

模板跟踪：[awesome-templates#22](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/22)。
服务端/客户端缺陷到 python-sdk，CLI 缺陷到 agent-sandbox，标题加 `[templates]`。
附脱敏复现、提供方、generation、SDK提交、预期和实际结果；先搜索现有 issue。

## 许可证

Apache-2.0。Playwright 为 Apache-2.0；Chromium 及其依赖保留各自上游许可声明。

后续真实构建网络诊断运行超过300秒，因此早先流截止不代表统一单步执行上限；拆分阶段保留，慢速大资产传输仍待解决。
