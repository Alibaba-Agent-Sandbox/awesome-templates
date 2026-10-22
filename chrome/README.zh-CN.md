# chrome

[English](README.md)

## 做什么

运行原版有界面的 Chrome-for-Testing145.0.7632.6，使用私有 Xvfb/Openbox 桌面，提供原生 CDP9222、Debian 原版 noVNC6080 和真实桌面 PNG。范围是浏览器应用；不包含模型、远程桌面产品或基准成绩。

## 技术栈

Alibaba generation2 basev0.0.49、Python3.13/Linuxx64；完整 SHA256 校验的原版 Chrome ZIP；精确固定的 Debian 桌面/VNC 软件包；独立环境中完整哈希锁定的 aiohttp3.14.5、pycryptodome4.1.0、Pillow11.3.0。[Dockerfile](Dockerfile)、[浏览器来源](browser.json)、[依赖锁](requirements.lock)、[设计](../docs/design/chrome.md)。服务端源码 e2cb27e24fde0a67112f82b8d44af463445a5d1a。

## 解决的问题

通过自动化和可见交互画面操作同一个真实浏览器，无需嵌套 Docker、KVM 或宿主机浏览器。CDP9222 透明转发原生回环9223；noVNC6080 转发带密码认证的回环5901 RFB。浏览器以 user 运行，使用私有配置和 Xauthority。

## 快速开始（CLI）

按[平台 steps](../docs/platform-steps.md)安装已验证 CLI0.4.1 原生入口并配置已授权的极速版访问。尖括号值需替换为本次独占资源；不可变 COPY 需要先发布对应源码提交。等待官方 READY 后再创建。以下操作打开 example.org 并截图。chrome_start 返回临时 VNC 密码，应私密保存，避免写入日志。

The `abx run` command uses the CLI0.4.1 native entry as `abx --native run`.

```bash
python scripts/prepare_steps.py chrome --output /tmp/chrome-steps-<unique-run> \
  --asset-transport parallel --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/chrome-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> chrome_start
abx --native run <owned-sandbox-id> chrome_open --arg url=https://example.org
abx --native run <owned-sandbox-id> chrome_screenshot
abx --native run <owned-sandbox-id> chrome_stop
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

完整验证入口：`ABX="abx --native" python scripts/run_steps_e2e.py chrome --sandbox-create sdk --http --asset-transport oss`。OSS 私有缓存只传输精确哈希归档，并独立验证本次对象/桶清理。steps 运行不能证明 Docker 镜像已构建。

## 快速开始（Python SDK）

按[配套源码安装](../docs/python-client-installation.md)安装 `agent-sandbox-client`。示例已做语法检查；真实验收使用独占离线测试页面，见下方记录；任务与 CLI/HTTP 相同。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        info = await sb.run("chrome_start", timeout=150)
        # Keep info["vnc_password"] private; enter it in the noVNC UI.
        cdp_url = sb.network.get_url(9222)
        vnc_url = sb.network.get_url(6080) + "/vnc.html"
        await sb.run("chrome_open", url="https://example.org", timeout=60)
        image = await sb.run("chrome_screenshot", timeout=60)
        png = await sb.files.read_bytes(image["path"], max_bytes=8 * 1024**2)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        await sb.run("chrome_stop", timeout=90)
    finally:
        await sb.kill()

asyncio.run(main())
```

CDP 和 WebSocket 需要所选提供方的网关访问头。通过 noVNC 界面输入生成的密码，不要将密码写入 URL。配置 ABX_SERVER_TOKEN 后使用 `sb.server_at(9000, token=...)` 的命令客户端，并在 finally 关闭该客户端；CDP 转发也要求相同 Bearer。请求超时不会取消桌面，仍须 chrome_stop 或销毁独占沙箱。

## 快速开始（HTTP POST）

