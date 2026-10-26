# 在启动前配置模板应用

[English](runtime-environment.md)

由一个入口负责启动：`abx template launch` 准备模板并启动其声明的应用。SDK 连接这个已运行的沙箱，调用命名命令。模型配置和 `ABX_SERVER_TOKEN` 必须在应用进程导入模板前传入；再连接一个客户端不会重新配置已有进程。

## 启动一次，再连接使用

先完成[安装和提供方配置](using-templates.zh-CN.md#安装)。以下示例使用已发布的 CLI 0.5.6、Python 客户端 0.4.0a6 和 `python-hello` 模板。配置极速版，并在启动前将 `ABX_SERVER_TOKEN` 安全地设置到本地环境。模型模板还需要按其 README 设置声明的配置项；`template.yaml` 中声明空值并不提供密钥。

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
```

将返回的沙箱 ID 填入下面示例，提供方和应用令牌与启动时保持一致。应用已在声明的 9000 端口运行；连接时不会启动另一个服务。

```python
import asyncio
import os

from agent_sandbox import ProviderSandbox


async def main():
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()


asyncio.run(main())
```

预期结果为 `Hello, Ada!`。使用 OpenSandbox 时，先完成其[提供方配置](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)，启动选择 `--provider opensandbox`，连接选择 `provider="opensandbox"`。其他模板使用其实际服务端口和命令名。CLI 调用、HTTP POST 和清理参见[完整调用示例](using-templates.zh-CN.md)。

`client.aclose()` 和 `sb.close()` 关闭客户端资源，不删除沙箱。使用结束后，资源所有者用 `abx --provider alicloud-express kill <sandbox-id>` 删除该实例，并单独清理不再需要的确切自有准备模板和镜像。消费已运行应用的 API 不需要再创建沙箱。

## 启动配置与认证

模板的启动命令和声明的服务应由同一个入口管理。缺少模型配置时，检查模板文档中的只读配置诊断命令及启动配置，不要为了绕过失败检查再启动第二个命令服务。从已准备引用创建实例属于高级启动路径；已有应用启动后，不应再由另一个入口重复启动。作者按现有 [SDK 模板编写指南](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/docs/zh/guide/authoring-templates.md) 开发即可。

应用进程启动时读取 `ABX_SERVER_TOKEN`。值非空时保护命名命令调用；未设置时应用允许匿名调用。之后的 create/connect 调用不能为已运行进程补上认证。`/health` 不要求应用令牌，但提供方网关仍可能要求自己的认证。health 成功不证明命令认证或模型配置正确。

应用令牌、提供方网关凭据和上游模型密钥各有用途。`application_client(..., token=...)` 保留提供方网关访问头，并通过支持的请求头发送应用令牌。不要记录令牌，也不要把模型密钥放进命令参数、提示词或镜像层。具体请求头行为见[认证规范](template-spec.zh-CN.md#认证令牌)。
