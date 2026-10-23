# Goose

[English](README.md)。

## 做什么

运行官方 Goose1.54.0 终端 agent，对接 OpenAI 兼容服务。每次使用私有配置和
文件 stdin；默认无工具聊天，只有显式 `allow_tools=true` 才开启开发工具。

## 技术栈

阿里云 FC 基础镜像v0.0.49、generation2、非root用户user、SDK源码e2cb27e。
官方Linux x86_64/aarch64 CPU GNU资产的字节数和SHA256固定在
[assets.json](assets.json)，对应[源码cd643d2126fffab4c6a6186905211ba868d6a657](https://github.com/block/goose/tree/cd643d2126fffab4c6a6186905211ba868d6a657)。
不需要GPU、Docker daemon、桌面或浮动安装脚本。目前本机测试为Linux x86_64；
arm64资产pin不代表arm64提供方通过。

## 解决的问题

在自有沙箱中使用真正Goose完成终端、文件工作，保留调用者已有提供方、扩展、
hint和会话配置。本配置选择上游支持的OpenAI兼容服务，不代表验证全部提供方
或Goose桌面应用。

## 快速开始（CLI）

原生CLI语法；先确认[入口兼容性](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

```bash
abx template deploy ./goose -y
abx create <template-id> --detach --timeout 900
abx run <sandbox-id> goose_version
abx run <sandbox-id> goose_setup_check
abx kill <sandbox-id>
abx template delete <template-id> -y
```

版本/配置检查不需要key。模型调用需要运行中命令server已经取得配置，见下面
SDK显式启动；create-time环境不会重配预热server。[使用指南](../docs/using-templates.zh-CN.md)
说明提供方配置和ID所有权。

## 快速开始（Python SDK）

按[配套说明](../docs/python-client-installation.md)从固定源码安装 `agent-sandbox-client` 发行包。在操作端环境设置三个
GOOSE变量；凭据不进入argv。例子拥有整个沙箱，销毁前读取产物。

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
            env={"GOOSE_API_KEY": os.environ["GOOSE_API_KEY"],
                 "GOOSE_BASE_URL": os.environ["GOOSE_BASE_URL"],
                 "GOOSE_MODEL": os.environ["GOOSE_MODEL"],
                 "WORKSPACE": "/home/user/app"})
        result = await server.commands.run(
            "goose", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_tools=True, command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("Goose failed; inspect the private returned diagnostics")
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

SDK helper在9010启动新server，使用独立随机bearer token，不重配原9000进程。
仅销毁调用者拥有的沙箱。示例已按API/源码检查；实际提供方/模型通过依赖下面
独立回执。

## 快速开始（HTTP POST）

`ABX_SERVER_URL` 为已配置server的SDK9010转发URL，`ABX_SERVER_TOKEN` 为该
进程启动时的随机token。

```bash
curl --fail-with-body --max-time 660 -X POST "$ABX_SERVER_URL/commands/goose" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain 6*7 briefly","allow_tools":false,"command_timeout":600}'
```

示例响应：`{"result":{"stdout":"42","stderr":"","exit_code":0}}`。
HTTP200通过 `result` 包装 `{stdout,stderr,exit_code}`，保留上游非零退出码。
缺少/多余/错误类型参数400、鉴权失败401、未知命令404；路径、配置、版本、
限额或超时失败500，带error/type。响应缓冲。HTTP等待时限与命令时限不同，
断连不保证原生进程取消。

## 命令参考

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| goose_version | 无 | 真实固定版本字符串1.54.0 |
| goose_setup_check | 无 | installed/version及api_key_set/base_url_set/model_set；不修改配置或登录 |
| goose | 必填prompt:str，非空UTF-8/无NUL/最大256KiB；cwd:str=""，WORKSPACE内现有目录；allow_tools:bool=false；command_timeout:int=600，1..1800 | {stdout:str,stderr:str,exit_code:int} |

实际调用 `run --instructions - --no-session --no-profile --max-turns 20`，固定
quiet文本输出和提供方/模型，工具模式仅加载developer builtin。默认chat不公布
任何工具。输入是私有文件stdin，不拼接shell或prompt argv。每路输出上限256KiB；
超时/超量先清理未reap的自有进程组再回收leader。每次删除私有Goose配置/数据，
项目改动保留至调用者清理或销毁沙箱。返回诊断会遮盖已配置key和base URL，
但项目stdout仍可能包含项目私有内容。

## 配置

| 名称 | 必需 | 默认 | 用途 |
| --- | --- | --- | --- |
| GOOSE_API_KEY | 模型调用 | 空 | 兼容服务凭据，仅映射为原生子进程OPENAI_API_KEY |
| GOOSE_BASE_URL | 模型调用 | 空 | 显式HTTP(S)地址，无userinfo/query/fragment，映射上游OPENAI_BASE_URL |
| GOOSE_MODEL | 模型调用 | 空 | 上游真实模型ID |
| WORKSPACE | 否 | /home/user/app | 自有工作目录 |
| ABX_SERVER_TOKEN | 否 | 空 | 命令server进程bearer token |
| GOOSE_BINARY | 仅操作端诊断 | 镜像PATH中的Goose | 独立安装的二进制，仍检查精确版本 |

私有GOOSE_PATH_ROOT/HOME和XDG目录，关闭keyring、遥测、自动会话命名，
设置 `CONTEXT_FILE_NAMES=[]`、`--no-profile`，保留调用者状态。原生子进程仅接收
PATH/可选CA与私有运行/模型设置，不继承云端、GitHub或命令server凭据。

启动第二个服务时保留镜像 PATH；显式覆盖 PATH 时必须包含 `/opt/goose`。诊断只报告该服务进程实际可见的二进制。

## 资源

2vCPU/2048MB，命令API9000，可显式另启9010；不依赖浏览器共享内存。安装器
固定约81MB CPU压缩资产，下载预算240秒、socket超时30秒、可执行文件上限
400MiB，Docker构建另以 `du -sx` 检查8GiB镜像rootfs。操作端prefix安装不扫描
整个本机文件系统。每次最多20模型turn及声明的墙钟时限，再清理。主动setsid
脱离及server被SIGKILL超出进程组保证；最终隔离边界是整个沙箱销毁。

## 已验证

当前工作流清单尚无项目认可的验收收据。历史验收记录仅证明原输入和原调用路径；参见[工作流验证](../docs/workflows.zh-CN.md)。

## 二次开发

本机安装：`python goose/install_runtime.py --prefix <new-private-prefix>`；真实
CLI/协议/进程回归：`python -m pytest -q goose/test_commands.py`。合成HTTP fixture
只证明原生协议和工具选择，不证明真实模型或云端支持。HTTP控制器在
E2E_REQUIRE_LLM=1时要求真实源码修改、新报告、原测试不变及隔离held-out断言；
静态marker不能单独证明通过。E2E_REQUIRE_CLI=1要求真实可执行文件。

按[step指南](../docs/platform-steps.zh-CN.md)执行
`python scripts/prepare_steps.py goose --output /tmp/goose-steps`仅生成配置；
真实基础step验收为 `python scripts/run_steps_e2e.py goose --timeout 1200`。
构建方式回执、真实模型及独立自有资源清理分别记录。

## 贡献

[贡献指南](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)及
[设计](../docs/design/goose.md)。两种语言、pin、argv与证据保持一致。

## 问题反馈

[Issue49](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/49)。
模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
Server/客户端：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板采用[Apache-2.0](../LICENSE)。官方Goose为Apache-2.0；[原始许可证](upstream-LICENSE)
与未改动的官方二进制一并安装。上游依赖保留各自声明。不分发上游桌面、
Vulkan/CUDA资产、专有账户或模型权重。

### 当前版本新增平台 step 验收

[真实 step](evidence/express-2026-10-20T135350Z.json) 与 [外部 HTTP 尝试](evidence/verification-steps-2026-10-20T135350Z.json)：官方 READY、Python SDK 创建、CLI/SDK 冒烟，HTTP 9 通过、0 失败、1 跳过。本回执模型调用仍为 NOT_RUN；沙箱/模板及同账户私有资产缓存对象/bucket 都独立确认清理后才发布。既有镜像/模型回执保留其独立范围。
