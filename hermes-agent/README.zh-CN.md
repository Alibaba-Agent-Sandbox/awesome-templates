# Hermes Agent

## 做什么

运行真实 NousResearch Hermes Agent CLI，启用本地终端和文件工具。当前交付代码任务切片，未配置消息网关、浏览器、桌面或外部终端后端。

## 技术栈

NousResearch Hermes Agent v0.22.1, commit `297552a9d646119871391d202509822cd86330df`; private Python 3.14.6; `uv==0.12.3`; upstream frozen `uv.lock`; platform Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df)

## 解决的问题

通过命名命令提供真实 Hermes 无头 CLI 调用，限制 CLI 进程的等待时间并返回完整缓冲输出；模型凭据在创建沙箱时注入。网关已接受的任务具有独立生命周期。

## 快速开始（CLI）

```bash
abx template install alibaba-agent-sandbox/awesome-templates//hermes-agent
abx create --template <template-id> --env OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
abx run <sandbox-id> hermes --arg prompt="Inspect this project and fix the failing calculation" --arg model="<model-id>"
```

Hermes 还须通过 model 参数或创建环境的 HERMES_MODEL 指定实际可用模型。

## 快速开始（Python SDK）

客户端发行包为 `agent-sandbox-client`。安装可用性及源码固定安装见 [installation](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"OPENROUTER_API_KEY": os.environ["OPENROUTER_API_KEY"]})
    try:
        result = await sb.run("hermes", prompt="Inspect and fix the calculation", model="<model-id>",
                              timeout=660)
        print(result)
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/hermes" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600,"model":"<model-id>"}'
```

成功响应为 `{"result":"buffered output"}`。JSON 参数直接放在请求体，无 args 包装。网关凭据由提供方规定；`ABX_SERVER_TOKEN` 为独立的服务端鉴权，未设置时可省略 Authorization。SDK 可用 `sb.server_at(9000, token=...)`。

HTTP 400：缺失、类型或范围错误；401：鉴权失败；404：未知命令；500：凭据缺失、执行失败或超时。命令返回完整缓冲结果。`command_timeout` 只控制 CLI 及其所属进程组；SDK `timeout` 只控制客户端 HTTP 等待。Hermes v0.22.1 通过独立的 canonical gateway 和 managed worker 执行已接受的任务，两种超时之后任务都可能继续。需要停止全部工作时必须销毁沙箱；本模板未提供逐任务网关取消能力。后台任务使用 process API。

## 命令参考

`hermes` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| model | string | "" | Required argument or HERMES_MODEL; no implicit model choice. |
| provider | string | "" | Argument or HERMES_PROVIDER=openrouter; openrouter / openai-api / custom. |
| cwd | string | "" | Existing directory; relative to WORKSPACE. |
| max_turns | integer | 20 | Maximum tool rounds, 1–100. |
| command_timeout | integer | 600 | CLI 进程期限，1–1800 秒；网关已接受的工作可能继续。 |

| Additional command | Parameters | Result |
|---|---|---|
| hermes_version | none | Installed upstream version and provenance. |
| hermes_setup_check | none | Read-only CLI/version/provider-key diagnostic. |
| run | script: string = main.py | Local Python stdout (compatibility). |

## 配置

`WORKSPACE=/home/user/app`、`HERMES_HOME=/home/user/.hermes`、`HERMES_PROVIDER=openrouter`。必须指定 `HERMES_MODEL` 或 model 参数。OpenRouter 使用 `OPENROUTER_API_KEY`；openai-api/custom 使用 `OPENAI_API_KEY`，custom 还需要 `OPENAI_BASE_URL`。命令使用 `-Q --yolo`、terminal/file 工具及本地终端后端，忽略用户配置和规则，不启动交互式设置，超时杀死所属进程组。Hermes 会在 HERMES_HOME 持久化会话或记忆。CLI 会在需要时自动启动 canonical gateway，该独立进程满足上游空闲条件后退出。终止 CLI 不会取消网关已接受的任务。未配置消息适配器，但上游内部 canonical gateway 是 CLI 执行路径的一部分。

所有密钥在 template.yaml 中为空值；不要复制到镜像或日志。

Hermes 通过自己的 Python 3.14 shebang 启动。镜像只把 hermes 启动器链接到平台 PATH，python3 与 agent-sandbox-server 使用服务端环境。本地直接运行 python3 commands.py 时须选择装有 agent-sandbox-server 的 Python 环境；把整个 Hermes venv 放在 PATH 最前面会选错解释器。

## 资源

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## 已验证

当前编程验收器通过 `python3 -I` 先导入可信标准库，再直接编译计算器与原测试的实际源码字节，要求原有三个测试全部成功，拒绝跳过、预期失败和意外成功。每个原测试/保留输入进程必须返回模型响应结束后才生成的随机完成确认，确认值不会进入模型提示词。提前 `SystemExit`、`os._exit(0)`、固定 `INDEPENDENT_OK` 文本和陈旧字节码都不能提供该确认。这是防止提前退出的验收检查，不是抵抗同一操作系统权限下恶意 Python 的安全边界。历史模型运行保留原验收器哈希，不能证明新门槛；必须单独记录新验收器版本在已审镜像上的真实模型复验。规范要求的完整部署与提供方认证仍是独立门槛。

尚未记录任何通过的提供方测试。

## 二次开发

```bash
python3 scripts/check_template.py hermes-agent
python3 -m pytest -q hermes-agent/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` 控制模型验收执行期限，默认 600 秒，范围 1–1800。L0 不调用真实模型；`E2E_REQUIRE_LLM=1` 强制真实代码验收。L3 从目标端只读诊断检查密钥，种入必失败的源码与测试，经目标文件 API 验证源码修改、新产物、原测试未修改，并独立执行 unittest 和隐藏输入计算。缺密钥不能视为验收。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/hermes-agent.md).

## 问题反馈

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## 许可证

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).
