# browser-automation

## 做什么

Python 的 browse/scrape/fill_form 每次独立创建浏览器；原生MCP调用有意共享一个自有浏览器会话，直到停止或空闲关闭。mcp_stop删除其私有配置和输出。

用无头 Chromium 导航、保存 PNG 截图、提取正文和链接、填写表单。
每个命名命令独立创建并关闭浏览器，并发请求不共享 cookie、DOM 或表单值。
填表时内部校验输入值，只返回成功填写数量，不提交表单。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

阿里云 runtime 基础镜像（默认 `v0.0.49`，Python 3.13）、Playwright `1.58.0`
与其匹配的 Chromium revision，以及 Dockerfile 中精确提交钉住的
`agent-sandbox-server`。浏览器加 `--disable-dev-shm-usage`，适配极速版 64 MB
共享内存。开放命名命令、文件与进程 API；不启用可选 `/browser/*` 原语端点。

## 解决的问题

为 Agent 提供可复现的浏览器操作与可下载产物，不需要 Docker、KVM、桌面、
模型密钥或持久化浏览器会话。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./browser-automation --yes
abx run <sandbox-id> browse --json-args '{"url": "data:text/html,<title>ABX_E2E_OK</title><h1>ABX_E2E_OK</h1>", "action": "extract"}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('browse', url='data:text/html,<title>ABX_E2E_OK</title><h1>ABX_E2E_OK</h1>', action='extract'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/browse`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{"url": "data:text/html,<title>ABX_E2E_OK</title><h1>ABX_E2E_OK</h1>", "action": "extract"}
```

该检查的预期响应：

```json
{"result": {"action": "extract", "title": "ABX_E2E_OK", "text": "ABX_E2E_OK"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

版本2.1.0加入官方 `@playwright/mcp@0.0.83` 和 lockfile 固定的 JavaScript Playwright1.64.0-alpha-1790635538000，复用现有 Chromium1208，不再安装第二份浏览器或模型凭据。原 Python API 继续使用 Playwright1.58.0；两个驱动组合都要真实验收，npm 版本号不能证明浏览器行为。

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

## 资源

2 vCPU、2048 MB 内存、9000端口。Chromium 用 `/tmp` 替代小容量 `/dev/shm`。
并发请求增加内存占用，通过文件 API 删除旧 `browser-artifacts/` 释放根文件系统。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 2.1.0 历史验收


版本2.1.0通过真实阿里云极速版原生step构建、Python SDK Sandbox.create、CLI/SDK浏览器及原生MCP冒烟，以及完整远程HTTP29 PASS/0 FAIL/0 SKIP。真实MCP工具发现、导航、快照、点击及截图复用Chromium1208，独立计数器与PNG检查通过。自有沙箱/模板删除及独立不存在性回查通过；其他提供方及其余上游工具动作未认证。

| Version | Provider | Evidence |
| --- | --- | --- |
| 2.1.0 | alicloud-express | [SDK-created steps](evidence/express-2026-10-20T094547Z.json), [full HTTP29](evidence/full-http-steps-2026-10-20T094547Z.json) |

## 2.0.2 历史验收

版本 2.0.2 已通过真实 CI 镜像登记、官方 READY、CLI/SDK，以及完整 Chromium 截图/PDF/独立产物 HTTP 检查 24 通过、0 失败、0 跳过。独立确认 sandbox/template/registry 清理。状态仍为 experimental；其他提供方未验证。

| 提供方 | 范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 精确当前版本、真实镜像和独立清理 | [正式回执](evidence/express-2026-10-20.json)、[HTTP](evidence/image-http-2026-10-20T060053Z.json) |


另一平台 step 尝试在 1200 秒内未达到 READY，官方最后状态为 building；[失败记录](evidence/full-http-steps-2026-10-20T062809Z.json)保留，不作为 step 通过证据。

## 历史验收

尚未记录任何通过的提供方测试。

静态符合性和本地浏览器验收可以独立执行，不代表云端提供方验收。L1 要求真实镜像
构建，L2 要求 READY 沙箱及外部 CLI、SDK 调用。缺失 Chromium 时 L0 失败，跳过
浏览器测试不能算作验收。

## 二次开发

2.0.2 将 Python 包、系统依赖、Chromium 下载拆为三个构建 RUN，避免
一次真实构建流截止。后续成功诊断超过300秒，不能推断极速版统一单步时限。Playwright 版本及完整 Chromium 不变；旧版本证据保留。


在本目录运行 `abx template deploy` 或上述安装命令。部署器替换阿里云 region/tag
占位符，并可从 `ABX_SERVER_SDK_SOURCE` 注入服务端 wheel；否则使用归档提交钉。
重型安装放前层，`COPY commands.py` 放最后。Dockerfile 无 CMD/ENTRYPOINT，
generation 2 使用 YAML 的 `start_cmd`、`ready_cmd`，以 `user` 运行。

本地安装钉住的 Playwright 与对应 Chromium 到可写缓存，安装和运行时设置一致的
`PLAYWRIGHT_BROWSERS_PATH`。将 `WORKSPACE` 与 `ABX_SERVER_BASE_DIR` 指向
同一可写目录后启动 `python3 commands.py`，再运行
`E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py`。测试导航内联页面、
通过服务端文件 API 下载真实 PNG、检查表单脱敏及并发隔离，缺浏览器退出非零。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py browser-automation`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵守 [CONTRIBUTING.md](../CONTRIBUTING.md)、
[模板规范](../docs/template-spec.zh-CN.md) 和
[设计文档](../docs/design/browser-automation.md)。从仓库根运行
`python3 scripts/check_template.py browser-automation` 与
`python3 scripts/run_local_e2e.py`。只记录真实通过级别，未满足验收前保持 experimental。

## 问题反馈

模板跟踪：[awesome-templates#22](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/22)。
服务端/客户端缺陷到 python-sdk，CLI 缺陷到 agent-sandbox，标题加 `[templates]`。
附脱敏复现、提供方、generation、SDK提交、预期和实际结果；先搜索现有 issue。

## 许可证

Apache-2.0。Playwright 为 Apache-2.0；Chromium 及其依赖保留各自上游许可声明。

后续真实构建网络诊断运行超过300秒，因此早先流截止不代表统一单步执行上限；拆分阶段保留，慢速大资产传输仍待解决。
