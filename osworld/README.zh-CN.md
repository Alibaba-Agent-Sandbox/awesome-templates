# OSWorld Linux 浏览器切片

## 做什么

运行真实的私有 Xvfb/Openbox/Chromium 桌面，提供 [OSWorld](https://github.com/xlang-ai/OSWorld) 截图、Linux AT-SPI、原生鼠标键盘操作与私有剪贴板 Unicode 粘贴和明确的任务评估子集。这是独立的 Alibaba 模板。完整 OSWorld benchmark、VM 快照、Office 和模型 agent 不在此浏览器切片内；[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) 保持开放。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

OSWorld 固定源码 `b138d348256078fa634fc3b73567a7337c793e6b`（Apache-2.0）；Playwright 1.58.0 及对应 Chromium revision；PyAutoGUI 0.9.54、Pillow 11.3.0、Flask 3.1.2、NumPy 2.3.3、lxml 6.0.1、requests 2.32.5。Python 完整依赖图有[哈希锁文件](requirements.txt)。Debian 13 x86_64 关键桌面包固定版本，传递系统依赖仍由发行版仓库解析。见 [Dockerfile](Dockerfile)、[源码归属](upstream/source.json)与[设计](../docs/design/osworld.md)。

## 解决的问题

在无 KVM、无 Docker daemon、运行时非特权的 Express 内操作真实浏览器桌面。失败或不支持的任务明确报错，不产生虚构 benchmark 分数。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./osworld --yes
abx run <sandbox-id> osworld_desktop_smoke --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('osworld_desktop_smoke'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/osworld_desktop_smoke`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "desktop screenshot/click/type/hotkey/AT-SPI/evaluation OK"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

用该文件的 `task_path` 调用 `run_task_config` 和 `evaluate`。setup 只支持 1..4 个 HTTP(S) 或 workspace 文件 URL，以及 0..5 秒的 `sleep`，最多 8 步。evaluator 只支持 `check_include_exclude`（非空 include 列表）或 `exact_match`、真实 `accessibility_tree` getter 和 `rule` expected。未知字段/步骤、launch/shell/VM/Office/proxy、postconfig、不支持的 metric 均在 setup 前失败，跳过步骤不会获得分数。从提交的固定源码执行未改动的 getter/metric 定义，不导入云/proxy/Office registry。无 LibreOffice 时向上游浏览器可访问性 handler 表达版本未知，不伪造二进制或版本。Unicode 粘贴全文在浏览器 DOM 中独立验证；native 任务试验中 astral emoji 的可访问性观察不稳定，验收任务使用 ASCII 和 CJK。返回真实上游 XML，不伪造缺失字符或评分。

## 资源

2 vCPU / 2048 MB，generation 2，非 root `user`，9000 端口。不需要 KVM、GPU、Docker daemon 或额外 capability。镜像包含浏览器和系统库，运行时不下载 GUI。worker 显式保留镜像的 `PLAYWRIGHT_BROWSERS_PATH=/opt/osworld-browser`，从安装路径查找固定浏览器。用一次性 sandbox 访问不可信页面。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python scripts/check_template.py osworld
python -m pytest -q osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py
E2E_BASE_URL=http://127.0.0.1:9000 E2E_REQUIRE_DESKTOP=1 E2E_RUN_DESKTOP=1 python osworld/e2e_test.py
```

required GUI 模式缺依赖即失败。默认本地 HTTP 检查只报告 GUI SKIP，不声明桌面通过。真实镜像 smoke 验证 PNG/树、基线分数 0、原生操作、独立浏览器状态、最终分数 1、像素变化和清理；marker 不参与评分。镜像smoke另用私有剪贴板粘贴4096个含emoji的Unicode字符，并独立读取完整DOM值；任务评分使用ASCII/CJK，emoji的可访问性表示不计通过。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py osworld`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵循[贡献指南](../CONTRIBUTING.md)与[模板规范](../docs/template-spec.zh-CN.md)，保持固定源码/许可证、翻译、支持范围和证据准确。

## 问题反馈

[Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36) 跟踪切片及剩余完整运行时。模板问题提交本仓库；SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0。保留原 OSWorld 文件、完整[上游许可证](upstream/LICENSE)与源码 SHA256 清单。PyAutoGUI 等依赖保留安装分发的许可证；Chromium 和 Debian 包保留安装自带 notices。

1024×768 PNG/Xvfb 屏幕与浏览器页面 viewport 是不同测量值。启动只要求可见且非零的 viewport，不会通过缩放或模拟把页面改成屏幕大小。`desktop_start` 和 `run_task_config` 返回 `browser_geometry`，仅包含屏幕、外层窗口、viewport 和内容偏移的数值字段；独立 smoke 仅打印这些数值用于镜像诊断。`click` 仍接受屏幕坐标，smoke 使用实际内容偏移和 DOM 矩形，继续要求真实输入、上游评分 0→1、PNG 像素变化及完整 4096 字符目标值读回。参见[viewport 后续证据](../.agents/evidence/verify/2026-10-16-osworld-viewport.md)。

镜像显式将 `/home/user/app` 目录归属运行用户，使上传的任务文件和一次性 smoke fixture 可以在非 root 身份下写入；仅给 `COPY` 文件设置 owner 并不会自动修正 WORKDIR 本身。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。

### 当前平台 step 验收

[当前版本真实 step](evidence/express-2026-10-20.json)与[基础外部 HTTP 结果](evidence/verification-steps-2026-10-20T151021Z.json)已通过：官方 READY、真实 Python SDK 创建、CLI/SDK smoke，6 PASS / 0 FAIL / 1 GUI SKIP，耗时 346.984 秒。自有沙箱、模板及私有缓存已独立确认清理。早期失败保留为历史记录；本次未运行模型，不扩大已有镜像／模型验收范围。

跳过的是外部桌面检查，并非模型检查；内部命名桌面 smoke 已单独通过。完整外部桌面验收必须启用两个桌面开关，18 项全部通过且无跳过，下述真实 SDK 创建复测已完成该层验收。

[当前必选外部桌面结果](evidence/verification-steps-2026-10-20T171144Z.json)与[规范 CLI/SDK 回执](evidence/express-2026-10-20T171144Z.json)：真实 SDK 创建原生 steps，274.783 秒，18 PASS/0 FAIL/0 SKIP。原控制器验证真实 PNG、点击、Unicode 输入、快捷键、AT-SPI、上游评分0→1及像素变化，随后清理桌面和任务文件，并独立确认沙箱、模板、私有缓存均不存在。两个桌面必选开关均已记录；本次完成浏览器切片的外部桌面层，不扩大到完整 benchmark、模型或 VM 重置能力。
