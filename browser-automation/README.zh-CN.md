# browser-automation

## 做什么

用无头 Chromium 导航、保存 PNG 截图、提取正文和链接、填写表单。
每个命名命令独立创建并关闭浏览器，并发请求不共享 cookie、DOM 或表单值。
填表时内部校验输入值，只返回成功填写数量，不提交表单。

## 技术栈

阿里云 runtime 基础镜像（默认 `v0.0.49`，Python 3.13）、Playwright `1.58.0`
与其匹配的 Chromium revision，以及 Dockerfile 中精确提交钉住的
`agent-sandbox-server`。浏览器加 `--disable-dev-shm-usage`，适配极速版 64 MB
共享内存。开放命名命令、文件与进程 API；不启用可选 `/browser/*` 原语端点。

## 解决的问题

为 Agent 提供可复现的浏览器操作与可下载产物，不需要 Docker、KVM、桌面、
模型密钥或持久化浏览器会话。

## 快速开始（CLI）

```bash
abx template install alibaba-agent-sandbox/awesome-templates//browser-automation
abx create --template <template-id>
abx run <sandbox-id> browse --arg url=https://example.com --arg action=extract
abx run <sandbox-id> browse --json-args '{"url":"https://example.com","action":"screenshot","timeout_s":30}'
abx run <sandbox-id> scrape --arg url=https://example.com --arg selector=h1
```

使用 CLI 返回的模板和沙箱 id。`abx run` 调用命名命令，`abx exec` 执行 shell
程序。`--arg` 传字符串，整数 `timeout_s` 用 `--json-args`。真实表单秘密不要
写进命令行或 shell 历史；在妥善管理秘密的进程中使用 SDK。

## 快速开始（Python SDK）

安装客户端发行包：`python3 -m pip install agent-sandbox-client`。

```python
import asyncio
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        result = await sb.run("browse", url="https://example.com", action="extract", timeout=90)
        print(result["title"])
        screenshot = await sb.run("browse", url="https://example.com", action="screenshot", timeout=90)
        await sb.server.files.download_file(screenshot["path"], "example.png")
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 返回解包后的 `result`。`timeout=90` 是客户端 HTTP 超时；命令
`timeout_s=30` 默认分别限制浏览器启动、导航和每项动作，不是整个命令的墙钟
截止时间。每个表单字段都可能消耗一次动作超时。客户端超时不保证取消服务端。
后台浏览器脚本、重连、取消请用进程 API。配置 `ABX_SERVER_TOKEN` 后用
`sb.server_at(9000, token=server_token, timeout=90).commands.run(...)`。

## 快速开始（HTTP POST）

`BASE_URL` 为 `sb.network.get_url(9000)` 返回的沙箱端口地址。
本地未配置认证时：

```bash
curl --fail-with-body -X POST "$BASE_URL/commands/browse" \
  -H 'Content-Type: application/json' \
  --data '{"url":"https://example.com","action":"extract","timeout_s":30}'
```

返回形状（网页文本可能变化）：

```json
{"result":{"action":"extract","title":"Example Domain","text":"Example Domain\n..."}}
```

参数对象直接放 JSON 正文，不包 `args`。服务端认证是独立可选项：创建沙箱时
注入 `ABX_SERVER_TOKEN` 后，加 `Authorization: Bearer ${SERVER_TOKEN}` 或
`X-Access-Token: ${SERVER_TOKEN}`。提供方网关认证与它不同：提供方要求时，
使用 `sb.network.get_access_headers()` 返回的访问头。当前极速版 9000 端口在
网关处公开，不要把沙箱访问令牌当服务端令牌。两层同时认证时，保留服务端
Authorization 头及提供方独立网关头，不记录任何实际令牌。

HTTP 400 为缺少参数或类型错误；401 为服务端认证失败；404 为命令不存在；
500 为浏览器/脚本失败，或非法 action、URL、范围、表单 JSON 等语义错误。
错误格式为 `{"error":"...","type":"..."}`，浏览器错误不包含请求值。

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

## 配置

| 变量 | 默认值 | 用途 |
|---|---|---|
| `PLAYWRIGHT_BROWSERS_PATH` | 镜像内 `/opt/playwright` | 共享可读 Chromium 安装目录 |
| `WORKSPACE` | `/home/user/app` | 脚本根和 `browser-artifacts/` 产物根，与服务端文件策略对齐 |
| `ABX_SERVER_TOKEN` | 未设置/空 | 可选服务端认证，创建沙箱时注入 |
| `ABX_SERVER_PORT` | `9000` | 本地 `python3 commands.py` 启动端口 |

正文、截图、链接和用户脚本输出可能包含页面敏感信息。产物应按私有文件处理，
不要输出到共享日志。禁止把凭据写入镜像或 YAML。填表成功与错误响应都不回显
输入值；用户脚本自行保证 stdout 安全。

## 资源

2 vCPU、2048 MB 内存、9000端口。Chromium 用 `/tmp` 替代小容量 `/dev/shm`。
并发请求增加内存占用，通过文件 API 删除旧 `browser-artifacts/` 释放根文件系统。

## 已验证

尚未记录任何通过的提供方测试。

静态符合性和本地浏览器验收可以独立执行，不代表云端提供方验收。L1 要求真实镜像
构建，L2 要求 READY 沙箱及外部 CLI、SDK 调用。缺失 Chromium 时 L0 失败，跳过
浏览器测试不能算作验收。

## 二次开发

在本目录运行 `abx template deploy` 或上述安装命令。部署器替换阿里云 region/tag
占位符，并可从 `ABX_SERVER_SDK_SOURCE` 注入服务端 wheel；否则使用归档提交钉。
重型安装放前层，`COPY commands.py` 放最后。Dockerfile 无 CMD/ENTRYPOINT，
generation 2 使用 YAML 的 `start_cmd`、`ready_cmd`，以 `user` 运行。

本地安装钉住的 Playwright 与对应 Chromium 到可写缓存，安装和运行时设置一致的
`PLAYWRIGHT_BROWSERS_PATH`。将 `WORKSPACE` 与 `ABX_SERVER_BASE_DIR` 指向
同一可写目录后启动 `python3 commands.py`，再运行
`E2E_BASE_URL=http://127.0.0.1:9000 python3 e2e_test.py`。测试导航内联页面、
通过服务端文件 API 下载真实 PNG、检查表单脱敏及并发隔离，缺浏览器退出非零。

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
