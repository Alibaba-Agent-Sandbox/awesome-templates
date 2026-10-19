# claude-code

[English](README.md)

## 做什么

通过命名命令 `claude` 调用钉死版本的 Anthropic Claude Code CLI，修改项目并生成工作区文件。
文本回复成功不代表编程任务完成；应下载产物并独立运行项目测试。

## 技术栈

阿里云运行时基础镜像（Python 3.13、Node 20），Claude Code **2.0.76**，以及钉在
python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505` 的服务端。
部署 CLI 注入 wheel 时优先安装 wheel。Claude Code 2.0.76 支持 Node >=18，无需另装 Node。
安装层在前、`commands.py` 复制在后，便于复用镜像层。

## 解决的问题

在 CLI、Python SDK 和 HTTP 上提供一致的无头编程命令。使用 files API 获取生成产物，
使用服务端提供的 process 和 terminal API 管理进程与终端。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

```bash
abx template install alibaba-agent-sandbox/awesome-templates//claude-code
# 使用安装返回的模板 id，创建时注入已有密钥。
abx create --template <template-id> --env ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
abx run <sandbox-id> claude_version
abx run <sandbox-id> claude --arg prompt='创建 hello.py，输出 hello'
abx run <sandbox-id> claude --json-args '{"prompt":"修复 calculator.py 并运行测试","cwd":"project","allowed_tools":"Read,Edit,Write,Bash(python3:*)","command_timeout":300}'
```

先用 files 或 shell API 创建 `project`。注入凭据时关闭 shell tracing；有平台秘密注入功能时优先使用，
命令行参数可能被本机其他进程看到。

## 快速开始（Python SDK）

客户端发行名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。配套版本发布前，请按[固定提交的双包安装说明](../docs/python-client-installation.md)安装。

```python
import asyncio
import json
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=600,
        envs={"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]},
    )
    try:
        result = await sb.run("claude", prompt="创建 hello.py，输出 hello", timeout=420)
        print(json.loads(result)["result"])
        print(await sb.files.read("/home/user/app/hello.py"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 返回命令结果，`claude` 的结果是 JSON **字符串**。`sb.run(timeout=...)` 控制 HTTP 超时，`command_timeout` 控制 CLI 执行上限。响应完整缓冲；实时 stdout 使用进程流 API。

## 快速开始（HTTP POST）

```bash
curl --request POST "$SANDBOX_SERVER_URL/commands/claude" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --max-time 420 \
  --data '{"prompt":"创建 hello.py，输出 hello","command_timeout":300}'
```

`SANDBOX_SERVER_URL` 为沙箱端口 9000 URL。未配置服务认证时省略 Authorization 头。
HTTP 200 为 `{"result":"<上游 JSON>"}`，400 表示参数错误，401 表示认证失败，500 表示命令失败。
CLI 的 300 秒执行上限与 HTTP 的 420 秒请求超时独立。客户端超时不代表上游进程已停止。

## 命令参考

| 命令或参数 | 类型/默认值 | 行为 |
|---|---|---|
| `claude_version()` | 无参数 | 查看已安装 CLI 版本，不访问模型。 |
| `claude.prompt` | 必填字符串 | 作为独立 argv 参数传入，不拼接 shell。 |
| `claude.model` | 字符串，`sonnet` | 上游模型名或别名。 |
| `claude.cwd` | 字符串，空 | `WORKSPACE` 内已存在的相对或绝对目录；拒绝符号链接逃逸。 |
| `claude.allowed_tools` | 字符串，`Read,Edit,Write` | Claude 工具许可规则，shell 需显式许可。 |
| `claude.resume` | 字符串，空 | 可选的上游会话 id。 |
| `claude.command_timeout` | 整数，`300` | 1–900 秒；客户端超时应更长。 |

向沙箱端口 9000 URL 发出等价 HTTP 请求：

```http
POST /commands/claude
Content-Type: application/json

{"prompt":"创建 hello.py，输出 hello","model":"sonnet","cwd":"","allowed_tools":"Read,Edit,Write","command_timeout":300}
```

HTTP 200 包装为 `{"result":"<上游 JSON>"}`。缺参或类型错误返回 HTTP 400；CLI 非零退出、
超时、无效 JSON、上游 `is_error` 返回 HTTP 500，错误中不含上游诊断原文。
`GET /commands` 提供当前参数 schema。这是一次完整响应，不是 SSE。

## 配置

| 环境变量 | 用途 |
|---|---|
| `ANTHROPIC_API_KEY` | 模型调用要求沙箱内已注入。 |
| `WORKSPACE` | 工作区根目录，默认 `/home/user/app`。 |
| `ABX_SERVER_TOKEN` | 可选的命名命令服务认证，创建时注入。 |
| `E2E_RUN_LLM` | `0` 跳过真实 Agent；`1` 要求运行端已有密钥。 |
| `E2E_REQUIRE_LLM` | `1` 时缺密钥或强制跳过都失败。 |
| `E2E_MODEL` | 验收使用的可选模型覆盖。 |

使用 `--permission-mode dontAsk`，需要许可的工具必须由 `allowed_tools` 或上游设置允许。
封装不打开全局权限绕过。工具规则和 cwd 检查不构成操作系统隔离：Agent 以沙箱 `user` 身份运行，
允许 Bash 后能访问该用户的文件、网络和注入凭据。使用一次性沙箱及最少凭据，避免宿主机秘密挂载，
避免把不可信提示词与秘密放在一起。模型输出可能含工作区数据，不应直接记录全部输出。
封装不回传 stderr 和异常载荷原文，并从成功 JSON 中涂掉已知秘密环境变量的值。

启用 `ABX_SERVER_TOKEN` 后，HTTP 带 `Authorization: Bearer <token>` 或
`X-Access-Token: <token>`。SDK 使用
`await sb.server_at(9000, token=os.environ["ABX_SERVER_TOKEN"]).commands.run("claude", prompt="...", timeout=420)`。
沙箱网关 token 和该服务 token 是不同的凭据。

## 资源

2 vCPU、2048 MB，无 GPU、Docker、KVM 或额外权限。模型调用需要访问 Anthropic 外网并消耗账户额度。
工具规则见[上游 CLI 参考](https://code.claude.com/docs/en/cli-reference)和[无头调用](https://code.claude.com/docs/en/headless)。

## 已验证

尚未记录任何通过的提供方测试。

## 二次开发

修改 `commands.py` 时保留 argv 方式。升级时同时修改 Dockerfile 精确 npm 版本及 smoke 期望。
不要把秘密放入镜像层。从仓库根目录运行：

```bash
python3 scripts/check_template.py claude-code
python3 -m unittest discover -s claude-code/tests -v
python3 scripts/run_local_e2e.py
```

L0 跳过模型。L1 要真实构建；L2 要部署和外部 CLI/SDK smoke。L3 对创建好的沙箱运行
`e2e_test.py`，设置 URL/token、运行端已有密钥、`E2E_REQUIRE_LLM=1` 和 `E2E_RUN_LLM=1`，
不打印秘密。套件先复现项目失败，要求真实 Agent 修改代码、新建产物与报告，保持测试文件不变，
再独立运行两项测试。只清理本次唯一目录、进程与 PTY 会话。必需模式缺密钥会失败。
提供方记录必须等真实运行通过后填写。

## 贡献

遵循[贡献指南](../CONTRIBUTING.md)和[模板规范](../docs/template-spec.zh-CN.md)。

## 问题反馈

模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
SDK/服务端问题提交到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，
CLI 问题提交到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题加 `[templates]`。
先搜索已有 issue，附复现步骤并去掉凭据。

## 许可证

本模板 Apache-2.0。Claude Code 适用上游自己的条款。
