# Pi

## 做什么

在阿里云沙箱基础镜像内运行[官方 Pi 编程 CLI](https://github.com/earendil-works/pi)。本模板提供一次性的 print 模式任务，使用 OpenAI 兼容模型端点；它是独立模板，不依赖 E2B 模板注册。

## 技术栈

`@earendil-works/pi-coding-agent@1.3.0`（MIT）、校验 SHA256 的 Node.js 24.16.0、平台 Python 3.13 和 Agent Sandbox server。提交的 package-lock 冻结全部 118 个 npm 依赖，使用 `npm ci --ignore-scripts --omit=dev` 安装；fd 10.5.0 与 ripgrep 15.2.0 官方 musl 归档也校验 SHA256。[Dockerfile](Dockerfile) · [template.yaml](template.yaml)。

## 解决的问题

通过带类型的命名命令运行 Pi，限定执行时间、隔离模型配置，并要求调用方明确允许修改沙箱文件。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

```bash
abx template install alibaba-agent-sandbox/awesome-templates//pi
abx create --template <template-id> --env PI_BASE_URL="$PI_BASE_URL" --env PI_MODEL="$PI_MODEL" --env PI_API_KEY="$PI_API_KEY"
abx run <sandbox-id> pi --arg prompt="检查这个项目"
abx run <sandbox-id> pi --arg prompt="修复计算错误" --arg allow_tools=true
```

## 快速开始（Python SDK）

安装 `agent-sandbox-client`；参见[源码安装说明](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
        envs={key: os.environ[key] for key in ("PI_BASE_URL", "PI_MODEL", "PI_API_KEY")})
    try:
        print(await sb.run("pi", prompt="修复计算错误", allow_tools=True,
                           command_timeout=600, timeout=660))
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/pi" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"检查这个项目","allow_tools":false,"command_timeout":600}'
```

参数直接放在 JSON body 中，不包裹 `args`。成功返回 `{"result":"缓冲输出"}`。网关 token 与可选的 server bearer token 分开配置，未设置时省略对应 header。HTTP 400 表示参数无效，401 表示认证失败，404 表示命令不存在，500 表示配置缺失、执行失败或超时。SDK 的 HTTP `timeout` 不会取消模型进程；进程期限由 `command_timeout` 控制。

## 命令参考

| 命令 | 参数 | 返回值 |
|---|---|---|
| pi_version | 无 | 已安装版本字符串。 |
| pi_tools_check | 无 | 在临时文件上真正离线执行官方 read/find/grep/ls，返回 `read/find/grep/ls OK`。 |
| pi_setup_check | 无 | 安装状态、版本、固定版本、key/端点/模型是否配置的布尔值、工作目录；不返回凭证或端点值。 |
| pi | prompt: string 必填；cwd: string = ""；allow_tools: boolean = false；command_timeout: integer = 600 | 脱敏后的缓冲文本；期限范围 1–1800 秒。 |

`cwd` 必须存在，相对路径基于 `WORKSPACE`；它不是文件访问隔离边界。提示词通过 stdin 输入，不经过 shell 插值，也不放在 argv 中。

## 配置

`PI_BASE_URL` 是兼容 chat-completions 的端点，`PI_MODEL` 是模型 ID，`PI_API_KEY` 是密钥；三项必须齐全。拒绝含内嵌凭证、query 或 fragment 的 URL，不启动交互登录。metadata 内凭证值为空。

每次任务在私有临时目录生成 `models.json`，仅写上游支持的 `$PI_API_KEY` 引用；成功、失败或 Python 取消后均删除。不会复用用户配置或持久会话。`--offline` 关闭启动时的模型目录刷新等自动网络操作，所请求的模型调用仍访问配置端点。扩展、MCP、skills、上下文文件、主题、提示词模板均关闭。

镜像明确安装固定版本的 `fd` 与 `rg`，离线模式不依赖运行时下载工具。`pi_tools_check` 无需模型就运行四个真实默认工具，并纳入镜像/云端 smoke。

默认工具严格为 `read,grep,find,ls`。`allow_tools=true` 明确加入 `edit,write,bash`，允许模型在当前沙箱用户可访问范围内修改文件、执行代码。Pi 的 `--no-approve` 仅忽略需要信任的项目配置，不限制工具；默认工具由白名单控制，真正的隔离边界仍是沙箱。不要让不可信调用方直接使用可写模型执行。

Linux 下每次调用拥有独立进程组，并发排空 stdout/stderr；成功、错误、超时或 Python 取消时先清理进程组，再回收 leader。自行创建新 session 的子进程会逃离此进程组边界。HTTP 断开不代表取消。

## 资源

2 vCPU · 2048 MB · 9000 端口 · `/home/user/app` · 非 root `user`。不需要 Docker、KVM 或额外权限。本命令面不包括 RPC 持久会话、交互 TUI 或扩展安装。

## 已验证

当前编程验收器通过 `python3 -I` 先导入可信标准库，再直接编译计算器与原测试的实际源码字节，要求原有三个测试全部成功，拒绝跳过、预期失败和意外成功。每个原测试/保留输入进程必须返回模型响应结束后才生成的随机完成确认，确认值不会进入模型提示词。提前 `SystemExit`、`os._exit(0)`、固定 `INDEPENDENT_OK` 文本和陈旧字节码都不能提供该确认。这是防止提前退出的验收检查，不是抵抗同一操作系统权限下恶意 Python 的安全边界。历史模型运行保留原验收器哈希，不能证明新门槛；必须单独记录新验收器版本在已审镜像上的真实模型复验。规范要求的完整部署与提供方认证仍是独立门槛。

尚无本模板的镜像云部署通过记录。先前 b2857609735c1da8529ba8ecf3d065076cdfb542 的源码服务使用官方 Pi 1.3.0 与 `qwen3.8-flash`，通过独立源码、测试和产物验收；后续离线工具/lock 修复需要自己的镜像与云验证，不能沿用该次结果宣称云 L2 或镜像 L3。参见[验证记录](../.agents/evidence/verify/2026-10-16-pi-runtime.md)。

## 二次开发

```bash
python3 scripts/check_template.py pi
python3 -m pytest -q pi/test_commands.py pi/test_e2e_protocol.py pi/test_cli_protocol.py pi/test_install_tools.py
python3 scripts/run_local_e2e.py
```

默认本地检查不调用模型。`E2E_REQUIRE_CLI=1` 要求实际固定版本；`E2E_REQUIRE_LLM=1` 使用目标配置强制真实编程验收。验证器先创建失败源码和测试，明确允许 Pi 写入，再下载改动源码、新产物，确认原测试未修改，最后独立运行隔离 unittest 和 held-out 输入；仅返回 marker 会失败。`E2E_COMMAND_TIMEOUT` 控制模型期限；`E2E_SERVER_TOKEN` 是可选 server bearer token，`E2E_TOKEN` 是网关 token。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py pi`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[贡献规范](../CONTRIBUTING.md) · [模板规范](../docs/template-spec.zh-CN.md) · [设计](../docs/design/pi.md)。

## 问题反馈

[模板 Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41)。SDK/server 问题在 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题在 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。请提供脱敏版本和复现步骤。

## 许可证

模板代码采用 Apache-2.0，Pi 上游采用 MIT；fd 官方归档的 LICENSE-MIT、LICENSE-APACHE，以及 ripgrep 的 LICENSE-MIT、UNLICENSE、COPYING（MIT/Unlicense）随完整解包目录保留在 `/opt/pi-tools/`，npm 依赖也保留各自许可文件。[LICENSE](../LICENSE)。
