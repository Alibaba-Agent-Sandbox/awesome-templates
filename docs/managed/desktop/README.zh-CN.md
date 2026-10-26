# desktop

[English](README.md)

## 做什么

使用 E2B 账号创建平台托管的 `desktop` 桌面实例。

## 技术栈

[E2B Desktop 源码](https://github.com/e2b-dev/desktop/tree/9fe5f55fabe3bd9f0277661a830e1d228b463b44)定义了 Ubuntu/Xfce 桌面环境；部署的模板由 E2B 管理。

## 解决的问题

使用现成的桌面环境。shell/文件通过 Agent Sandbox 操作；截图、桌面输入使用上游 E2B Desktop SDK。

## 快速开始（CLI）

运行下面命令前，从 E2B 账号取得 API Key，并在本地导出：

```bash
export ABX_E2B_API_KEY='<e2b-api-key>'
```

使用有权访问 `desktop` 模板的 Key。这是 E2B 平台认证；shell、文件和桌面访问不需要在沙箱中交互登录，也不需要模型 API Key、模型 endpoint 或应用令牌。自建 E2B 部署可能还需 `ABX_E2B_BASE_URL` 和 `ABX_E2B_DOMAIN`，按该部署实际值配置，不要传入阿里云极速版凭据。

使用 CLI 0.5.6 或更高版本和当前托管目录，按[安装与平台配置说明](../../using-templates.zh-CN.md)准备。

安装 [CLI](../../using-templates.zh-CN.md) 和 Node.js 22+，完成下方平台配置，将 `<sandbox-id>` 替换为创建时返回的实例 ID。

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//e2b --allow-unpinned --yes
abx provider doctor e2b
abx --provider e2b template launch desktop --sandbox-timeout 180 --yes
export ABX_SANDBOX_ID="<返回的沙箱ID>"
abx --provider e2b exec "$ABX_SANDBOX_ID" -- python3 -c 'print(6*7)'
abx --provider e2b kill "$ABX_SANDBOX_ID" -y
```

## 快速开始（Python SDK）

安装 [Python 客户端](../../python-client-installation.md)及相同的提供商插件，并确保提供商引擎能从 PATH 找到 Node.js。

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="e2b", template="desktop", timeout=180)
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

该镜像不包含项目的 `/commands/*` 应用服务。生命周期、进程与文件操作使用提供商 SDK；截图和桌面输入使用上游 Desktop SDK。

## 命令参考

`ProviderSandbox.create` 创建实例；`commands.run` 返回 `exit_code/stdout/stderr`；`files.write/read/remove` 操作文件；`kill` 删除实例，`close` 释放本地连接。

## 配置

将 `ABX_E2B_API_KEY` 设为 E2B 账号密钥。仅在部署需要时设置 `ABX_E2B_BASE_URL` 和 `ABX_E2B_DOMAIN`，详见 [E2B 提供商指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/tree/main/e2b)。

## 资源

超时单位为秒。CPU、内存和镜像可用性取决于部署配置；用完后删除实例。

## 贡献

遵循[贡献规范](../../../CONTRIBUTING.zh-CN.md)，保持双语一致，保留带日期的测试记录。

## 问题反馈

[反馈模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)；提供商集成问题见 [awesome-providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues)。

## 许可证

本仓库文档和测试采用 Apache-2.0；上游镜像、SDK 和内置应用保留各自许可证与条款。
