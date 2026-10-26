# base

[English](README.md)

## 做什么

阿里云极速版提供的 `base` 托管模板。直接创建实例即可使用，无需构建镜像。

## 技术栈

托管镜像提供 Python 3.13、Node.js 20。提供方会更新镜像；业务依赖特定版本时，请查询实例内的实际版本。

## 解决的问题

无需准备镜像，即可执行 shell 命令和操作文件。

## 快速开始（CLI）

执行 CLI 启动或 Python 创建前，先在本地终端配置以下变量。三项值从阿里云极速版控制台取得，必须属于**同一地域**，API Key 需要有目标托管模板的访问权限。

```bash
export ABX_SANDBOX_API_KEY='<sandbox-api-key>'
export ABX_SANDBOX_BASE_URL='<sandbox-api-url>'
export ABX_SANDBOX_DOMAIN='<sandbox-domain>'
```

三个占位符分别替换为 Sandbox API Key、API URL 和沙箱域名；域名填主机名，不填 URL。这些是平台凭据，不是模型 API Key。本例不需要模型、模型 endpoint、模型密钥、应用令牌或交互登录。直接创建已有托管镜像，无需 Docker、ACR namespace 或镜像构建 AccessKey。账号配置差异见[平台配置指南](../../using-templates.zh-CN.md)。

使用 CLI 0.5.6 或更高版本和当前托管目录，按[安装与平台配置说明](../../using-templates.zh-CN.md)准备。

先完成 [CLI 安装和平台配置](../../using-templates.zh-CN.md)，将 `<sandbox-id>` 替换为创建时返回的实例 ID。

```bash
abx --provider alicloud-express template launch base --sandbox-timeout 180 --yes
export ABX_SANDBOX_ID="<返回的沙箱ID>"
abx --provider alicloud-express exec "$ABX_SANDBOX_ID" -- python3 -c 'print(6*7)'
abx --provider alicloud-express kill "$ABX_SANDBOX_ID"
```

## 快速开始（Python SDK）

安装 [Python 客户端](../../python-client-installation.md)，配置相同的极速版账号。下面打印 `42`，读写文件，并在结束后删除本次创建的沙箱。

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="alicloud-express", template="base", timeout=180)
    try:
        result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
        print(result.stdout)  # 42
        await sb.files.write("/tmp/example.txt", "hello")
        print(await sb.files.read("/tmp/example.txt"))
        await sb.files.remove("/tmp/example.txt")
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

该托管镜像不提供项目的 `/commands/*` 应用服务。使用上面的进程和文件 API；需要自定义 HTTP 命令时，从[源码模板](../../../_skeleton/README.zh-CN.md)开始。

## 命令参考

`ProviderSandbox.create(provider=..., template=..., timeout=...)` 创建实例；`commands.run` 返回 `exit_code`、`stdout`、`stderr`；`files.write/read/remove` 操作沙箱内文件。`kill` 删除实例，`close` 释放本地连接。

当前极速版提供商未实现 `ProviderSandbox.run_code`（`E8004`）。运行 Python 进程请使用上面的 `commands.run`；持久内核或解释器会话需要对应的已接入接口。

## 配置

按[使用指南](../../using-templates.zh-CN.md)配置极速版账号。本例不需要模型密钥；预热进程的环境变量规则见[运行环境](../../runtime-environment.zh-CN.md)。

## 资源

设置有限的超时时间（秒），结束后删除实例。CPU、内存与镜像更新由平台管理。

## 贡献

遵循[贡献规范](../../../CONTRIBUTING.zh-CN.md)。保持中英文一致，新运行新增带日期的记录。

## 问题反馈

[反馈模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。

## 许可证

文档与验证脚本采用 Apache-2.0；托管镜像及内置软件保留各自许可证。
