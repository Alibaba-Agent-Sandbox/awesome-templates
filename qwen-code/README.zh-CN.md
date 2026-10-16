# Qwen Code

[English](README.md)

## 做什么

通过类型化命名命令运行固定版本 Qwen Code 无头编码 CLI，并提供安装诊断和 Python 脚本执行命令。模板保持实验状态，实际验收层级见下文。

## 技术栈

Alibaba FC generation 2 基础镜像、平台 Python、基础镜像未提供 Node >=22 时安装的 Node.js 22、`@qwen-code/qwen-code@0.23.0`，以及 [Dockerfile](Dockerfile) 固定提交的沙箱服务器。CLI 不需要额外的 DashScope/OpenAI Python 库。

## 解决的问题

提供可复现的无头编码环境。显式选择 OpenAI 兼容认证，缺少密钥时在启动 CLI 前返回错误，避免等待浏览器 OAuth 登录。

## 快速开始（CLI）

安装需要 Express 授权配置和可用 Docker daemon：

```bash
abx template install ./qwen-code --registry-type local
abx create --template <template-id> --env OPENAI_API_KEY="$OPENAI_API_KEY"
abx run <sandbox-id> qwen_version
abx run <sandbox-id> qwen_setup_check
abx run <sandbox-id> qwen --json-args '{"prompt":"修复现有 calculator.py，在 REPORT.md 解释修复并运行测试","max_turns":20,"yolo":true,"command_timeout":300}'
```

先上传项目。`yolo=true` 自动批准所有代理工具操作，仅在允许代理修改的沙箱和项目中启用；默认 `false`。结果为 CLI 完成后返回的 JSON 文本，不是实时事件。

## 快速开始（Python SDK）

客户端发行包是 `agent-sandbox-client`，导入名是 `agent_sandbox`。匹配版本未发布时使用[固定源码安装](../docs/python-client-installation.md)，并配套服务器版本。

```python
import asyncio
import os
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600,
        envs={"OPENAI_API_KEY": os.environ["OPENAI_API_KEY"]})
    try:
        print(await sb.run("qwen_version"))
        await sb.files.write("/home/user/app/calculator.py", "def add(a,b):\n    return a-b\n")
        print(await sb.run("qwen", prompt="修复 calculator.py，在 REPORT.md 解释修复并运行测试",
            max_turns=20, yolo=True, command_timeout=300, timeout=330))
        print((await sb.commands.run("cd /home/user/app && python3 -c 'from calculator import add; assert add(2,3)==5'")).exit_code)
    finally:
        await sb.kill()

asyncio.run(main())
```

`timeout=330` 限制客户端 HTTP 等待，`command_timeout=300` 限制代理进程组执行。客户端超时不保证取消执行。后台任务和取消使用进程 API。配置 `ABX_SERVER_TOKEN` 时，命名命令使用 `sb.server_at(9000, token=os.environ["ABX_SERVER_TOKEN"]).run(...)`。

## 快速开始（HTTP POST）

