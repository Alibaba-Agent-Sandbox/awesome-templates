# Factory Droid

## 做什么

在现有项目上无头运行 Factory Droid 0.241.1。具名命令提供有执行时限的编码调用、版本查询与不调用模型的安装检查。

## 技术栈

从 `https://registry.npmjs.org` 安装固定 CLI，并显式包含平台可选包。基础镜像 npm 镜像源对所需 native 包返回404；缺包会进入上游 fallback，可能使二进制成为自引用链接。

阿里云 FC 基础镜像（通常为 `v0.0.49`），镜像内 Python 3.13、Node.js 20，npm `@factory/cli@0.241.1`，以及 [Dockerfile](Dockerfile) 中固定源码版本的 `agent-sandbox-server`。模板采用 generation 2，以非 root 的 `user` 用户运行，开放 9000 端口。

## 解决的问题

自动化可通过 Agent Sandbox 上传项目，让 Droid 修改源文件，再读取产物并独立运行测试。缺少 Factory 凭据会在启动 CLI 前报错，避免交互登录等待。`WORKSPACE` 指定项目根目录；成功输出与错误消息均对已配置秘密值脱敏。

## 快速开始（CLI）

按[官方安装说明](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox#readme)安装 CLI，在 `alicloud-express` 构建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//droid
abx create --template <template-id>
abx run <sandbox-id> droid_version
abx run <sandbox-id> droid_setup_check
abx run <sandbox-id> droid --arg prompt='Review the existing project' --arg auto=''
```

使用安装返回的模板 ID。创建沙箱时通过私有环境配置注入 `FACTORY_API_KEY`；提供方凭据与 Factory 产品密钥不同。最后一条命令需要 Factory 密钥。编码前通过 SDK 文件 API 上传项目。结束后执行 `abx kill <sandbox-id> -y`。

## 快速开始（Python SDK）

客户端包名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。版本尚未发布时使用[配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=600,
        envs={"FACTORY_API_KEY": os.environ["FACTORY_API_KEY"]},
    )
    try:
        await sb.files.write("/home/user/app/calc.py", "def add(a, b):\n    return a - b\n")
        print(await sb.run("droid_version"))  # "0.241.1"
        print(await sb.run("droid", prompt="Fix calc.py so add returns the sum.",
                           auto="low", command_timeout=300, timeout=360))
        print(await sb.files.read("/home/user/app/calc.py"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`command_timeout` 控制服务端执行期限；`Sandbox.run(timeout=360)` 控制客户端 HTTP 等待时间。客户端超时不保证取消进程。具名命令返回缓冲结果；后台执行、进度和取消使用 SDK 进程 API。

## 快速开始（HTTP POST）

通过 `sb.network.get_url(9000)` 获取沙箱 9000 端口 URL：

```bash
curl -X POST '<sandbox-port-9000-url>/commands/droid' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ABX_SERVER_TOKEN}" \
  -d '{"prompt":"Fix calc.py so add returns the sum.","auto":"low","command_timeout":300}'
