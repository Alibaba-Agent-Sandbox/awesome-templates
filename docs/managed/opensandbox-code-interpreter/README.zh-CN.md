# opensandbox-code-interpreter

[English](README.md)

## 做什么

在 OpenSandbox 服务上使用上游 Code Interpreter 镜像。

## 技术栈

镜像为 `opensandbox/code-interpreter:v1.1.0`；[上游示例](https://github.com/opensandbox-group/OpenSandbox/blob/30348cbdfe4b9cfd49e0963617aed357a8f1ac4c/docs/examples/code-interpreter.md)介绍其原生运行时。镜像由上游维护。

## 解决的问题

通过 Agent Sandbox 操作 shell 和文件，或通过上游 SDK 使用原生解释器上下文。

## 快速开始（CLI）

此直接启动示例需要支持规范 5 的 CLI 和同步更新后的托管目录。兼容版本及目录配套上线前，按[固定源码安装说明](../../using-templates.zh-CN.md)准备。下方历史记录验证的是其原 create/exec 接口，不表示已重新验证本次新的目录启动命令。

安装 [CLI](../../using-templates.zh-CN.md) 和 Node.js 22+，完成下方平台配置，将 `<sandbox-id>` 替换为创建时返回的实例 ID。

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//opensandbox --allow-unpinned --yes
abx provider doctor opensandbox
abx --provider opensandbox template launch opensandbox-code-interpreter --sandbox-timeout 180 --yes
abx --provider opensandbox exec <sandbox-id> -- python3 -c 'print(6*7)'
abx --provider opensandbox kill <sandbox-id> -y
```

## 快速开始（Python SDK）

安装 [Python 客户端](../../python-client-installation.md)及相同的提供商插件，并确保提供商引擎能从 PATH 找到 Node.js。

```python
import asyncio
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.create(provider="opensandbox", template="opensandbox/code-interpreter:v1.1.0", timeout=180)
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

### 使用原生解释器 SDK

持久 Python 上下文使用上游 OpenSandbox SDK。按[复现工作流](../../../.github/workflows/managed-opensandbox.yml)中的命令和锁文件安装固定的上游 SDK 依赖，并安装[公开 Python 客户端](../../python-client-installation.md)。下面显式启动镜像内的原生解释器服务，并让上游 SDK 连接同一个实例。

```python
import asyncio, os
from datetime import timedelta
from urllib.parse import urlsplit
from opensandbox import Sandbox as NativeSandbox
from opensandbox.config import ConnectionConfig
from code_interpreter import CodeInterpreter, SupportedLanguage
from agent_sandbox import ProviderSandbox

async def main():
    provider = "opensandbox"
    sb = await ProviderSandbox.create(provider=provider, template="opensandbox/code-interpreter:v1.1.0", timeout=600, cpu=2, memory=3072,
        provider_options={"entrypoint": "/opt/code-interpreter/code-interpreter.sh"},
        envs={"PYTHON_VERSION": "3.11", "JAVA_VERSION": "17", "NODE_VERSION": "20", "GO_VERSION": "1.24"},
        )
    sid = sb.id
    try:
        url = urlsplit(os.environ.get("ABX_OPENSANDBOX_BASE_URL", "http://127.0.0.1:8080"))
        config = ConnectionConfig(domain=url.netloc, protocol=url.scheme,
            api_key=os.environ.get("ABX_OPENSANDBOX_API_KEY") or os.environ.get("OPEN_SANDBOX_API_KEY"),
            use_server_proxy=True, request_timeout=timedelta(seconds=60))
        native = await NativeSandbox.connect(sid, connection_config=config)
        try:
            interpreter = await CodeInterpreter.create(sandbox=native, ready_timeout=timedelta(seconds=120))
            try:
                context = await interpreter.codes.create_context(SupportedLanguage.PYTHON)
                first = await interpreter.codes.run("value = 37\nvalue", context=context)
                print(first.result[0].text)  # 37
                second = await interpreter.codes.run("value + 5", context=context)
                print(second.result[0].text)  # 42
                await interpreter.codes.delete_context(context.id)
            finally:
                await interpreter.aclose()
        finally:
            await native.close()
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())
```

项目的 OpenSandbox `ProviderSandbox.run_code` 适配仍未实现（`E8004`）。原生会话使用上面的 `interpreter.codes`。

## 快速开始（HTTP POST）

该镜像不包含项目的 `/commands/*` 应用服务。生命周期、进程与文件操作使用提供商 SDK；原生代码会话使用上游解释器 SDK。

## 命令参考

`ProviderSandbox.create` 创建实例；`commands.run` 返回 `exit_code/stdout/stderr`；`files.write/read/remove` 操作文件；`kill` 删除实例，`close` 释放本地连接。

## 配置

将 `ABX_OPENSANDBOX_BASE_URL` 设为服务根地址；服务需要密钥时配置 `ABX_OPENSANDBOX_API_KEY`。默认进程保活实例以便执行命令和操作文件。启动原生解释器时，按上方示例传入 `provider_options={"entrypoint": "/opt/code-interpreter/code-interpreter.sh"}`；使用 CLI 创建时，将 `ABX_OPENSANDBOX_ENTRYPOINT` 设为该脚本路径。

该提供商需要支持 `argv` 请求的 execd；[复现工作流](../../../.github/workflows/managed-opensandbox.yml)固定了已验证的 release-1.1.1 execd 镜像摘要。它与解释器镜像 `v1.1.0` 是两个独立组件；旧 execd `v1.1.0` 不适用于当前提供商。

## 资源

超时单位为秒。CPU、内存和镜像可用性取决于部署配置；用完后删除实例。

## 已验证

[2026-10-24 运行记录](../../../.agents/evidence/verify/2026-10-24-managed-native-pass.json)分别验证了默认实例创建和执行，以及显式启动原生解释器后的 Jupyter 健康、Python 持久/隔离上下文、程序异常和删除清理。两类实例均独立确认已删除。原始依赖版本与镜像摘要保留在记录中；[2026-10-21 历史记录](../evidence/verification-opensandbox-code-interpreter-2026-10-21-native-docker.json)也原样保留。

## 二次开发

定制上游镜像，或从[源码模板](../../../_skeleton/README.zh-CN.md)构建项目命令服务；原生解释器服务需要明确指定启动入口。

## 贡献

遵循[贡献规范](../../../CONTRIBUTING.zh-CN.md)，保持双语一致，保留带日期的测试记录。

## 问题反馈

[反馈模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)；提供商集成问题见 [awesome-providers](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues)。

## 许可证

本仓库文档和测试采用 Apache-2.0；上游镜像、SDK 和内置应用保留各自许可证与条款。