端口 URL 使用 `sb.network.get_url(9000)` 的结果。Express 网关需要 `X-Access-Token`；单独配置服务器认证时还需要 `Authorization: Bearer`。仅在相应层不要求认证时省略对应 header。

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/qwen" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $SANDBOX_GATEWAY_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  -d '{"prompt":"修复 calculator.py，在 REPORT.md 解释修复并运行测试","max_turns":20,"yolo":true,"command_timeout":300}'
```

参数直接作为 JSON 对象，不加 `args` 包装。返回 `{"result":"<Qwen JSON 输出文本>"}`。`POST /commands/qwen_version` 的请求 `{}` 返回 `{"result":"0.23.0"}`。缺参或类型错误为 400；认证失败为 401；未知命令为 404；范围错误、缺密钥/CLI、上游失败或执行期限到期为 500，响应为 `{"error":"...","type":"RuntimeError"}` 或 `ValueError`。成功和错误输出均脱敏秘密环境变量值。

## 命令参考

| 命令 | 参数 | 结果及上游调用 |
| --- | --- | --- |
| `qwen` | `prompt: str` 必填非空；`max_turns: int=100`（1–1000）；`model: str=""` 使用 `OPENAI_MODEL`；`cwd: str=""` 使用工作区；`command_timeout: int=600`（1–1800 秒）；`yolo: bool=false` | 字符串；`qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`，按需加 `--model MODEL`、`--yolo` |
| `qwen_version` | 无 | 真实 `qwen --version` 输出，不需密钥 |
| `qwen_setup_check` | 无 | 安装/版本/pin、密钥/模型/base URL 是否配置、设置文件存在与 JSON 有效性；不返回设置内容，不写文件 |
| `run` | `script: str="main.py"` | 兼容命令，返回 Python stdout，执行期限 120 秒 |

`cwd` 为绝对路径或相对 `WORKSPACE` 的路径，必须已经存在。包装器使用 argv 数组，不拼接 shell。上游编码代理可以修改文件并执行 shell 工具。

此生命周期实现适用于 Linux：并行读取两路输出，在清理自建进程组前保留未回收的会话 leader。成功、非零退出和执行截止都会先清理该组再返回。

## 配置

| 变量 | 含义 |
| --- | --- |
| `OPENAI_API_KEY` | 创建时注入的主要模型密钥 |
| `DASHSCOPE_API_KEY` | 主要密钥为空时的备选值，仅在子进程映射 |
| `OPENAI_BASE_URL` | 默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`，可覆盖为兼容端点 |
| `OPENAI_MODEL` | 默认 `qwen3-coder-plus`，命令参数 `model` 优先 |
| `WORKSPACE` | 默认 `/home/user/app` |
| `ABX_SERVER_TOKEN` | 可选的独立服务器 HTTP 认证令牌，不是模型密钥 |

诊断只读 `~/.qwen/settings.json` 和 `<workspace>/.qwen/settings.json`，保留内容与权限；正常编码可能产生上游运行缓存。兼容约定见[上游模型提供方配置](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md)和[无头模式](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md)。每个端点/模型仍需真实验收，不把 API 日志中的秘密写入公开产物。

## 资源

2 vCPU、4096 MB 内存、端口 9000，需要访问所选模型服务的出网能力。generation 2 使用非 root `user`，Qwen 不依赖 Docker-in-Docker 或额外权限。

## 已验证

当前编程验收器通过 `python3 -I` 先导入可信标准库，再直接编译计算器与原测试的实际源码字节，要求原有三个测试全部成功，拒绝跳过、预期失败和意外成功。每个原测试/保留输入进程必须返回模型响应结束后才生成的随机完成确认，确认值不会进入模型提示词。提前 `SystemExit`、`os._exit(0)`、固定 `INDEPENDENT_OK` 文本和陈旧字节码都不能提供该确认。这是防止提前退出的验收检查，不是抵抗同一操作系统权限下恶意 Python 的安全边界。历史模型运行保留原验收器哈希，不能证明新门槛；必须单独记录新验收器版本在已审镜像上的真实模型复验。规范要求的完整部署与提供方认证仍是独立门槛。

尚未记录任何通过的提供方测试。

本地 CLI 安装/版本及 HTTP 回归结果见[验证记录](../.agents/evidence/verify/2026-10-16-qwen-code-v2.md)。缺少可用 Docker daemon，L1 镜像构建和 L2 Express 阻塞。本地模型运行不构成云端或镜像验收。

## 二次开发

在 `commands.py` 添加类型化 `@command`，`start()` 保持在主入口保护内。保留 `qwen`、`run` 名称，双语更新参数文档，固定 CLI/server 版本。修改前阅读[设计](../docs/design/qwen-code.md)。

## 贡献

遵守[贡献规则](../CONTRIBUTING.md)和[模板规范](../docs/template-spec.md)。运行 `python3 scripts/check_template.py qwen-code`、`python3 -m pytest -q qwen-code/test_commands.py`、`python3 scripts/run_local_e2e.py`。本地 CLI 缺失时可跳过实版本测试，`E2E_REQUIRE_CLI=1` 时必须失败，跳过不代表运行时通过。真实编码验收先用兼容密钥/base URL/model 启动服务器，再运行 `E2E_REQUIRE_CLI=1 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python3 qwen-code/e2e_test.py`。测试修改现有源文件，经文件 API 读取新报告和精确产物，再经目标 shell API 独立运行原测试及保留计算；只清理本次唯一项目目录。保留工程记录，不提交密钥或失败的提供方通过证据。

## 问题反馈

模板任务跟踪于 [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26)。SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，附脱敏命令、版本及实际未通过门禁。

## 许可证

模板使用 Apache-2.0。Qwen Code 保留[上游许可](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE)。
