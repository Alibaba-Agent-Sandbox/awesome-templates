# Crush

[English](README.md).

## 做什么

运行官方原生Crush0.98.1，显式配置兼容OpenAI的提供方。默认无工具；allow_tools=true仅启用bash/edit/multiedit/view/write/ls/glob/grep八项。禁用子Agent、MCP、联网抓取、后台任务及LSP工具。

## 技术栈

阿里云FC generation2 CPU、非root user、SDK固定e2cb27e。[assets.json](assets.json)固定官方GNU Linux x86_64/aarch64下载长度与SHA256，源码[8b1824282eccc78cc62c188c245cf375230a18ce](https://github.com/charmbracelet/crush/tree/8b1824282eccc78cc62c188c245cf375230a18ce)。arm64固定版本不等于已验证运行。

## 解决的问题

在自有沙箱通过真实终端Agent编辑项目，每次使用独立配置和数据。本模板仅支持显式兼容提供方CLI模式；交互UI、调用者已有配置和其他上游提供方未认证。

## 快速开始（CLI）

```bash
abx template deploy ./crush -y
abx create <template-id> --detach --timeout 900
abx run <sandbox-id> crush_version
abx run <sandbox-id> crush_setup_check
abx kill <sandbox-id>
abx template delete <template-id> -y
```

deploy返回模板ID，create返回自有沙箱ID。version/setup无需模型密钥。[入口兼容及提供方配置](../docs/using-templates.md#client-entry-compatibility)。模型配置必须进入运行中的命令服务，create环境不能重新配置预热服务。

## 快速开始（Python SDK）

按[固定客户端安装说明](../docs/python-client-installation.md)安装agent-sandbox-client，在操作者环境设置三个CRUSH变量：

```python
import asyncio
import os
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900)
    server = None
    try:
        server = await sb.start_server(
            port=9010, commands="/home/user/app/commands.py", timeout=60,
            token=secrets.token_urlsafe(32),
            env={"CRUSH_API_KEY": os.environ["CRUSH_API_KEY"],
                 "CRUSH_BASE_URL": os.environ["CRUSH_BASE_URL"],
                 "CRUSH_MODEL": os.environ["CRUSH_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "crush", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("Crush failed; inspect the private returned diagnostics")
        print(await sb.files.read("/home/user/app/HELLO.txt"))
    finally:
        try:
            if server is not None:
                await server.aclose()
            await sb.kill()
        finally:
            await sb.close()

asyncio.run(main())

```

新建9010服务使用随机令牌，导出文件后仅销毁本次自有沙箱。示例完成源码检查，不自动构成云端/模型验收。启动服务保留镜像PATH；显式覆盖时包含/opt/crush。

## 快速开始（HTTP POST）

ABX_SERVER_URL为SDK转发的9010地址，ABX_SERVER_TOKEN为该服务随机令牌。

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/crush" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

HTTP200返回{"result":{"stdout":"42","stderr":"","exit_code":0}}，保留非零退出码。缺失/未声明/类型错误参数400，认证401，未知命令404，路径/配置/限制/版本或超时500。结果缓冲；客户端超时/断连不保证取消原生进程。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| crush_version | none | actual pinned0.98.1 string |
| crush_setup_check | none | installed/version/api_key_set/base_url_set/model_set; read-only flags |
| crush | prompt:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

实际argv：crush run --quiet --model owned/ID --small-model owned/ID --cwd DIRECTORY --data-dir PRIVATE。提示通过私有文件stdin输入。CRUSH_CLIENT_SERVER=false选择前台模式。默认禁用全部29项原生工具，显式许可仅开放上述八项。成功、失败、超时、输出溢出均清理自有进程组及身份固定的标记子进程。同用户恶意程序、主动擦除归属标记或服务SIGKILL仍需销毁整个沙箱。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| CRUSH_API_KEY | model calls | empty | explicit compatible-provider credential |
| CRUSH_BASE_URL | model calls | empty | HTTP(S) endpoint; no userinfo/query/fragment |
| CRUSH_MODEL | model calls | empty | bounded native model identifier |
| WORKSPACE | no | /home/user/app | existing caller workspace |
| ABX_SERVER_TOKEN | no | empty | server process bearer token |
| CRUSH_BINARY | diagnostics | image PATH | binary override; actual version still checked |

独立HOME/XDG/CRUSH配置数据目录，使用原生禁用默认提供方及自动更新开关。上游自动读取项目配置，因此cwd至最近Git根目录间存在.crushrc/crushrc/.crush.json/crush.json时，在运行前拒绝，保留调用者原文件；无Git时只检查cwd。子进程仅继承PATH/可选CA和私有运行设置，排除云/GitHub/服务密钥。显式模型密钥与地址写入私有0600配置，返回诊断替换其完整值；项目输出仍可能含项目私密内容。

## 资源

2vCPU/2048MB，命令端口9000，可显式启动9010。x64压缩包约26.8MB；下载预算240秒、套接字30秒，单执行文件上限400MiB；构建根文件系统8GiB门禁。提示256KiB，每路输出256KiB，执行1..1800秒另加有限清理时间。不虚构原生max-turn参数；单响应8192 token及执行截止时间约束运行。每次删除私有配置/会话数据，项目修改保留至调用者清理。

## 已验证

当前工作流清单尚无项目认可的验收收据。历史验收记录仅证明原输入和原调用路径；参见[工作流验证](../docs/workflows.zh-CN.md)。

## 二次开发

python crush/install_runtime.py --prefix <new-private-prefix>安装至新的私有目录。实际固定版本在PATH后运行python -m pytest -q crush/test_commands.py crush/test_controller.py。夹具使用人工编写HTTP及工具响应，不在操作者主机执行真实模型生成命令。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py crush --output /tmp/crush-steps仅生成步骤；python scripts/run_steps_e2e.py crush --timeout 1200才实际运行。真实模型验收设置E2E_REQUIRE_LLM=1和E2E_REQUIRE_CLI=1，静态标记不能替代L3。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/crush.md)，同步双语API、限制和不可变验证记录。

## 问题反馈

[模板Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65)；[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板封装代码为[Apache-2.0](../LICENSE)。Crush0.98.1为**FSL-1.1-MIT**，当前不能标为MIT或OSI批准开源。保留并阅读[上游原许可证](upstream-LICENSE.md)、未来许可生效日期及限制，不能推断商业再分发不受限制。安装未修改的官方二进制并保留捆绑声明，不包含模型权重。
