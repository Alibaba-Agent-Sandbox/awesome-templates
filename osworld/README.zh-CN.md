# OSWorld Linux 浏览器切片

[English](README.md)

## 做什么

运行真实的私有 Xvfb/Openbox/Chromium 桌面，提供 [OSWorld](https://github.com/xlang-ai/OSWorld) 截图、Linux AT-SPI、原生鼠标键盘操作与私有剪贴板 Unicode 粘贴和明确的任务评估子集。这是独立的 Alibaba 模板。完整 OSWorld benchmark、VM 快照、Office 和模型 agent 不在此浏览器切片内；[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) 保持开放。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

OSWorld 固定源码 `b138d348256078fa634fc3b73567a7337c793e6b`（Apache-2.0）；Playwright 1.58.0 及对应 Chromium revision；PyAutoGUI 0.9.54、Pillow 11.3.0、Flask 3.1.2、NumPy 2.3.3、lxml 6.0.1、requests 2.32.5。Python 完整依赖图有[哈希锁文件](requirements.txt)。Debian 13 x86_64 关键桌面包固定版本，传递系统依赖仍由发行版仓库解析。见 [Dockerfile](Dockerfile)、[源码归属](upstream/source.json)与[设计](../docs/design/osworld.md)。

## 解决的问题

在无 KVM、无 Docker daemon、运行时非特权的 Express 内操作真实浏览器桌面。失败或不支持的任务明确报错，不产生虚构 benchmark 分数。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//osworld --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" desktop_start --json-args '{}'
abx run "$SANDBOX_ID" a11y_tree --json-args '{}'
```

返回实时桌面的无障碍 XML；可继续对同一会话调用 `screenshot`、`click`、`type` 和 `hotkey`。

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
            await client.commands.run('desktop_start')
            result = await client.commands.run('a11y_tree')
            print(result)
        finally:
            try:
                await client.commands.run('desktop_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

先按顺序调用：

- `POST /commands/desktop_start` with `{}`.

`POST /commands/a11y_tree`

```json
{}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/desktop_stop` with `{}`.

## 命令参考

| 命令 | 参数 | 返回 |
|---|---|---|
| osworld_setup_check | 无 | 源码 commit、依赖布尔值、运行状态、明确切片。 |
| desktop_start | 无 | 启动/复用一个 owned 会话；运行状态、屏幕尺寸与数值型浏览器几何信息。 |
| desktop_stop | 无 | 停止 owned 进程组并删私有状态；`stopped`。 |
| screenshot | 无 | 真实 PNG base64、MIME、SHA256、width=1024、height=768。 |
| click | x: int 必填，y: int 必填，button: str = left | 1024x768 内真实点击；left/middle/right。 |
| type | text: str 必填 | 私有 X11 剪贴板加真实 Ctrl+V 粘贴 1..4096 个 Unicode 字符，拒绝 NUL。 |
| hotkey | keys: str 必填 | 1..4 个逗号分隔的 PyAutoGUI 键名。 |
| a11y_tree | 无 | 上游真实 AT-SPI XML，最多 2 MiB。 |
| run_task_config | task_path: str 必填 | 应用已完整校验的支持步骤，返回数量及当前浏览器几何信息。 |
| evaluate | task_path: str 必填 | 上游 metric 对真实可访问性状态计算的分数。 |
| osworld_desktop_smoke | 无 | 真实离线任务及清理；不允许已有会话。 |

## 配置

此模板不需要模型账号；当前命令只操作一个 Linux 浏览器桌面切片，不提供完整 OSWorld 虚拟机、Office、任意任务或自动规划 Agent。若接入外部 Agent，模型与账号由调用方另行配置。

观察、操作或任务前先启动桌面。一个锁串行执行操作。普通操作限时 30 秒，输入、启动与一次性 smoke 限时 60 秒。输入使用原生剪贴板粘贴，60 秒上限包含剪贴板就绪与清理。超时、worker 失败、Python 取消或不支持的任务会停止 owned 会话，需要显式重启。HTTP 断连不取消执行。请求最多 32 KiB，响应最多 8 MiB。主动 setsid 脱离组的子进程超出 Linux 进程组边界。

保留原 HOME，不覆盖其值。worker 使用私有 XDG config/cache/runtime 目录、禁用 Python user-site，并拥有私有 Xauthority cookie、DBus/AT-SPI 服务与 Chromium user-data 目录；不继承用户浏览器 profile、DISPLAY 或云/模型凭据。不监听 VNC 或上游任意代码执行 HTTP。Chromium 在外层 sandbox 内使用 `--no-sandbox`。声明的 API shell/files 仍开放，隔离边界是外层 sandbox。用 `ABX_SERVER_TOKEN` 限制调用者。截图和树会包含用户打开的页面内容；浏览器 URL 可以使用网络出口。

`type` 会覆盖本私有 display 的剪贴板，并向当前聚焦应用发送真实 Ctrl+V。它支持 Unicode 粘贴，不承诺每字符一个物理键事件。文本通过 stdin 进入 foreground `xclip` 0.13-4。粘贴后停止并回收该 xclip 进程，确认其剪贴板 ownership 已释放；目标应用中按请求粘贴的内容仍保留。输入与hotkey会通过真实X焦点切回本次启动的Chrome主窗口，只匹配其进程PID；不操作宿主/其他会话窗口。不会使用共享宿主剪贴板。不接受粘贴的应用不受此命令支持。

将 OSWorld 结构的 JSON 任务文件上传到 `WORKSPACE`（默认 `/home/user/app`），最多 64 KiB；解析到目录外的符号链接被拒绝。支持的子集为：

```json
{
  "snapshot": "chrome",
  "config": [{"type":"chrome_open_tabs","parameters":{"urls_to_open":["https://example.com"]}}],
  "evaluator": {
    "func": "check_include_exclude",
    "result": {"type":"accessibility_tree"},
    "expected": {"type":"rule","rules":{"include":["Example Domain"],"exclude":[]}}
  }
}
```

用该文件的 `task_path` 调用 `run_task_config` 和 `evaluate`。setup 只支持 1..4 个 HTTP(S) 或 workspace 文件 URL，以及 0..5 秒的 `sleep`，最多 8 步。evaluator 只支持 `check_include_exclude`（非空 include 列表）或 `exact_match`、真实 `accessibility_tree` getter 和 `rule` expected。未知字段/步骤、launch/shell/VM/Office/proxy、postconfig、不支持的 metric 均在 setup 前失败，跳过步骤不会获得分数。从提交的固定源码执行未改动的 getter/metric 定义，不导入云/proxy/Office registry。无 LibreOffice 时向上游浏览器可访问性 handler 表达版本未知，不伪造二进制或版本。剪贴板粘贴支持 Unicode，但上游无障碍树可能遗漏部分 astral emoji。返回真实上游 XML，不伪造缺失字符或评分。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx run "$SANDBOX_ID" desktop_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU / 2048 MB，generation 2，非 root `user`，9000 端口。不需要 KVM、GPU、Docker daemon 或额外 capability。镜像包含浏览器和系统库，运行时不下载 GUI。worker 显式保留镜像的 `PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser`，从安装路径查找固定浏览器。用一次性 sandbox 访问不可信页面。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/osworld.md)。

## 问题反馈

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) 跟踪切片及剩余完整运行时。模板问题提交本仓库；SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0。保留原 OSWorld 文件、完整[上游许可证](upstream/LICENSE)与源码 SHA256 清单。PyAutoGUI 等依赖保留安装分发的许可证；Chromium 和 Debian 包保留安装自带 notices。

1024×768 PNG/Xvfb 屏幕与浏览器页面 viewport 是不同测量值。启动只要求可见且非零的 viewport，不会通过缩放或模拟把页面改成屏幕大小。`desktop_start` 和 `run_task_config` 返回 `browser_geometry`，仅包含屏幕、外层窗口、viewport 和内容偏移的数值字段；独立 smoke 仅打印这些数值用于镜像诊断。`click` 仍接受屏幕坐标，smoke 使用实际内容偏移和 DOM 矩形，继续要求真实输入、上游评分 0→1、PNG 像素变化及完整 4096 字符目标值读回。参见[viewport 后续证据](../.agents/evidence/verify/2026-10-16-osworld-viewport.md)。

镜像显式将 `/home/user/app` 目录归属运行用户，使上传的任务文件和一次性 smoke fixture 可以在非 root 身份下写入；仅给 `COPY` 文件设置 owner 并不会自动修正 WORKDIR 本身。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
