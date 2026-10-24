# chrome

[English](README.md)

## 做什么

运行原版有界面的 Chrome-for-Testing145.0.7632.6，使用私有 Xvfb/Openbox 桌面，提供原生 CDP9222、Debian 原版 noVNC6080 和真实桌面 PNG。范围是浏览器应用；不包含模型、远程桌面产品或基准成绩。

## 技术栈

Alibaba generation2 basev0.0.49、Python3.13/Linuxx64；完整 SHA256 校验的原版 Chrome ZIP；精确固定的 Debian 桌面/VNC 软件包；独立环境中完整哈希锁定的 aiohttp3.14.5、pycryptodome4.1.0、Pillow11.3.0。[Dockerfile](Dockerfile)、[浏览器来源](browser.json)、[依赖锁](requirements.lock)、[设计](../docs/design/chrome.md)。服务端源码 e2cb27e24fde0a67112f82b8d44af463445a5d1a。

## 解决的问题

通过自动化和可见交互画面操作同一个真实浏览器，无需嵌套 Docker、KVM 或宿主机浏览器。CDP9222 透明转发原生回环9223；noVNC6080 转发带密码认证的回环5901 RFB。浏览器以 user 运行，使用私有配置和 Xauthority。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./chrome --workflow application --yes
abx run <sandbox-id> chrome_smoke --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('chrome_smoke'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/chrome_smoke`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "native headed Chrome145.0.7632.6 CDP/VNC/PNG and cleanup OK"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters / limits | Result / effects |
| --- | --- | --- |
| chrome_version | none | Actual browser_version145.0.7632.6 and native_binary_sha256; verifies fixed binary before execution |
| chrome_setup_check | none | installed/running/reserved_ports_available booleans, browser_version and mode; no launch |
| chrome_start | none | running, browser_version, cdp9222, vnc6080, vnc_path, private vnc_password, width1024, height768, headed, shm_bytes, optional cgroup limits, reused; creates desktop/profile/processes |
| chrome_status | none | Owned live status without password; stopped status includes owned_ports_absent/private_state_absent |
| chrome_open | url: required string, 1..2048 characters; HTTP(S) without whitespace/control/userinfo, or about:blank | Native final URL/title after navigation; existing session required |
| chrome_screenshot | none | Exclusive new workspace PNG: path/bytes/sha256/width/height; at most8MiB; retained for caller |
| chrome_stop | none | running:false, owned_ports_absent:true, private_state_absent:true only after owned cleanup |
| chrome_smoke | none | Exact manifest smoke string after actual CDP state, authenticated VNC/PNG and cleanup; rejects an active caller session |

调用串行化。启动就绪预算90秒；导航/CDP/VNC 操作30秒；启动建议客户端超时150秒。结果缓冲返回，IPC 限8MiB、输入限32KiB。PNG 独占创建并设置0600权限。停止时保留调用方截图，不删除无关文件或进程；调用方或沙箱销毁负责最终清理。

## 配置

| 变量 | 默认值/要求 | 用途 |
| --- | --- | --- |
| WORKSPACE | /home/user/workspace；已存在目录 | 截图根目录，命令模块启动时读取 |
| ABX_SERVER_TOKEN | 必填；清单值为空 | 启动前导出独立应用令牌 |

[运行环境](../docs/runtime-environment.md)说明预热服务：创建沙箱时注入变量不会重配现有进程。每个独占会话生成私有8字符 VNC 密码与 Xauthority cookie；密码仅由授权的 start 调用返回，不进入 argv/日志。浏览器环境不包含操作者云、模型或 GitHub 凭据。停止删除本次 HOME、配置、cookie、密码文件。noVNC 仍需 VNC 密码；转发 URL 应使用提供方访问控制。

## 资源

声明2vCPU/2048MB、1024×768、端口9000/9222/6080、内部9223/5901及一个独占 X display。无需 Docker/KVM/GPU。Chrome 在一次性外层沙箱内使用 --no-sandbox 与 --disable-dev-shm-usage，不构成额外 OS 隔离。镜像根目录限制8GiB。极速版 /dev/shm 实测1031241728字节，v2 cgroup 路径不可用；2CPU/2048MB 是模板声明，不是实测峰值或 cgroup2 上限。独立 L1 原生镜像 smoke 实测64MiB共享内存，当时 CPU/内存未限制，根目录实测1689714688字节。这些是分开测量，不代表2GB与64MiB组合压力测试。每个服务一个会话；下载/截图占用调用方工作空间。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

同步更新 browser.json、安装器固定版本/哈希、原生来源校验、系统依赖及 smoke 断言，并保留原版浏览器声明。必须验证原生 CDP、密码认证 RFB、真实 VNC 点击，以及独立 CDP 状态变化；截图或 HTTP 模拟不能代替浏览器。

## 贡献

遵守[贡献规范](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.md)、[文档规范](../docs/documentation-standards.md)，保持双语说明、设计、目录和历史收据一致。

## 问题反馈

CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。[Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61) 跟踪本模板。模板/控制器问题提交此仓库，客户端/服务端契约问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

自编包装代码 Apache-2.0。Chrome-for-Testing 与 Debian 组件保留各自许可证；noVNC 包含 MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 等许可及第三方声明。包装代码不会重新许可这些资产。见[上游声明](UPSTREAM-NOTICE.md)及镜像内原生软件包 copyright。
