# Hermes Agent

## 做什么

运行真实 NousResearch Hermes Agent CLI，启用本地终端和文件工具。当前交付代码任务切片，未配置消息网关、浏览器、桌面或外部终端后端。

## 技术栈

NousResearch Hermes Agent v0.22.1, commit `297552a9d646119871391d202509822cd86330df`; private Python 3.14.6; `uv==0.12.3`; upstream frozen `uv.lock`; platform Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df)

## 解决的问题

通过命名命令提供真实 Hermes 无头 CLI 调用，限制 CLI 进程的等待时间并返回完整缓冲输出；模型凭据在创建沙箱时注入。网关已接受的任务具有独立生命周期。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

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
from agent_sandbox.api.sandbox import Sandbox

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

版本 1.1.1 已通过真实 CI 镜像登记、官方 READY、CLI/SDK，以及 17 项严格真实模型检查（qwen3.8-flash、OpenAI 兼容协议），含源码修改、新产物、原始测试不变和独立 held-out 完成证明。独立确认 sandbox/template/registry 清理。状态仍为 experimental；其他提供方未验证。

| 提供方 | 范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 精确当前版本、真实镜像和独立清理 | [正式回执](evidence/express-2026-10-20.json)、[HTTP](evidence/image-http-2026-10-20T062649Z.json)、[严格模型](evidence/model-image-2026-10-20T062649Z.json) |

2026-10-19的1.1.0历史镜像验收：CLI创建沙箱，镜像来源、HTTP、17项真实兼容模型断言及自有沙箱/模板/镜像仓库独立清理均通过。这些回执只证明原版本及控制器，不用于认定1.1.1通过。[image](evidence/express-2026-10-19.json) · [HTTP](evidence/image-http-2026-10-19T175057Z.json) · [model](evidence/model-image-2026-10-19T175057Z.json).

补充原生SDK创建验收2026-10-20：同一1.1.1运行时由已验证CI镜像注册、官方READY、真实Python Sandbox.create创建，完成CLI/SDK冒烟及关闭模型的HTTP控制器。[新的不可变SDK回执](evidence/express-2026-10-20T110933Z.json)、[HTTP及清理](evidence/image-http-2026-10-20T110933Z.json)。沙箱/模板/镜像仓库不存在性和运行后镜像digest均独立确认。本次没有重跑模型；上方同一运行时/控制器的历史真实模型通过仍单独保留。

## 历史验收

当前编程验收器通过 `python3 -I` 先导入可信标准库，再直接编译计算器与原测试的实际源码字节，要求原有三个测试全部成功，拒绝跳过、预期失败和意外成功。每个原测试/保留输入进程必须返回模型响应结束后才生成的随机完成确认，确认值不会进入模型提示词。提前 `SystemExit`、`os._exit(0)`、固定 `INDEPENDENT_OK` 文本和陈旧字节码都不能提供该确认。这是防止提前退出的验收检查，不是抵抗同一操作系统权限下恶意 Python 的安全边界。历史模型运行保留原验收器哈希，不能证明新门槛；必须单独记录新验收器版本在已审镜像上的真实模型复验。规范要求的完整部署与提供方认证仍是独立门槛。

尚未记录任何通过的提供方测试。

## 二次开发

```bash
python3 scripts/check_template.py hermes-agent
python3 -m pytest -q hermes-agent/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` 控制模型验收执行期限，默认 600 秒，范围 1–1800。L0 不调用真实模型；`E2E_REQUIRE_LLM=1` 强制真实代码验收。L3 从目标端只读诊断检查密钥，种入必失败的源码与测试，经目标文件 API 验证源码修改、新产物、原测试未修改，并独立执行 unittest 和隐藏输入计算。缺密钥不能视为验收。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py hermes-agent`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/hermes-agent.md).

## 问题反馈

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## 许可证

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### 当前平台 step 验收

[当前版本真实 step](evidence/express-2026-10-20T151019Z.json)与[完整外部 HTTP 结果](evidence/verification-steps-2026-10-20T151019Z.json)已通过：官方 READY、真实 Python SDK 创建、CLI/SDK smoke，9 PASS / 0 FAIL / 1 model SKIP，耗时 319.815 秒。自有沙箱、模板及私有缓存已独立确认清理。早期失败保留为历史记录；本次未运行模型，不扩大已有镜像／模型验收范围。
