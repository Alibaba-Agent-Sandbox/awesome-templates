# DeepSeek coding harness

## 做什么

使用 DeepSeek 官方 Chat Completions 工具协议执行真实代码循环：模型可读取、写入、列目录和执行 shell，工具结果回传模型，直到最终回答。

## 技术栈

Python 3.13; `httpx==0.28.1`; Agent Sandbox server. No third-party agent CLI.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://api-docs.deepseek.com/guides/tool_calls/)

## 解决的问题

通过命名命令提供有执行期限的代码任务，返回完整缓冲输出；模型凭据在创建沙箱时注入。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

```bash
abx template install alibaba-agent-sandbox/awesome-templates//deepseek-harness
abx create --template <template-id> --env DEEPSEEK_API_KEY="$DEEPSEEK_API_KEY"
abx run <sandbox-id> deepseek --arg prompt="Inspect this project and fix the failing calculation"
```

## 快速开始（Python SDK）

客户端发行包为 `agent-sandbox-client`。安装可用性及源码固定安装见 [installation](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"DEEPSEEK_API_KEY": os.environ["DEEPSEEK_API_KEY"]})
    try:
        result = await sb.run("deepseek", prompt="Inspect and fix the calculation",
                              timeout=660)
        print(result)
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/deepseek" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600}'
```

成功响应为 `{"result":"buffered output"}`。JSON 参数直接放在请求体，无 args 包装。网关凭据由提供方规定；`ABX_SERVER_TOKEN` 为独立的服务端鉴权，未设置时可省略 Authorization。SDK 可用 `sb.server_at(9000, token=...)`。

HTTP 400：缺失、类型或范围错误；401：鉴权失败；404：未知命令；500：凭据缺失、执行失败或超时。命令返回完整缓冲结果。`command_timeout` 控制执行期限；SDK `timeout` 只控制客户端 HTTP 等待，客户端超时不保证取消。后台任务使用 process API。

## 命令参考

`deepseek` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| model | string | "" | Argument, then DEEPSEEK_MODEL, then deepseek-flash. |
| cwd | string | "" | Existing directory; relative to WORKSPACE. |
| max_turns | integer | 20 | Maximum API rounds, 1–100. |
| command_timeout | integer | 600 | Worker execution deadline, 1–1800 seconds. |

| Additional command | Parameters | Result |
|---|---|---|
| deepseek_setup_check | none | Read-only key-presence/model/tool diagnostic. |
| deepseek_tools | none | Comma-separated registered tool names; no API call. |
| run | script: string = main.py | Local Python stdout (compatibility). |

## 配置

默认 `DEEPSEEK_BASE_URL=https://api.deepseek.com`、`DEEPSEEK_MODEL=deepseek-flash`、`WORKSPACE=/home/user/app`。`DEEPSEEK_API_KEY` 缺失时使用 `OPENAI_API_KEY`。兼容服务必须显式指定端点和模型，验收与原生 DeepSeek 分开记录。shell 子进程不继承环境凭据。文件工具拒绝 cwd 外路径及符号链接逃逸，单次读写上限 128 KiB，shell 每个输出流保留最后 64 KiB。shell 具有沙箱用户权限，不受文件工具的路径检查约束。

所有密钥在 template.yaml 中为空值；不要复制到镜像或日志。

## 资源

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## 已验证

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

当前编程验收器通过 `python3 -I` 先导入可信标准库，再直接编译计算器与原测试的实际源码字节，要求原有三个测试全部成功，拒绝跳过、预期失败和意外成功。每个原测试/保留输入进程必须返回模型响应结束后才生成的随机完成确认，确认值不会进入模型提示词。提前 `SystemExit`、`os._exit(0)`、固定 `INDEPENDENT_OK` 文本和陈旧字节码都不能提供该确认。这是防止提前退出的验收检查，不是抵抗同一操作系统权限下恶意 Python 的安全边界。历史模型运行保留原验收器哈希，不能证明新门槛；必须单独记录新验收器版本在已审镜像上的真实模型复验。规范要求的完整部署与提供方认证仍是独立门槛。

尚未记录任何通过的提供方测试。

</details>

## 二次开发

```bash
python3 scripts/check_template.py deepseek-harness
python3 -m pytest -q deepseek-harness/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` 控制模型验收执行期限，默认 600 秒，范围 1–1800。L0 不调用真实模型；`E2E_REQUIRE_LLM=1` 强制真实代码验收。L3 从目标端只读诊断检查密钥，种入必失败的源码与测试，经目标文件 API 验证源码修改、新产物、原测试未修改，并独立执行 unittest 和隐藏输入计算。缺密钥不能视为验收。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py deepseek-harness`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/deepseek-harness.md).

## 问题反馈

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## 许可证

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).
