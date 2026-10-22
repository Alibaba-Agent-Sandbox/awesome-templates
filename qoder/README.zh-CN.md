# Qoder

## 做什么

通过真实 Qoder CLI 在沙箱中无头执行代码修改；保留原有 `qoder_run` Python 脚本命令。

## 技术栈

Qoder CLI `@qoder-ai/qodercli@1.1.72`; platform Python 3.13 / Node.js 20; Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://docs.qoder.com/cli/run-in-scripts)

## 解决的问题

通过命名命令提供有执行期限的代码任务，返回完整缓冲输出；模型凭据在创建沙箱时注入。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

```bash
abx template install alibaba-agent-sandbox/awesome-templates//qoder
abx create --template <template-id> --env QODER_PERSONAL_ACCESS_TOKEN="$QODER_PERSONAL_ACCESS_TOKEN"
abx run <sandbox-id> qoder --arg prompt="Inspect this project and fix the failing calculation"
```

## 快速开始（Python SDK）

客户端发行包为 `agent-sandbox-client`。安装可用性及源码固定安装见 [installation](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=900,
                              envs={"QODER_PERSONAL_ACCESS_TOKEN": os.environ["QODER_PERSONAL_ACCESS_TOKEN"]})
    try:
        result = await sb.run("qoder", prompt="Inspect and fix the calculation",
                              timeout=660)
        print(result)
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -X POST "$SANDBOX_PORT_9000_URL/commands/qoder" \
  -H 'Content-Type: application/json' \
  -H "X-Access-Token: $GATEWAY_ACCESS_TOKEN" \
  -H "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Inspect and fix the calculation","command_timeout":600}'
```

成功响应为 `{"result":"buffered output"}`。JSON 参数直接放在请求体，无 args 包装。网关凭据由提供方规定；`ABX_SERVER_TOKEN` 为独立的服务端鉴权，未设置时可省略 Authorization。SDK 可用 `sb.server_at(9000, token=...)`。

HTTP 400：缺失、类型或范围错误；401：鉴权失败；404：未知命令；500：凭据缺失、执行失败或超时。命令返回完整缓冲结果。`command_timeout` 控制执行期限；SDK `timeout` 只控制客户端 HTTP 等待，客户端超时不保证取消。后台任务使用 process API。

## 命令参考

`qoder` → buffered string.

| Parameter | Type | Required/default | Meaning |
|---|---|---|---|
| prompt | string | required | Task text; nonempty. |
| cwd | string | "" | Existing directory; relative paths resolve under WORKSPACE. |
| command_timeout | integer | 600 | Execution deadline, 1–1800 seconds. |

| Additional command | Parameters | Result |
|---|---|---|
| qoder_version | none | Installed CLI version. |
| qoder_setup_check | none | Read-only installed/version/PAT-presence diagnostic. |
| qoder_run | script: string = main.py | Local Python stdout; does not call Qoder. |

## 配置

`WORKSPACE=/home/user/app`。模型调用必须注入 `QODER_PERSONAL_ACCESS_TOKEN`，不会启动浏览器登录。`accept_edits` 自动批准文件编辑，shell 确认由上游拒绝；禁用会话持久化和自动更新。

所有密钥在 template.yaml 中为空值；不要复制到镜像或日志。

## 资源

2 vCPU · 2048 MB · port 9000 · `/home/user/app` · non-root `user`.

## 已验证


### 当前镜像验收 — 2026-10-22

| 提供方 | 当前版本与范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 1.1.1；常规镜像、真实 CLI/SDK、完整 HTTP 9 PASS / 0 FAIL / 1 SKIP、沙箱/模板/私有镜像仓库独立清理 | [运行与 HTTP 回执](evidence/image-http-2026-10-22T113531Z.json) |
| opensandbox | 1.1.1；原始 Docker 后端、逐项 CLI/SDK 命名 smoke、完整 HTTP 9 PASS / 0 FAIL / 1 SKIP、SDK/容器/进程独立清理 | [原生源码镜像回执](evidence/opensandbox-2026-10-22T112920Z.json) |

CLI 在 OpenSandbox 中通过实际 `abx exec` 调用容器内命名 HTTP API；通用 `run_code` 仍不支持，`template launch` 的能力检查仍生效。缺少模型或厂商账号的检查按回执明确跳过，不计为真实模型通过。[复现与验收范围](../docs/source-image-acceptance.zh-CN.md)。

<details>
<summary>此前验收记录（保留原有时间与范围）</summary>

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.1.1; steps构建、官方READY、CLI/SDK基础冒烟、独立清理；当前版本真实模型尚未执行 | [2026-10-19](evidence/express-2026-10-19T184147Z.json) |

新版本的目录归属已在真实生成步骤中验证。旧版本回执保持历史范围；基础冒烟不能推断完整模型验收。

2026-10-21对未改动的模板1.1.1重新验证程序／API：不可变原生steps、官方READY、真实SDK创建、CLI/SDK版本smoke通过，完整HTTP9项通过、1项凭证依赖测试跳过。另起独立认证命令服务，通过SDK qoder调用真实原版Qoder1.1.72，使用固定且明确无效的合成PAT；原生程序正确拒绝认证。这是预期错误路径测试，不是厂商／模型成功调用。未使用真实厂商凭证，当前认证后的代码／模型验收仍未执行。次级服务／端口及沙箱／模板均独立确认清理，耗时140.071秒。[当前回执](evidence/express-2026-10-21T093940Z.json)、[程序／API证明](evidence/verification-steps-2026-10-21T093940Z.json)。

</details>

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

尚未记录任何通过的提供方测试。

</details>

## 二次开发

```bash
python3 scripts/check_template.py qoder
python3 -m pytest -q qoder/test_commands.py
python3 scripts/run_local_e2e.py
```

`E2E_COMMAND_TIMEOUT` 控制模型验收执行期限，默认 600 秒，范围 1–1800。L0 不调用真实模型；`E2E_REQUIRE_LLM=1` 强制真实代码验收。L3 从目标端只读诊断检查密钥，种入必失败的源码与测试，经目标文件 API 验证源码修改、新产物、原测试未修改，并独立执行 unittest 和隐藏输入计算。缺密钥不能视为验收。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py qoder`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) · [spec](../docs/template-spec.md) · [design](../docs/design/qoder.md).

## 问题反馈

[Template issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). [Python SDK/server issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues); [CLI issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). Include sanitized commands, versions and provider; omit keys.

## 许可证

Apache-2.0 template code. Upstream tools retain their own licenses and attribution. See [LICENSE](../LICENSE).

### 2026-10-20完整 step 检查点：模板1.1.1

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T155408Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，9 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
