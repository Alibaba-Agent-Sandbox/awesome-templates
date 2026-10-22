# kimi-code

## 做什么

在已有沙箱目录运行官方 Kimi Code 2.2.0 的一次无头任务。每次使用私有临时配置，结束、失败和超时清理自有进程组。上游 prompt 模式自动许可工具，wrapper 须显式 allow_tools=True 才启动；返回缓冲的 stream-JSON 字符串，不提供会话续接。

## 技术栈

阿里云 FC v0.0.49、SHA256 校验的固定 Node.js 24.16.0、MIT 许可的 `@moonshot-ai/kimi-code@2.2.0` 和 Dockerfile 中固定 server SDK 源码。使用现行 Node CLI，不安装旧 Python 发行包。

## 解决的问题

在单个极速版实例内提供可复现的 Moonshot CLI、兼容模型配置、类型参数和有界工具执行；不进行交互账号登录。

## 快速开始（CLI）

先按[安装指南](../docs/using-templates.zh-CN.md)安装源码可追溯的 CLI 及 agent-sandbox-client/server。在服务进程启动前注入配置；[预热服务说明](../docs/runtime-environment.zh-CN.md)解释 create env 与已有进程的区别。

```bash
abx template deploy ./kimi-code -y
abx create --template <template-id> -y
abx run <sandbox-id> kimi_version
abx run <sandbox-id> kimi --json-args '{"prompt":"Summarize the files in the current directory.","command_timeout":120,"allow_tools":true}'
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

替换上一命令返回的 ID。这是原生 CLI；若帮助显示 detach，使用 `abx create <template-id> --detach` 和不带 -y 的 kill。命名命令仍使用 abx run。

## 快速开始（Python SDK）

客户端 distribution 是 agent-sandbox-client，按[固定源码](../docs/python-client-installation.md)安装。先配置目标服务的模型环境。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=600)
    try:
        print(await sb.run("kimi", prompt="Summarize the files in the current directory.",
                           command_timeout=120, allow_tools=True, timeout=150))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

timeout 是客户端 HTTP 预算，command_timeout 是进程组截止时间；HTTP 超时不保证取消。显式配置的服务使用对应 server_at 端口和 token。

## 快速开始（HTTP POST）

使用 port 9000 的服务 URL；服务认证和 provider gateway 认证独立，必要时加提供方明确要求的 gateway header。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/kimi"   --header 'Content-Type: application/json'   --header "Authorization: Bearer $ABX_SERVER_TOKEN"   --data '{"prompt":"Summarize the files in the current directory.","command_timeout":120,"allow_tools":true}'
# {"result":"<buffered upstream stream-JSON text>"}
```

服务无 token 时才省略 Authorization。body 直接是参数对象。参数缺失/类型错误为 400，认证 401，未知命令 404，执行或输入错误 500，包含 error/type。

## 命令参考

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| kimi_version | 无 | 固定 CLI 版本 |
| kimi_setup_check | 无 | installed/version/pinned_version、模型/key/base 是否配置及 workspace，无凭据值 |
| kimi | prompt 必填字符串，1..65536 UTF-8 字节；cwd 可选，默认 workspace，必须存在；command_timeout 默认 600，整数 1..1800 秒；allow_tools 默认 false，布尔 | 缓冲 stream-JSON；非零、超时、每流超过 8 MiB 为错误 |

真实 argv 是 `kimi --prompt PROMPT --output-format stream-json`，上游拒绝 --prompt 与 --auto/--yolo 混用，并在 prompt 模式内部自动许可工具，因此 allow_tools 必须显式为 true，否则拒绝启动。输入独立 argv，不拼接 shell。自动模式具有 user 的文件和网络权限，能改文件、执行命令。

## 配置

| 名称 | 必需 | 默认/用途 |
| --- | --- | --- |
| KIMI_MODEL_NAME | 模型任务需要 | 实际模型 ID |
| KIMI_MODEL_API_KEY | 模型任务需要 | 空 secret 声明，启动时注入 |
| KIMI_MODEL_BASE_URL | 模型任务需要 | 明确授权的兼容端点，不隐式转发凭据 |
| KIMI_MODEL_PROVIDER_TYPE | 否 | openai，也可 kimi/anthropic |
| WORKSPACE | 否 | /home/user/app |
| ABX_SERVER_TOKEN | 否 | 服务认证，默认空 |

配置名称已从实际 npm 2.2.0 runtime 核对，另见[官方配置](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md)。每次调用用独有 KIMI_CODE_HOME，保留用户配置，去除无关云端/registry 凭据，响应中脱敏 secret 及 JSON 转义形式。allow_tools=false 拒绝启动，不声称提供只读 prompt 模式。

## 资源

2 vCPU、2048 MiB、平台根文件系统、9000 端口。不需要 KVM/Docker/显示器/GPU。上游要求 Node >=22.19，固定构建已提供。镜像不含模型 key。

## 已验证


### 当前镜像验收 — 2026-10-22

| 提供方 | 当前版本与范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 1.0.0；常规镜像、真实 CLI/SDK、完整 HTTP 9 PASS / 0 FAIL / 1 SKIP、沙箱/模板/私有镜像仓库独立清理 | [运行与 HTTP 回执](evidence/image-http-2026-10-22T111230Z.json) |
| opensandbox | 1.0.0；原始 Docker 后端、逐项 CLI/SDK 命名 smoke、完整 HTTP 9 PASS / 0 FAIL / 1 SKIP、SDK/容器/进程独立清理 | [原生源码镜像回执](evidence/opensandbox-2026-10-22T111821Z.json) |

CLI 在 OpenSandbox 中通过实际 `abx exec` 调用容器内命名 HTTP API；通用 `run_code` 仍不支持，`template launch` 的能力检查仍生效。缺少模型或厂商账号的检查按回执明确跳过，不计为真实模型通过。[复现与验收范围](../docs/source-image-acceptance.zh-CN.md)。

<details>
<summary>此前验收记录（保留原有时间与范围）</summary>

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

镜像内真实模型编码验收也已通过17项检查，使用 qwen3.8-flash，见[模型回执](evidence/model-express-2026-10-19T153814Z.json)；此前失败尝试仍单独保留。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

尚未记录任何通过的提供方测试。

</details>

</details>

## 二次开发

保留真实上游 CLI，不能用 HTTP 文本响应代替 agent。版本、argv、配置和双语保持一致。运行 checker、单元及 HTTP 测试。模型验收必须真实修改已有源码、生成报告和精确产物、保留原测试并通过新随机确认的独立断言。版本检查不是模型通过。运行 `python scripts/run_steps_e2e.py kimi-code` 使用[step 流程](../docs/platform-steps.zh-CN.md)。

## 贡献

阅读[贡献规则](../CONTRIBUTING.zh-CN.md)和[设计](../docs/design/kimi-code.md)，同一 PR 更新工程记录及回归证据。

## 问题反馈

模板问题见 [Issue 48](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/48)，SDK/server 去 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 去 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。提供版本与脱敏复现。

## 许可证

模板 wrapper 为 Apache-2.0，见 [LICENSE](../LICENSE)；上游 Kimi Code 为 MIT，固定官方 npm 包保留原许可证。

### 2026-10-20完整 step 检查点：模板1.0.0

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T155159Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，9 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
