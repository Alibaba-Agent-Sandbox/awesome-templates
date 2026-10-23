# Copilot CLI

[English](README.md)。

## 做什么

运行固定版本的真实 GitHub Copilot CLI，通过显式 OpenAI 兼容 BYOK 端点调用模型。每次请求使用独立临时状态；修改文件必须传 allow_write=true。固定模型工具列表不包含 shell、委派或网页工具。

## 技术栈

阿里云 FC generation2 基础镜像、Linux x86_64、非 root user。固定 @github/copilot@1.0.100 和必需的 @github/copilot-linux-x64@1.0.100；[lockfile](package-lock.json) 校验完整性，禁用 npm 安装脚本并省略其他架构的可选包。服务端固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a。原生软件使用独立[上游许可证](UPSTREAM-LICENSE.md)。

## 解决的问题

在真实终端编程 Agent 外提供鉴权命令 API、文件传输和 sandbox 生命周期。此 BYOK 配置不使用 GitHub 登录或厂商 PAT，需要所配置模型端点支持流式 Chat Completions 和工具调用；其他上游提供商配置不属于当前范围。

## 快速开始（CLI）

```bash
abx template deploy ./copilot-cli -y
abx create <template-id> --detach --timeout 900
abx run <sandbox-id> copilot_version
abx run <sandbox-id> copilot_setup_check
abx kill <sandbox-id>
abx template delete <template-id> -y
```

使用 deploy/create 返回的 ID 替换占位符。版本与配置检查不调用模型。参见[客户端和提供商配置](../docs/using-templates.md#client-entry-compatibility)。同一源码也可使用原生平台 steps，保留资源归属和清理：

```bash
python scripts/express_e2e.py ./copilot-cli --build steps --sandbox-create sdk
```

steps 通过不能证明 Dockerfile 已构建。预热服务不会因 create 环境参数而重新配置，模型示例显式启动独立服务。

## 快速开始（Python SDK）

按[固定源码安装说明](../docs/python-client-installation.md)安装 agent-sandbox-client，在操作者环境设置三个模型变量，使用部署结果的模板 ID。

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
            env={name: os.environ[name] for name in (
                "COPILOT_PROVIDER_BASE_URL", "COPILOT_PROVIDER_API_KEY", "COPILOT_MODEL")})
        result = await server.commands.run(
            "copilot", prompt="Create HELLO.txt containing hello, then read it back.",
            allow_write=True, command_timeout=300, timeout=360)
        if result["exit_code"] != 0:
            raise RuntimeError("Native Copilot failed; inspect private diagnostics")
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

示例创建独立鉴权9010服务、读取目标文件并销毁自有 sandbox。源码检查不等于真实执行，执行资格以凭证为准。

## 快速开始（HTTP POST）

ABX_SERVER_URL 为 SDK 转发的9010地址；ABX_SERVER_TOKEN 为该服务的随机 token。

```bash
curl --fail-with-body --max-time 360 -X POST "$ABX_SERVER_URL/commands/copilot" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' \
  --data '{"prompt":"Explain the existing source","allow_write":false,"command_timeout":300}'
```

HTTP200 返回 `{"result":{"stdout":"<native JSONL>","stderr":"","exit_code":0,"native_version":"1.0.100"}}`。原生命令非零退出保留 exit_code。鉴权401、命令不存在404、schema 错误400；配置、路径、限额、输出溢出或超时返回500及 error/type。每路输出缓冲上限256KiB。客户端断开不保证取消进程。

## 命令参考

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| copilot_version | 无 | 实际二进制检查，{native_version:"1.0.100"}；不需要模型 key |
| copilot_setup_check | 无 | mode、base_url_set/api_key_set/model_set 布尔值、github_auth_required=false；无网络 |
| copilot | prompt:str 必填，1..32768UTF-8字节/无 NUL；cwd:str=""，解析符号链接后必须位于 WORKSPACE 内且存在；allow_write:bool=false；command_timeout:int=300，1..600秒 | stdout:str、stderr:str、exit_code:int、native_version:str |

