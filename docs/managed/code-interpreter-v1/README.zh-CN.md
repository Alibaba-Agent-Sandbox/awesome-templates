# code-interpreter-v1

[English](README.md)

## 做什么

阿里云极速版提供的 `code-interpreter-v1` 托管模板。直接创建实例即可使用，无需构建镜像。

## 技术栈

托管镜像提供 Python 3.13、Node.js 20，以及 numpy、pandas、matplotlib。提供方会更新镜像；业务依赖特定版本时，请查询实例内的实际版本。

## 解决的问题

使用预装的数值计算包进行 Python 数据处理。

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
abx --provider alicloud-express template launch code-interpreter-v1 --sandbox-timeout 180 --yes
export ABX_SANDBOX_ID="<返回的沙箱ID>"
abx --provider alicloud-express exec "$ABX_SANDBOX_ID" -- python3 -c 'import pandas as pd; print(int(pd.DataFrame({"amount": [12, 30]})["amount"].sum()))'
abx --provider alicloud-express kill "$ABX_SANDBOX_ID"
```

## 快速开始（Python SDK）

安装 [Python 客户端](../../python-client-installation.md)，配置相同的极速版账号。下面打印 `42`，读写文件，并在结束后删除本次创建的沙箱。

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="alicloud-express", template="code-interpreter-v1", timeout=180)
    try:
        result = await sb.commands.run(
            "python3 -c 'import pandas as pd; print(int(pd.DataFrame({\"amount\": [12, 30]})[\"amount\"].sum()))'",
            timeout=30,
        )
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

### 持久 Python、数据表与图表

持久 Python context 使用独立的公开入口
`agent_sandbox.code_interpreter.AsyncSandbox`。[expenses.py](expenses.py)
显式传入极速版兼容 API Key、API URL 和域名，与 CLI 使用相同地域和账号。
脚本会创建自己的实例，不会连接 CLI 示例中已经删除的实例。

将 [expenses.py](expenses.py) 下载到终端当前目录，在已安装客户端的环境运行
`python expenses.py`。它通过 pandas 汇总三个月的金额，下载
`expenses-summary.json` 和 600×300 的 `expenses.png`，最后在 `finally` 中删除实例。
预期汇总：`{"rows": 3, "total": "51.30", "total_cents": 5130}`。
本机无需安装 pandas 或 matplotlib，计算发生在托管实例内。

对于名为 `sb` 的 `AsyncSandbox` 实例，先执行
`await sb.run_code("value = 41")`，再执行 `await sb.run_code("value + 1")`，
状态会保留，返回文本 `42`。使用
`context = await sb.create_code_context(language="python")` 创建隔离状态，
调用 `run_code` 时传入 `context=context`。`list_code_contexts()` 列出 context；
`remove_code_context(context)` 删除本次创建的 context。
每次调用后先检查 `execution.error`，再使用 `execution.text` 或生成文件。
`on_stdout`、`on_stderr`、`on_result`、`on_error` 回调分别接收输出、结果和错误；
输出消息的文本位于 `.line`。

图表使用 matplotlib 的 `Agg` 后端和 `savefig`，随后通过
`files.read(..., format="bytes")` 下载。不要依赖 `plt.show()` 返回内联 PNG，
也不要使用 IPython 魔法命令。当前托管服务将 Python 异常的名称报告为
`ExecutionError`，原始异常保存在 `.value`；读取该内容，不要假定
`.name == "ValueError"`。

当前托管持久解释器在 Python 异常后会再次执行代码：先递增文件计数再
`raise ValueError(...)`，会递增两次。不要在可能抛异常的代码中进行业务写入；
需要只执行一次的任务使用上面的 `ProviderSandbox.commands.run` 进程入口，
并检查退出码。此平台缺陷尚未满足完整解释器验收条件。

## 快速开始（HTTP POST）

该托管镜像不提供项目的 `/commands/*` 应用服务。使用上面的进程和文件 API；需要自定义 HTTP 命令时，从[源码模板](../../../_skeleton/README.zh-CN.md)开始。

## 命令参考

`ProviderSandbox.create(provider=..., template=..., timeout=...)` 创建实例；`commands.run` 返回 `exit_code`、`stdout`、`stderr`；`files.write/read/remove` 操作沙箱内文件。`kill` 删除实例，`close` 释放本地连接。

当前极速版提供商未实现 `ProviderSandbox.run_code`（`E8004`）。独立进程使用 `commands.run`；持久 Python context 使用上述独立的 `agent_sandbox.code_interpreter.AsyncSandbox` API。这是两个不同的客户端接口。

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
