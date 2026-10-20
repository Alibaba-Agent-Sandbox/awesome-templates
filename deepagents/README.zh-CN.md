# DeepAgents

[English](README.md).

## 做什么

运行真实DeepAgents0.7.25本地文件/shell后端及显式兼容OpenAI聊天模型。默认不开放工具；allow_tools=true仅启用ls/read_file/write_file/edit_file/glob/grep/execute/delete八项。关闭通用及显式子Agent，工具中没有task/委派。

## 技术栈

阿里云FC、generation2、非root user、SDK固定e2cb27e。[requirements.lock](requirements.lock)固定全部解析依赖及SHA256，包括[DeepAgents0.7.25](https://pypi.org/project/deepagents/0.7.25/)与langchain-openai1.7.2。由[requirements.in](requirements.in)通过uv0.11.28/Python3.13生成；镜像安装校验哈希并执行pip check。无远程E2B/OpenSandbox后端或模型权重。

## 解决的问题

让真实LangChain Deep Agent在自有沙箱中执行文件/shell操作，不额外创建远程沙箱。采用已验证Python API短驱动，不假设存在控制台入口。每次独立进程、模型、profile及HOME/数据，保留调用者状态。

## 快速开始（CLI）

```bash
abx template deploy ./deepagents -y
abx create --template <template-id> --timeout 900 -y
abx run <sandbox-id> deepagents_version
abx run <sandbox-id> deepagents_setup_check
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Deploy returns the template ID and create returns the owned sandbox ID used above. Version/setup need no model key. See [entry compatibility and provider setup](../docs/using-templates.md#client-entry-compatibility). Model settings must be present in the running server; create-time environment does not reconfigure a prewarmed server.



## 快速开始（Python SDK）

按[固定客户端说明](../docs/python-client-installation.md)安装agent-sandbox-client，在操作者环境设置三个DEEPAGENTS模型变量。下面创建自有Sandbox及随机令牌9010服务，导出文件后清理；示例经源码检查，不自动构成云端验收。

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
            env={"DEEPAGENTS_API_KEY": os.environ["DEEPAGENTS_API_KEY"],
                 "DEEPAGENTS_BASE_URL": os.environ["DEEPAGENTS_BASE_URL"],
                 "DEEPAGENTS_MODEL": os.environ["DEEPAGENTS_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "deepagents", task="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("DeepAgents failed; inspect the private returned diagnostics")
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

## 快速开始（HTTP POST）

ABX_SERVER_URL为SDK转发的9010地址，ABX_SERVER_TOKEN为该服务随机令牌。

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/deepagents" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"task":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

HTTP200返回{"result":{"stdout":"42","stderr":"","exit_code":0}}，保留非零原生退出码。参数缺失/未声明/类型错误400，认证401，未知命令404；路径/配置/限制/超时500。结果缓冲，客户端超时/断连不保证取消原生执行。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| deepagents_version | none | actual installed0.7.25 |
| deepagents_setup_check | none | installed/version/api_key_set/base_url_set/model_set flags; read-only |
| deepagents | task:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

实际[驱动](worker.py)显式构造ChatOpenAI(use_responses_api=False)、LocalShellBackend(inherit_env=False)，不传自定义或子Agent，GeneralPurposeSubagentProfile(enabled=False)。默认排除八项工具。上游profile注册会累加排除集合，因此每次使用新进程；许可工具也不能启用委派。任务/模型配置仅通过私有文件stdin进入。

图递归上限40表示图步骤，不等于40次模型调用。单模型请求60秒、零重试、最多8192输出token；单shell期限min(command_timeout,120)、原生shell输出100000字节为捕获后截断，不是峰值内存限制；外层期限1..1800秒及每路输出256KiB。原生非零码保留。超时/输出溢出500，普通结构化非零结果仍为HTTP200。返回替换配置密钥和地址完整值，项目输出仍可能私密。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| DEEPAGENTS_API_KEY | model calls | empty | explicit compatible-provider credential |
| DEEPAGENTS_BASE_URL | model calls | empty | HTTP(S), no userinfo/query/fragment |
| DEEPAGENTS_MODEL | model calls | empty | explicit model identifier |
| DEEPAGENTS_PYTHON | no | /opt/deepagents/bin/python | exact native dependency environment, version checked |
| WORKSPACE | no | /home/user/app | existing owned project directory |
| ABX_SERVER_TOKEN | no | empty | command-server process bearer token |

显式模型配置保留在私有stdin，不作为环境传入生成的shell。运行时仅PATH/可选CA、私有HOME/XDG、关闭LangSmith追踪；LocalShellBackend只接收PATH/HOME/locale及随机非秘密进程归属标记，不继承模型/云/GitHub/服务密钥。不加载skills/memory/profile文件。虚拟文件路径映射至cwd，但shell仍有沙箱用户全部权限，该映射不是shell隔离边界。

## 资源

2vCPU/2048MB，服务9000及可选显式9010；CPU Linux Python3.13，依赖虚拟环境/opt/deepagents，镜像8GiB根文件系统门禁。任务256KiB，每路输出256KiB，期限1..1800秒另加有限进程组/身份固定子进程清理。每次删除私有配置/会话，项目修改由调用者清理；同用户恶意代码或服务被中断时仍以销毁自有沙箱为最终边界。

## 已验证

版本1.0.0已通过真实阿里云极速版校验CI镜像注册、官方READY、原生Python Sandbox.create、CLI/SDK冒烟及 **17项严格真实模型检查，0 FAIL/0 SKIP**。显式兼容模型qwen3.8-flash驱动真实原生Agent改源码、生成报告及精确产物、保留全部原测试，并通过返回后的独立原测试/隐藏计算。沙箱/模板/镜像仓库清理及运行后镜像digest均独立确认。

| 版本 | 提供方 | 证据 |
| --- | --- | --- |
| 1.0.0 | alicloud-express | [SDK创建镜像](evidence/express-2026-10-20.json), [严格模型17](evidence/model-image-2026-10-20T113609Z.json), [关闭模型HTTP](evidence/image-http-2026-10-20T113609Z.json) |

单独关闭模型的HTTP控制器9 PASS/1项显式模型SKIP，不是L3。[真实原生step尝试](evidence/verification-steps-2026-10-20T112245Z.json)未在1200秒内独立到达READY，最后官方状态仍为building，未创建沙箱。已删除自有模板，并[独立回查模板/沙箱不存在](evidence/steps-cleanup-2026-10-20.json)。这是失败尝试，不能宣称step通过或推断提供方存在通用RUN时限。其他提供方及其余上游模型/后端未认证。

## 二次开发

python -m venv <new-prefix>后，用<new-prefix>/bin/python -m pip install --require-hashes -r deepagents/requirements.lock及pip check恢复。DEEPAGENTS_PYTHON指向虚拟环境Python，保留该路径，不解析其可执行文件符号链接。运行python -m pytest -q deepagents/test_commands.py deepagents/test_controller.py。真实DeepAgents配合人工HTTP/写文件工具及固定进程夹具，不在操作者主机运行真实模型生成命令。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py deepagents --output /tmp/deepagents-steps仅准备；python scripts/run_steps_e2e.py deepagents --timeout 1200实际执行。严格模型测试设置E2E_REQUIRE_LLM=1/E2E_REQUIRE_CLI=1。生成步骤或静态标记不是验收通过。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/deepagents.md)，保持双语、依赖哈希、上游声明及不可变验证记录一致。

## 问题反馈

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码为[Apache-2.0](../LICENSE)。DeepAgents及langchain-openai为MIT，保留[DeepAgents原许可](upstream-LICENSE)与[集成库原许可](langchain-openai-LICENSE)。其余哈希固定依赖按各自许可证保留pip安装声明，不能统一重标Apache-2.0。
