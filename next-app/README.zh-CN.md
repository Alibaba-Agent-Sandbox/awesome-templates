# next-app

[English](README.md)。固定 Next.js16.4.2、React/React DOM19.3.1、Vite8.3.4 的前端脚手架及开发预览。

## 做什么

创建全新最小工程，启动真实开发服务器、查看日志并停止本次进程。每次只运行一个服务：命令接口9000、Next3000、Vite5173。不包含发布到 Vercel；HMR/WebSocket 尚未认证。

## 技术栈

阿里云基础镜像 fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>，默认v0.0.49，已观测 Node20.20.2 满足上游引擎要求。npm ci 使用提交的完整性锁文件，运行时不下载包。服务端固定 python-sdk e2cb27e24fde0a67112f82b8d44af463445a5d1a 作为无注入 wheel 时的回退。generation2、USER user、工作区 /home/user/app、平台 start/health 命令，无 Docker CMD/ENTRYPOINT。依赖许可证随安装保留。

## 解决的问题

在通用 Node 进程能力之外提供可实际访问、修改源码并重新预览的前端工程，明确启动、状态、日志、停止及资源所有权。

## 快速开始（CLI）

按照[原生 CLI 配置](../docs/platform-steps.zh-CN.md)准备环境。完成预览后执行停止和删除；标准入口参数差异见[入口兼容说明](../docs/using-templates.md#client-entry-compatibility)。

```bash
abx template deploy ./next-app -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create <template-id> --detach
abx run <sandbox-id> scaffold --arg kind=next --arg path=preview-app
abx run <sandbox-id> dev_start --arg kind=next --arg path=preview-app
abx run <sandbox-id> dev_logs
abx run <sandbox-id> dev_stop
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

客户端发行包为 `agent-sandbox-client`，导入 `agent_sandbox`。安装[配对 SDK](../docs/python-client-installation.md)，通过 sb.network.get_url(port) 获取平台真实转发地址。停止前先完成访问及文件保存。

```python
import asyncio
from urllib.parse import urlsplit
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        await sb.run("scaffold", kind="vite", path="preview-app")
        await sb.run("dev_start", kind="vite", path="preview-app",
                     allowed_host=urlsplit(sb.network.get_url(5173)).hostname)
        print(sb.network.get_url(5173))
        # Fetch/edit the preview before stopping it. Preserve desired source files.
        print(await sb.run("dev_logs", tail_bytes=4096))
        await sb.run("dev_stop")
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

将 ABX_SERVER_URL 设置为 SDK9000地址。命令服务鉴权使用启动前配置的 ABX_SERVER_TOKEN；预热进程配置见[运行环境](../docs/runtime-environment.md)。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/scaffold" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"kind":"next","path":"preview-app"}'
```

成功响应 {"result":{"path":"preview-app","kind":"next"}}。随后以相同参数调用 /commands/dev_start，访问 SDK3000地址，最后调用 /commands/dev_stop，参数 {}。缺失参数400，未知命令404，运行错误500。客户端超时不保证取消。

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

版本1.1.0为Vite新增准确SDK转发主机名 allowed_host。默认空值保留本机域名权限；传入 urlsplit(sb.network.get_url(5173)).hostname，仅设置固定Vite8.3.4源码及[官方文档](https://vite.dev/config/server-options#server-allowedhosts)支持的 __VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS。拒绝通配符、前导点后缀、协议、端口、凭据、逗号及空DNS标签。Next不接受此Vite专用设置。原1.0.0真实转发Vite403仍为失败；1.1.0需要新镜像/提供方验收。不改写Host，也不开全域允许。

## 配置

| 名称 | 默认值 | 用途 |
|---|---|---|
| ABX_SERVER_TOKEN | 空 | 命令接口 Bearer 鉴权，必须在进程启动前提供 |
| ABX_SERVER_PORT | 9000 | 本地命令服务端口 |
| WORKSPACE | /home/user/app | 已存在工作区 |
| NEXT_APP_TOOLCHAIN | /opt/next-app | 可信固定工具链；本机测试可指向安装目录 |

开发进程只继承 Node PATH、私有临时 HOME、语言、遥测关闭和所有权标记，不传入云端或模型密钥。预览应用无单独密码，应使用平台访问控制。日志可能包含应用数据，不可直接发布含隐私的日志。

## 资源

2vCPU、2048MB，平台根文件系统约10GiB，端口9000/3000/5173。不需要 Docker、KVM、显示器。Linux pidfd/procfs 用于身份安全的清理；停止所有权标记的派生进程和未回收主进程组，并独立确认内核监听不存在。

## 已验证

版本1.1.0通过真实SDK创建的极速版已验证镜像注册、原生CLI/SDK自测、完整HTTP6 PASS/0 FAIL/0 SKIP，以及3000/5173独立转发HTTP。两个真实应用都返回SDK写入的新源码标记，再完成自有进程/项目停止及删除。沙箱/模板/镜像仓库清理和运行后摘要独立回查通过。Vite仅允许准确SDK域名。默认FC响应仍把HTML标为附件；浏览器渲染及WebSocket/HMR明确为NOT_RUN，其他提供方也未验证。

| Version | Provider | Evidence |
| --- | --- | --- |
| 1.1.0 | alicloud-express | [SDK-created image](evidence/express-2026-10-20.json), [HTTP6](evidence/image-http-2026-10-20T102030Z.json), [independent forwarded source edits](evidence/forwarded-http-2026-10-20T102030Z.json) |

## 二次开发

通过 SDK 文件接口修改 app/page.js 或 index.html，再次访问预览。升级包时保持明确版本并重建锁文件。参考[Next 官方安装](https://nextjs.org/docs/app/getting-started/installation)及[Vite 指南](https://vite.dev/guide/)。开发服务器会执行应用源码，本包装不构成额外安全隔离。

## 贡献

阅读[贡献指南](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计](../docs/design/next-app.md)。完成真实进程回归、HTTP L0、实际镜像 L1、云端 L2 后再声明对应平台通过；保留失败和独立清理记录。

## 问题反馈

[模板 Issue54](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/54)，[Python SDK/服务端](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI 问题标题使用 [templates] 前缀。

## 许可证

仓库源码 Apache-2.0，见 [LICENSE](../LICENSE)。Next、React、Vite 为 MIT，来源固定在 upstream-pins.json，传递依赖许可证随 node_modules 保留。

FC把HTML标为附件时，可在启动自有应用后使用[SDK本地中继](../docs/preview-proxy.zh-CN.md)：python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 3000（Next）或--remote-port 5173（Vite）。Vite仍传入前述准确allowed_host。中继借用该沙箱；结束时停止中继并显式停止/销毁自有应用资源。Next/Vite此浏览器入口仅完成源码检查，浏览器及HMR未单独认证。

### 当前版本新增平台 step 验收

[真实原生 step](evidence/express-2026-10-20T130712Z.json)：官方 READY、Python SDK 创建、当前 CLI/SDK 冒烟，以及独立确认所拥有沙箱/模板已清理。[完整外部 HTTP](evidence/full-http-steps-2026-10-20T130712Z.json)：6 通过、0 失败、0 跳过。
