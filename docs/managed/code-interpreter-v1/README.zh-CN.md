# code-interpreter-v1

[English](README.md)

## 做什么

阿里云极速版提供的 `code-interpreter-v1` 托管模板。直接创建实例即可使用，无需构建镜像。

## 技术栈

[2026-10-19 清单](../evidence/code-interpreter-v1-2026-10-19T154153Z.json)记录了 Python 3.13、Node.js 20，以及 numpy、pandas、matplotlib。提供方会更新镜像；业务依赖特定版本时，请查询实例内的实际版本。

## 解决的问题

使用预装的数值计算包进行 Python 数据处理。

## 快速开始（CLI）

使用 CLI 0.5.1 或更高版本和当前托管目录，按[安装与平台配置说明](../../using-templates.zh-CN.md)准备。下方历史记录验证的是其原 create/exec 接口，不表示已重新验证本次目录启动命令。

先完成 [CLI 安装和平台配置](../../using-templates.zh-CN.md)，将 `<sandbox-id>` 替换为创建时返回的实例 ID。

```bash
abx --provider alicloud-express template launch code-interpreter-v1 --sandbox-timeout 180 --yes
abx --provider alicloud-express exec <sandbox-id> -- python3 -c 'print(6*7)'
abx --provider alicloud-express kill <sandbox-id>
```

## 快速开始（Python SDK）

安装 [Python 客户端](../../python-client-installation.md)，配置相同的极速版账号。下面打印 `42`，读写文件，并在结束后删除本次创建的沙箱。

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="alicloud-express", template="code-interpreter-v1", timeout=180)
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

## 已验证

[2026-10-25 官方 npm CLI 0.5.1／Python client 0.4.0a1 新安装验证](../evidence/public-npm-code-interpreter-v1-2026-10-25T115223Z.json)：通过默认公开目录启动，检查非 root 运行环境、CLI 输出 42、Python 文件写读删、CLI 删除与独立控制面确认实例不存在。另已实际导入 numpy／pandas／matplotlib 并计算 DataFrame 总和 42。这是进程与文件能力验证，不代表持久解释器会话验收。

[2026-10-24 公开包记录](../../../.agents/evidence/verify/2026-10-24-managed-public-cli.json)：CLI 0.4.16 实际创建、执行得到 `42`、删除；Python 0.3.1a5 文件读写删除、`ProviderSandbox.run_code` 明确返回 `E8004`，并独立确认实例已删除。[2026-10-19 历史记录](../evidence/code-interpreter-v1-2026-10-19T154153Z.json)保留原始版本与调用路径。

## 二次开发

需要额外依赖或自定义命令服务时，从[源码骨架](../../../_skeleton/README.zh-CN.md)创建独立模板。

## 贡献

遵循[贡献规范](../../../CONTRIBUTING.zh-CN.md)。保持中英文一致，新运行新增带日期的记录。

## 问题反馈

[反馈模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。

## 许可证

文档与验证脚本采用 Apache-2.0；托管镜像及内置软件保留各自许可证。
