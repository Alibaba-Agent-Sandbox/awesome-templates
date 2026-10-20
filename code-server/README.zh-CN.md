# code-server

## 做什么

在沙箱里运行固定版 code-server 浏览器 IDE。必须密码认证，支持独立启动、状态和停止；配置、用户数据和扩展目录均隔离，不修改调用者原有 IDE 配置。

## 技术栈

阿里云 FC base v0.0.49；官方 code-server4.141.0 Linux x86_64/aarch64 独立包，包含上游 Node/VS Code 运行时。[assets.json](assets.json) 固定下载地址、准确字节数和官方 SHA256。保留包内许可证。服务端 SDK 固定提交 e2cb27e；generation2，非 root user。

## 解决的问题

给需要浏览器编辑工作区的用户提供真实 VS Code 界面，无需本地 Docker、KVM、桌面显示器或模型密钥。

## 快速开始（CLI）

下列使用原生 CLI 语法；[标准入口兼容说明](../docs/using-templates.md#client-entry-compatibility)。私人密码可通过 SDK 进程环境读取后传入。

```bash
abx template deploy ./code-server -y
abx create --template <template-id> --timeout 300 -y
abx run <sandbox-id> code_server_version
abx run <sandbox-id> code_server_self_test
abx run <sandbox-id> code_server_start --arg 'password=<your-private-12-byte-or-longer-password>'
abx run <sandbox-id> code_server_status
abx run <sandbox-id> code_server_stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

Install the [paired `agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        await sb.run("code_server_start", password=os.environ["CODE_SERVER_PASSWORD"])
        print(sb.network.get_url(8443))
        # Open this URL in your browser and log in with the same private password.
        # Export any workspace files you need before destroying the sandbox.
        await asyncio.to_thread(input, "Press Enter when finished editing: ")
        await sb.run("code_server_stop")
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' -d '{}' \
  '<sandbox-port-9000-url>/commands/code_server_self_test'
```

Response: `{"result":"CODE_SERVER_OK"}`. The IDE is a separate password-protected HTTP/WebSocket service on8443.

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| code_server_version | none | actual installed version string |
| code_server_start | password: str optional empty=server CODE_SERVER_PASSWORD; port: int=8443,1024..65535 excluding9000; cwd: str empty=WORKSPACE,existing workspace directory; timeout_s: int=60,1..120 | {port,running:true,auth:password} after actual health |
| code_server_status | none | {running:false}, or {running:true,port,auth:password} |
| code_server_stop | none | {running:false} only after owned processes exit, kernel listener absence and private-state cleanup |
| code_server_self_test | none; existing owned IDE must be stopped | CODE_SERVER_OK after real password rejection/login/workbench and cleanup |

密码必须12..256个 UTF-8 字节且不含 NUL。启动已占用端口或重复启动均拒绝；停止不会按进程名批量杀服务。异常启动/停止不发布成功状态。上游子进程继承本次随机归属标识，使用 Linux pidfd 固定身份再清理；退出后回查内核监听表。

## 配置

保留上游 TLS 校验的 SDK 本机预览见[操作指南](../docs/preview-proxy.zh-CN.md)。控制器明确区分直接域名和 sdk-local 两种结果。


WORKSPACE 默认 /home/user/app。CODE_SERVER_PASSWORD、ABX_SERVER_TOKEN 都是空占位符；前者也可逐次传 password 参数，后者只保护9000命令 API，不替代8443的 IDE 密码。预热服务的环境设置见[运行环境](../docs/runtime-environment.md)。配置文件权限0600，私有目录0700；不把云或模型密钥传入 IDE 进程。服务端关闭更新检查与遥测。

## 资源

2vCPU、2048MB；9000 为命令 API，8443 为 IDE。其他自选端口只保证本地监听，外部暴露需提供方配置。安装时以 du -sx 检查镜像可见根文件系统不超过8GiB；下载最多240秒，单包大小严格匹配。启动最多120秒；检查、子进程与输出均有界。停止清理本次 IDE 的配置/用户数据/扩展，工作区文件保留。

## 已验证

尚未记录任何通过的提供方测试。

### 真实浏览器、终端与编辑器检查

安装 Playwright1.58.0、其 Chromium 和 `certutil`（Debian/Ubuntu 包名
`libnss3-tools`）。在调用方独占且没有运行中 IDE 的沙箱上执行
`python code-server/browser_e2e_test.py --sandbox-id <sandbox-id>`。
控制器通过 SDK 返回的8443地址登录，加载工作台 JavaScript，经终端 WebSocket
写随机文件、files SDK 独立读回，再在浏览器编辑器修改、保存并独立读回。
它停止自己启动的 IDE、删除随机文件；调用方仍需负责销毁沙箱。

全程开启 TLS 校验。Chromium 的临时私有 HOME/NSS 仅导入 Python 默认 SSL
上下文已经信任的操作端 CA，保留原有浏览器配置，浏览器子进程不继承云端或
模型凭据。网络使用私有 CA 时，先配置操作端受信证书库，不绕过证书校验。
本机浏览器回归明确使用本地文件观察器，不作为云端或 SDK 验收。清理未确认
时不能返回通过。

### 默认域名的浏览器访问前提

当前默认 FC 域名上的真实最小 HTML 服务返回 HTTP200/text-html，但响应被加入
`Content-Disposition: attachment`；真实 Chromium 因此开始下载，TLS 校验始终
开启。[完整独立对照](evidence/preview-header-control-2026-10-20T060339Z.json)
还确认了测试沙箱列表及单独GET均已不存在。这与[官方默认域名限制](https://www.alibabacloud.com/help/en/functioncompute/web-functions)一致。

交互式浏览器使用前，需要绑定提供方支持的自定义预览域名与有效证书，再让
SDK 使用提供方返回的域名。只替换主机名字符串不会建立绑定。之后对该 SDK
URL 重跑浏览器控制器。控制器会提前诊断强制 HTML 下载，并清理自己启动的
IDE；前面的 CLI/SDK 示例用于浏览器访问时也需要这个前提。

[真实镜像尝试](evidence/image-attempt-2026-10-20T055537Z.json)的完整 HTTP5 项
通过，但[真实浏览器 UI 未通过](evidence/browser-ui-2026-10-20T055537Z.json)。
沙箱、模板及镜像仓库均已独立确认清理；因此尚未取得完整浏览器 IDE 提供方
验收，Issue53 保持未关闭。

## 二次开发

本地验证可把 install_runtime.py 的 --prefix 指向自己的工具目录；镜像构建显式启用 --check-rootfs，以免把 Docker 宿主机的 statvfs 使用量误当成镜像大小。部署可用[平台 steps](../docs/platform-steps.zh-CN.md)：`python scripts/prepare_steps.py code-server --output /tmp/ide-steps`，真实验收 `python scripts/run_steps_e2e.py code-server`。修改版本时同步资产哈希、实际版本检查与双语文档。WebSocket/终端交互须单独记录，认证页面成功不能推断它们通过。

## 贡献

遵循[贡献规范](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计](../docs/design/code-server.md)。用真实密码会话、错误密码、跨请求状态和内核/进程回查测试，不接受空端口 TCP 连接成功作为监听证明。

## 问题反馈

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53)；CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)；SDK：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板：Apache-2.0；code-server：MIT。保留官方发行包中的 LICENSE 和第三方声明，包括随包 VS Code/Node 组件的声明。用户安装的扩展各自遵守许可证。上游：[coder/code-server](https://github.com/coder/code-server/releases/tag/v4.141.0)。