先用 `{}` 调用 `POST /commands/chrome_start`。ABX_SERVER_URL 为 `sb.network.get_url(9000)`；需要时同时提供网关访问头和独立服务端 Bearer。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/chrome_open" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{"url":"https://example.org"}'
```

直接传递参数对象，不使用 args 包装。示例 HTTP200 返回 `{"result":{"url":"https://example.org/","title":"Example Domain"}}`。之后用 `{}` 调用 chrome_screenshot、chrome_stop。参数缺失/类型错误400，服务端认证失败401，未知命令404，语义/执行错误500并包含 `{error,type}`。原生浏览器或网络失败不会作为成功返回。

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
| ABX_SERVER_TOKEN | 可选；空 | 命令服务/CDP Bearer，与网关/VNC 认证独立 |

[运行环境](../docs/runtime-environment.md)说明预热服务：创建沙箱时注入变量不会重配现有进程。每个独占会话生成私有8字符 VNC 密码与 Xauthority cookie；密码仅由授权的 start 调用返回，不进入 argv/日志。浏览器环境不包含操作者云、模型或 GitHub 凭据。停止删除本次 HOME、配置、cookie、密码文件。noVNC 仍需 VNC 密码；转发 URL 应使用提供方访问控制。

## 资源

声明2vCPU/2048MB、1024×768、端口9000/9222/6080、内部9223/5901及一个独占 X display。无需 Docker/KVM/GPU。Chrome 在一次性外层沙箱内使用 --no-sandbox 与 --disable-dev-shm-usage，不构成额外 OS 隔离。镜像根目录限制8GiB。极速版 /dev/shm 实测1031241728字节，v2 cgroup 路径不可用；2CPU/2048MB 是模板声明，不是实测峰值或 cgroup2 上限。独立 L1 原生镜像 smoke 实测64MiB共享内存，当时 CPU/内存未限制，根目录实测1689714688字节。这些是分开测量，不代表2GB与64MiB组合压力测试。每个服务一个会话；下载/截图占用调用方工作空间。

## 已验证


### 当前镜像验收 — 2026-10-22

| 提供方 | 当前版本与范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 1.0.5；常规镜像、真实 CLI/SDK、完整 HTTP 30 PASS / 0 FAIL / 0 SKIP、沙箱/模板/私有镜像仓库独立清理 | [运行与 HTTP 回执](evidence/image-http-2026-10-22T101624Z.json) |
| opensandbox | 1.0.5；原始 Docker 后端、逐项 CLI/SDK 命名 smoke、完整 HTTP 30 PASS / 0 FAIL / 0 SKIP、SDK/容器/进程独立清理 | [原生源码镜像回执](evidence/opensandbox-2026-10-22T110912Z.json) |

CLI 在 OpenSandbox 中通过实际 `abx exec` 调用容器内命名 HTTP API；通用 `run_code` 仍不支持，`template launch` 的能力检查仍生效。缺少模型或厂商账号的检查按回执明确跳过，不计为真实模型通过。[复现与验收范围](../docs/source-image-acceptance.zh-CN.md)。

<details>
<summary>此前验收记录（保留原有时间与范围）</summary>

| 提供方 | 日期 | 范围 | 证据 |
| --- | --- | --- | --- |
| alicloud-express | 2026-10-20 |1.0.5；原版有界面 Chrome145，SDK 创建的原生 steps，CLI/SDK smoke、完整HTTP30/0/0及独立清理 | [收据](evidence/express-2026-10-20T230349Z.json)、[控制器/来源](evidence/verification-steps-2026-10-20T230349Z.json) |

准确运行/控制器源码 cd144246bcd3e2ba37865d90e24cba612db8b11b。[L1 原生镜像 smoke](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39512397976) 也通过，独立实测64MiB共享内存。原生 CDP/noVNC/RFB 认证、真实 VNC 指针输入与独立 DOM/画面变化、有效命名导航及外部 CDP 回读、PNG 独立下载/字节/哈希/多区域/返回后随机 ACK，以及本次原生进程/私有目录/display/监听/沙箱/模板/OSS 缺席均通过，耗时156.468秒。不声明模型、基准或其他提供方验收。[最终记录](../.agents/evidence/verify/2026-10-20-chrome-native-final.md)。历史鼠标指针采样失败和仅诊断尝试保持原样；本地/源码检查不能赋予提供方资格。

</details>

## 二次开发

同步更新 browser.json、安装器固定版本/哈希、原生来源校验、系统依赖及 smoke 断言，并保留原版浏览器声明。必须验证原生 CDP、密码认证 RFB、真实 VNC 点击，以及独立 CDP 状态变化；截图或 HTTP 模拟不能代替浏览器。

## 贡献

遵守[贡献规范](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.md)、[文档规范](../docs/documentation-standards.md)，保持双语说明、设计、目录和历史收据一致。

## 问题反馈

CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。[Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61) 跟踪本模板。模板/控制器问题提交此仓库，客户端/服务端契约问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

自编包装代码 Apache-2.0。Chrome-for-Testing 与 Debian 组件保留各自许可证；noVNC 包含 MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 等许可及第三方声明。包装代码不会重新许可这些资产。见[上游声明](UPSTREAM-NOTICE.md)及镜像内原生软件包 copyright。