```

请求体直接为参数对象，不加 `args` 包装。成功响应为 `{"result":"<缓冲的 Droid 输出>"}`。`ABX_SERVER_TOKEN` 为空时去掉该头；非空时必须带 `Authorization: Bearer <token>` 或 `X-Access-Token: <token>`。Python SDK 使用 `sb.server_at(9000, token=...)`。提供方网关鉴权与服务端鉴权不同，需要另加所选提供方要求的访问头。`GET /commands` 返回签名；`POST /commands/droid_version` 与 `/commands/droid_setup_check` 接受 `{}`。

HTTP 400 表示缺少参数或类型错误；401 表示服务端鉴权失败；404 表示未知命令；500 表示参数范围无效、缺少 Factory 凭据、上游执行失败或执行超时。响应不流式返回。

## 命令参考

| 命令 | 参数 | 返回值 / 上游调用 |
| --- | --- | --- |
| `droid_version` | 无 | `droid --version` 的版本字符串；不需要模型密钥。 |
| `droid_setup_check` | 无 | 对象：`installed`（布尔），`package`、`version`、`expected_version`（字符串），`api_key_set`、`workspace_exists`、`auto_update_enabled`（布尔）。不调用模型、不返回密钥值。 |
| `droid` | `prompt`：必填非空字符串；`auto`：字符串，默认 `low`，可为 `""`、`low`、`medium`、`high`；`cwd`：字符串，默认 `""`，必须为 `WORKSPACE` 内现有目录；`command_timeout`：整数，默认 300，范围 1–600 秒 | `droid exec [--auto LEVEL] -- PROMPT` 的缓冲 stdout 字符串。非零退出或超时抛出脱敏执行错误。 |

相对 `cwd` 从 `WORKSPACE` 解析；绝对路径在解析符号链接后也必须位于根目录内。`auto=""` 不传该选项，使用上游只读模式；`low` 允许项目编辑，`medium` 还允许开发命令，`high` 允许风险更高的操作。模板不传 `--skip-permissions-unsafe`。**兼容性：** 1.1.0 将 `/app` 改为 `/home/user/app`，编码命令默认显式传 `--auto low`；需要原先只读行为时传 `auto=""`。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 默认值 | 作用 |
| --- | --- | --- |
| `FACTORY_API_KEY` | 空 | 创建时注入的 Factory 账户 API 密钥；仅 `droid` 需要。 |
| `ABX_SERVER_TOKEN` | 空 | 可选 HTTP 服务鉴权。 |
| `WORKSPACE` | `/home/user/app` | 现有项目根目录；显式配置无效目录会报错。 |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | 子进程强制禁用自动更新，保持固定版本。 |

Factory 凭据在 [Factory API 密钥设置](https://app.factory.ai/settings/api-keys)获取。DashScope 或 OpenAI 密钥不能替代 `FACTORY_API_KEY`。自定义模型配置不属于本模板 API。上游行为见 [Droid Exec](https://docs.factory.com/droid-exec/overview)，具体选项以固定版本的真实帮助为准。脱敏涵盖 stdout、错误中的原始与 JSON 转义的已配置秘密值；Agent 写出的项目文件仍需遵守正常的秘密管理要求。cwd 约束用于选择项目，不是操作系统安全隔离边界。

## 资源

默认 2 vCPU、2048 MB 内存、9000 端口。模型调用需要访问外部 Factory 网络。平台启动 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，就绪探针为 `agent-sandbox-server healthcheck --port 9000`。

## 已验证

2026-10-18 源码运行验收：原生 Python SDK 完成固定版本 Droid 后台安装、SDK 无密钥版本/配置检查、外部 HTTP 套件与自有资源清理，九项记录均通过。见[准确范围证据](../.agents/evidence/verify/2026-10-18-droid-native-runtime.md)。这不是镜像标准部署 L2 或模型验收，`tested_on` 不变。

尚未记录任何通过的提供方测试。

## 二次开发

保留阿里云基础镜像、精确 CLI/server 版本和非 root 用户。通过 `@command` 扩展 [commands.py](commands.py)，直接传 argv，保留密钥检查、脱敏和超时清理。使用 BuildKit 构建，部署可注入 server wheel。运行：

```bash
python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py
python3 scripts/check_template.py droid
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py droid
```

本地套件要求服务端 PATH 有真实固定版本 `droid`，不伪造版本。L1 还需真实 Docker 构建；L2 需要真实极速版部署并从外部断言 smoke 命令。L3 设置 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1`，服务端提供 Factory 密钥，执行 [e2e_test.py](e2e_test.py) 的编码验收：预置失败代码、修改现有源文件、保持原测试、新建并下载产物、独立重跑测试和隐藏用例。验证器通过远端文件/进程 API 检查并清理自己的项目。缺少密钥会使必需 L3 失败；仅有响应标记不能通过。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计](../docs/design/droid.md)。同步[英文 README](README.md)，PR 包含回归、工程记录与真实验证证据。必要验收通过前保持 experimental。

## 问题反馈

继续使用 [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19)。模板问题提交至 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/server 问题至 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题至 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附版本、提供方、generation 和脱敏复现；不要附密钥或原始私有日志。

## 许可证

模板代码使用 [Apache-2.0](../LICENSE)。Factory Droid 独立按上游条款分发；安装 CLI 不改变其许可证。