只读工具固定 view/glob/grep；显式写入增加 edit/create/apply_patch。--allow-all-tools 仅批准封闭列表中的工具，不批准全局路径或 URL；上游路径策略继续生效，这不是操作系统文件隔离。禁用自动更新、遥测、内置 MCP、自定义指令、实验/BASH_ENV、提问和远程导出。不支持恢复会话、插件、调用者 HOME、工作区信任选项和任意 CLI 参数。参数通过 argv 传入，prompt 始终是单一字面参数。JSONL 保留上游格式，不承诺稳定事件 schema；调用方必须处理 session.error 和非零退出。

共享服务端布尔标量兼容 true/false/yes/no/1/0 字符串，便于 CLI 调用；非法布尔测试使用白名单以外的值。

## 配置

| 名称 | 必需/默认 | 含义 |
| --- | --- | --- |
| COPILOT_PROVIDER_BASE_URL | 模型请求/空 | HTTPS 或回环 HTTP 开发端点；无 userinfo/query/fragment；最长2048字符 |
| COPILOT_PROVIDER_API_KEY | 模型请求/空 | 显式端点凭据，最长8192字符，禁止 CR/LF/NUL |
| COPILOT_MODEL | 模型请求/空 | 显式模型标识，最长200ASCII字符 |
| WORKSPACE | /home/user/app | cwd 根目录 |
| ABX_SERVER_TOKEN | 操作者设置 | 命令服务鉴权 token |

模型变量在服务启动时读取。固定 type=openai、wire API=completions、transport=http，prompt/output token 上限65536/4096。不转发 key-command、自定义 headers、bearer、GitHub token 或其他主机凭据。上游 secret-env 过滤和包装层替换保护配置的 key。子进程只继承 PATH/可选 CA 路径及独立 HOME/XDG/temp/state。停止自有进程组和带随机标记的脱离子进程后删除临时配置/缓存/日志，项目修改保留。自有云 sandbox 是恶意代码的最终边界。参见[运行环境](../docs/runtime-environment.md)和[官方 BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models)。

## 资源

2vCPU/2048MB，默认9000、可选自有9010服务。仅 CPU Linux x86_64，无 GPU/KVM/Docker daemon。每次原生调用可能解包独立缓存，结束时删除。执行时限1..600秒加有界清理；每路输出256KiB。不预置模型权重，不需要 GitHub 服务账号。

## 已验证

当前工作流清单尚无项目认可的验收收据。历史验收记录仅证明原输入和原调用路径；参见[工作流验证](../docs/workflows.zh-CN.md)。

## 二次开发

参见[设计](../docs/design/copilot-cli.md)、固定版本 help 和 lockfile。升级必须重新验证版本、参数、许可证和真实模型行为。本地测试只运行预先编写的替代进程，不在主机执行模型生成代码。e2e_test.py 的 L3 要求显式自有远程 sandbox，源码修改、新文件、原始测试及隐藏断言均在云端执行。

## 贡献

遵守[贡献说明](../CONTRIBUTING.zh-CN.md)、项目/文档规范及记录要求，同时维护双语文档和固定来源。

## 问题反馈

[Issue64](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/64)。缺少账号或模型能力时如实保留限制，不替换为无关凭据。

SDK/server 问题：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)；CLI 问题：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

包装代码为 Apache-2.0，见[仓库许可证](../LICENSE)。未修改的 GitHub Copilot CLI 遵守其独立[许可证](UPSTREAM-LICENSE.md)，镜像和安装包保留完整文本。再分发要求作为具有额外实质功能的应用/服务的一部分，禁止独立或作为主要产品分发。鉴权远程 API、文件传输和 sandbox 服务独立许可，不重新许可 CLI，也不授予 GitHub 服务访问权。

统一非模型完整 HTTP 验收也已通过：真实 SDK 创建 steps，使用公开 CLI0.4.1，87.661 秒，8 PASS/0 FAIL/0 SKIP，沙箱与模板清理已独立确认。见[当前控制器结果](evidence/verification-steps-2026-10-20T171425Z.json)和[规范 CLI/SDK 回执](evidence/express-2026-10-20.json)。上文17项真实模型验收仍单独保留。
