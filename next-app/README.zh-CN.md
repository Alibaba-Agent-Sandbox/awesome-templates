# next-app

[English](README.md)

## 做什么

创建全新最小工程，启动真实开发服务器、查看日志并停止本次进程。每次只运行一个服务：命令接口9000、Next3000、Vite5173。不包含发布到 Vercel；HMR/WebSocket 尚未认证。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云基础镜像 fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>，默认v0.0.49，已观测 Node20.20.2 满足上游引擎要求。npm ci 使用提交的完整性锁文件，运行时不下载包。generation2、USER user、工作区 /home/user/app、平台 start/health 命令，无 Docker CMD/ENTRYPOINT。依赖许可证随安装保留。

## 解决的问题

在通用 Node 进程能力之外提供可实际访问、修改源码并重新预览的前端工程，明确启动、状态、日志、停止及资源所有权。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//next-app --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" scaffold --json-args '{"kind":"next","path":"preview-app"}'
abx run "$SANDBOX_ID" dev_start --json-args '{"kind":"next","path":"preview-app","timeout_s":120}'
```

返回 `running: true`、`port: 3000`。解析 3000 端口后可见 `ABX_NEXT_PREVIEW`；源码保留在 `preview-app/`。

用 `await sb.network.resolve(3000)` 获取 Next.js 预览入口，并保留地址的路径、查询和网关头；必要时使用[预览指南](../docs/preview-proxy.md)。应用本身没有登录认证，应使用提供方访问控制。Vite 需要指定 `kind="vite"` 并使用 5173；若被 Host 校验拒绝，只把实际网关主机名传给 `allowed_host`，不要填通配符。

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
            await client.commands.run('scaffold', kind='next', path='preview-app')
            result = await client.commands.run('dev_start', kind='next', path='preview-app', timeout_s=120)
            print(result)
        finally:
            try:
                await client.commands.run('dev_stop')
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

- `POST /commands/scaffold` with `{"kind": "next", "path": "preview-app"}`.

`POST /commands/dev_start`

```json
{
  "kind": "next",
  "path": "preview-app",
  "timeout_s": 120
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/dev_stop` with `{}`.

## 命令参考

| 命令 | 参数（均可省略） | 返回 |
|---|---|---|
| preview_self_test | none / 无 | NEXT_VITE_PREVIEW_OK; actual Next/Vite pages, owned workers/project cleanup |
| toolchain_versions | 无 | 实际 next/react/react-dom/vite 版本表 |
| scaffold | kind: next/vite，默认 next；path: 全新单层工作区目录名，默认 preview-app | {path,kind} |
| dev_start | kind: next/vite，默认 next；path: 匹配脚手架，默认 preview-app；timeout_s:1..180，默认120；allowed_host:str=""，仅Vite的单个准确DNS主机名 | {port,kind,running:true} |
| dev_status | 无 | {running:false} 或 {port,kind,path,running:true} |
| dev_logs | tail_bytes:1..8192，默认4096 | 有界缓冲日志尾部 |
| dev_stop | 无 | 独立确认进程和监听消失后的 {running:false} |

Next 使用本地 next dev --webpack --hostname0.0.0.0 --port3000；Vite 使用本地 vite --host0.0.0.0 --port5173 --strictPort，参数不经过 shell。拒绝已存在目录、符号链接目录及路径越界。受控 node_modules 链接只指向预装工具链。停止保留源码和构建缓存；需要时由调用方显式删除。日志为缓冲结果，不宣称实时流式。

Vite 可通过 allowed_host 指定准确的 SDK 转发主机名。默认空值保留本机域名权限；传入 urlsplit((await sb.network.resolve(5173))[0]).hostname，仅设置固定Vite8.3.4源码及[官方文档](https://vite.dev/config/server-options#server-allowedhosts)支持的 __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS。拒绝通配符、前导点后缀、协议、端口、凭据、逗号及空DNS标签。Next不接受此Vite专用设置。不改写Host，也不开全域允许。

## 配置

| 名称 | 默认值 | 用途 |
|---|---|---|
| ABX_SERVER_TOKEN | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| ABX_SERVER_PORT | 9000 | 本地命令服务端口 |
| WORKSPACE | /home/user/app | 已存在工作区 |
| NEXT_APP_TOOLCHAIN | /opt/next-app | 可信固定工具链；本机测试可指向安装目录 |

开发进程只继承 Node PATH、私有临时 HOME、语言、遥测关闭和所有权标记，不传入云端或模型密钥。预览应用无单独密码，应使用平台访问控制。日志可能包含应用数据，不可直接发布含隐私的日志。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx run "$SANDBOX_ID" dev_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU、2048MB，平台根文件系统约10GiB，端口9000/3000/5173。不需要 Docker、KVM、显示器。Linux pidfd/procfs 用于身份安全的清理；停止所有权标记的派生进程和未回收主进程组，并独立确认内核监听不存在。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/next-app.md)。

## 问题反馈

[模板 Issue54](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/54)，[Python SDK/服务端](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI 问题标题使用 [templates] 前缀。

## 许可证

仓库源码 Apache-2.0，见 [LICENSE](../LICENSE)。Next、React、Vite 为 MIT，来源固定在 upstream-pins.json，传递依赖许可证随 node_modules 保留。

FC把HTML标为附件时，可在启动自有应用后使用[SDK本地中继](../docs/preview-proxy.zh-CN.md)：python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 3000（Next）或--remote-port 5173（Vite）。Vite仍传入前述准确allowed_host。中继借用该沙箱；结束时停止中继并显式停止/销毁自有应用资源。Next/Vite此浏览器入口仅完成源码检查，浏览器及HMR未单独认证。
