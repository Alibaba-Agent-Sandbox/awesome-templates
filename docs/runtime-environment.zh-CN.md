# 配置应用运行环境

[English](runtime-environment.md)

`abx deploy .` 准备可复用的 Sandbox 模板并部署声明的 Serving 资源。普通源码模板自带 `run.py`，用于创建动态实例，并携带运行时凭据启动应用。先完成[安装](using-templates.zh-CN.md#安装)，再按所选模板 README 操作。

```bash
abx deploy . --yes
python3 run.py --template <prepared-template-id> --timeout 1800
```

`run.py` 保留该模板的应用启动命令，只传递 `RUNTIME_ENV_NAMES` 声明的变量，等待服务健康检查并验证带认证的命令发现。运行前导出文档要求的模型 Key、端点及模型配置。镜像默认值仍在 Dockerfile 中；启动后修改本机环境不会重新配置已运行的应用。

没有指定 `ABX_SERVER_TOKEN` 时，脚本自动生成独立应用令牌，将令牌、Provider 和已确认的 Sandbox ID 写入仅文件所有者可读写的 `.sandbox-session.json`。此私有文件已加入 Git 忽略列表。脚本不会覆盖已有会话文件；第二个实例可用 `--session` 指定新路径。启动失败时会尝试删除本次创建的实例；清理需要重试时保留会话文件。

后续 CLI 调用可读取令牌而不在终端显示它：

```bash
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
```

Python 客户端可直接读取私有文件：

```python
import asyncio
import json
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    session = json.loads(Path(".sandbox-session.json").read_text())
    sb = await ProviderSandbox.connect(session["sandbox_id"], provider=session["provider"])
    try:
        client = await sb.application_client(9000, token=session["application_token"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

上述命令适用于 `python-hello`，其他模板使用各自命令和端口。关闭客户端不会删除实例。先导出文件，再执行 `abx --provider alicloud-express sandbox delete <sandbox-id> --yes`；实例删除后再删除对应私有会话文件。准备好的模板和镜像有独立生命周期。

Sandbox 平台 Key、应用令牌和模型 Key 用于不同系统。仅 `/health` 成功不能证明应用认证有效；SDK 在保留 Provider 网关认证的同时添加应用令牌。参见[认证约定](template-spec.zh-CN.md#认证令牌)和 [CLI、SDK 与 HTTP](using-templates.zh-CN.md#clisdk-与-http)。
