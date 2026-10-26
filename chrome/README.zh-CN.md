# chrome

[English](README.md)

## 做什么

运行原版有界面的 Chrome-for-Testing145.0.7632.6，使用私有 Xvfb/Openbox 桌面，提供原生 CDP9222、Debian 原版 noVNC6080 和真实桌面 PNG。范围是浏览器应用；不包含模型、远程桌面产品或基准成绩。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Alibaba generation2 basev0.0.49、Python3.13/Linuxx64；完整 SHA256 校验的原版 Chrome ZIP；精确固定的 Debian 桌面/VNC 软件包；独立环境中完整哈希锁定的 aiohttp3.14.5、pycryptodome4.1.0、Pillow11.3.0。[Dockerfile](Dockerfile)、[浏览器来源](browser.json)、[依赖锁](requirements.lock)、[设计](../docs/design/chrome.md)。已发布服务端包。

## 解决的问题

通过自动化和可见交互画面操作同一个真实浏览器，无需嵌套 Docker、KVM 或宿主机浏览器。CDP9222 透明转发原生回环9223；noVNC6080 转发带密码认证的回环5901 RFB。浏览器以 user 运行，使用私有配置和 Xauthority。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//chrome --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" chrome_start --json-args '{}'
abx run "$SANDBOX_ID" chrome_open --json-args '{"url":"https://example.com"}'
abx run "$SANDBOX_ID" chrome_screenshot --json-args '{}'
```

返回实际浏览器标题和最终 URL；随后可截图保存同一会话。

`chrome_start` 返回会话专用 VNC 密码。解析 6080 端口后打开 noVNC，使用这个密码登录；CDP 使用 9222 端口和应用口令。必须原样保留提供方返回 URL 的路径、查询和网关头。浏览器网站账号需要在这个远端会话里单独登录，不继承本机 cookies。

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
            await client.commands.run('chrome_start')
            result = await client.commands.run('chrome_open', url='https://example.com')
            print(result)
            extra = await client.commands.run('chrome_screenshot')
            print(extra)
            Path("chrome.png").write_bytes(await sb.files.read_bytes(extra["path"]))
        finally:
            try:
                await client.commands.run('chrome_stop')
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

- `POST /commands/chrome_start` with `{}`.

`POST /commands/chrome_open`

```json
{
  "url": "https://example.com"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/chrome_stop` with `{}`.

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
| ABX_SERVER_TOKEN | 必填；清单为空 | 启动模板前必须导出独立应用令牌；与模型及网关凭据分开。也用于 CDP relay 认证。 |

[运行环境](../docs/runtime-environment.md)说明预热服务：创建沙箱时注入变量不会重配现有进程。每个独占会话生成私有8字符 VNC 密码与 Xauthority cookie；密码仅由授权的 start 调用返回，不进入 argv/日志。浏览器环境不包含操作者云、模型或 GitHub 凭据。停止删除本次 HOME、配置、cookie、密码文件。noVNC 仍需 VNC 密码；转发 URL 应使用提供方访问控制。

工作目录为 `/home/user/workspace`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 使用 chrome_screenshot 返回的 path 下载 PNG
abx download "$SANDBOX_ID" '<returned-path>' ./chrome.png
abx run "$SANDBOX_ID" chrome_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB；1024×768 桌面；命令端口 9000、CDP 9222、noVNC 6080。每个服务仅一个浏览器会话，不需要 GPU、KVM 或嵌套 Docker。Chrome 在外层沙箱内使用 `--no-sandbox`；这不是额外的隔离层。截图会占用工作区磁盘。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/chrome.md)。

## 问题反馈

CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。[Issue61](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/61) 跟踪本模板。模板/控制器问题提交此仓库，客户端/服务端契约问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

自编包装代码 Apache-2.0。Chrome-for-Testing 与 Debian 组件保留各自许可证；noVNC 包含 MPL2.0/BSD2/OFL1.1/CC-BY-SA3.0 等许可及第三方声明。包装代码不会重新许可这些资产。见[上游声明](UPSTREAM-NOTICE.md)及镜像内原生软件包 copyright。
