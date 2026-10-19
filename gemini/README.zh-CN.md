# gemini

实验状态的 Gemini CLI 模板。[English](README.md)。

## 做什么

通过具名命令 `gemini` 无头运行固定版本 Gemini CLI。`gemini_version` 和 `gemini_setup_check` 检查安装与配置。模型调用需要真实 Gemini 密钥；OpenAI 兼容密钥不能代替。

## 技术栈

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`（部署时解析区域与版本）、Node.js >=20、`@google/gemini-cli@0.64.0`。server 固定 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505`，部署注入 wheel 时优先使用 wheel。以 `user` 身份在 `/home/user/app` 运行；generation 2 的启动与健康检查见 [template.yaml](template.yaml)，镜像无 CMD/ENTRYPOINT。

## 解决的问题

提供有类型的缓冲结果调用、缺密钥保护、只读配置诊断、显式工具权限与进程组截止时间。默认使用上游 `plan` 只读模式；只有 `yolo=true` 才批准编辑与 shell 工具。沙箱运行时负责隔离；cwd 校验仅限制起始目录。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在仓库目录内使用已有 provider 配置：

```bash
abx template deploy ./gemini -y
abx create --template <template-id> -y --env GEMINI_API_KEY="$GEMINI_API_KEY"
abx run <sandbox-id> gemini_version
abx run <sandbox-id> gemini_setup_check
abx run <sandbox-id> gemini --json-args '{"prompt":"Describe the project files","command_timeout":120,"yolo":false}'
```

授权编码时显式传 `"yolo":true`，`cwd` 应为 `WORKSPACE` 内已存在的项目目录。替换 generation-1 模板时使用新别名，不直接附带 generation-2 启动参数更新旧模板。结束后用 `abx kill <sandbox-id> -y` 和 `abx template delete <template-id> -y` 清理本次资源。

## 快速开始（Python SDK）

客户端包是 `agent-sandbox-client`，导入名为 `agent_sandbox`。先核实版本是否发布，或使用[配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300,
                              envs={"GEMINI_API_KEY": os.environ["GEMINI_API_KEY"]})
    try:
        print(await sb.run("gemini", prompt="Describe the project files",
                           command_timeout=120, yolo=False, timeout=150))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 调具名命令；`sb.commands.run` 执行 shell。`command_timeout` 控制服务端 CLI 进程组执行时限，`timeout` 控制客户端 HTTP 等待；客户端超时不保证取消。后台任务和取消请使用进程 API。

## 快速开始（HTTP POST）

`ABX_SERVER_URL` 使用 `sb.network.get_url(9000)` 的地址，本地为 `http://127.0.0.1:9000`：

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/gemini" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{"prompt":"Describe the project files","command_timeout":120,"yolo":false}'
```

参数直接置于 JSON 顶层，无 `args` 包装。HTTP 200 返回 `{"result":"<缓冲的 Gemini JSON 输出>"}`。服务端未设置 `ABX_SERVER_TOKEN` 时省略 Authorization。Provider 网关鉴权独立存在，还需添加所选 provider 要求的访问头；服务端 token 不自动等于网关 token。

缺参数或类型错误为 400，鉴权失败 401，未知命令 404；参数范围/目录非法、空提示词、缺密钥、CLI 缺失、执行超时与上游失败为 500，错误格式 `{"error":"...","type":"..."}`。服务端先转换参数类型；请传 JSON 数字与布尔值。CLI 成功和失败输出均替换秘密环境变量的值。

## 命令参考

| 命令 | 参数 | 返回 |
|---|---|---|
| `gemini` | `prompt`：必填非空字符串；`model`：字符串，默认 `""` → `GEMINI_MODEL` → `gemini-3.1-flash-lite`；`cwd`：字符串，默认 `""` → `WORKSPACE`；`command_timeout`：整数 1–1800 秒，默认 600；`yolo`：布尔值，默认 false | 上游缓冲 JSON 字符串 |
| `gemini_version` | 无 | CLI 版本字符串，预期 `0.64.0` |
| `gemini_setup_check` | 无 | 安装/版本/pin、密钥存在布尔值、模型配置布尔值/工作目录及配置文件元信息；不返回密钥或配置值 |

`cwd` 必须存在且真实路径位于 `WORKSPACE` 内；相对路径以其为根，拒绝穿越与符号链接逃逸。argv 为 `gemini -p <prompt> --model <model> --output-format json --approval-mode plan`，显式授权后才改为 `yolo`。标准输入关闭；不臆造上游不存在的 turn-limit 参数。诊断不改写用户或项目的 `.gemini/settings.json`；JSON 对象检查不等于上游 schema 校验。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 默认值 | 用途 |
|---|---|---|
| `GEMINI_API_KEY` | 空 | 模型调用必需；空白同样在启动 CLI 前失败，防止交互式 OAuth 登录 |
| `GEMINI_MODEL` | `gemini-3.1-flash-lite` | 默认模型；须为密钥可用模型 |
| `WORKSPACE` | `/home/user/app` | 已存在的执行根目录 |
| `ABX_SERVER_TOKEN` | 空 | 可选服务端 bearer 鉴权，创建时注入 |
| `ABX_SERVER_PORT` | `9000` | 本地独立服务端口 |

现有上游鉴权配置由用户管理；wrapper 不改写 OAuth/Vertex profile，若与 API-key 模式冲突应检查现有配置。禁止在模板、镜像、报告或提交的环境文件中写入秘密值。

## 资源

2 vCPU、4096 MB 内存、9000 端口；Express 根文件系统约 10G。不需要嵌套 Docker、KVM 或额外 capabilities。

## 已验证

尚无 provider 验收记录。本地诊断与 mock 回归不代表镜像、云端或模型通过；`tested_on` 为空，目录状态保持 experimental。见[验证记录](../.agents/evidence/verify/2026-10-16-gemini-runtime.md)。

## 二次开发

阅读[设计](../docs/design/gemini.md)，保留固定 npm/server 版本、Alibaba base、非 root 与 generation-2 启动。运行 `python3 scripts/check_template.py gemini`、`python3 -m pytest gemini/test_commands.py gemini/test_e2e_protocol.py -q`、`python3 scripts/run_local_e2e.py`。本地套件需要 server/client 依赖；`E2E_RUN_LLM=0` 跳过模型且不发编码请求。

L1 必须真实构建；L2 必须部署并从外部调用 CLI/SDK。L3 在目标服务注入 `GEMINI_API_KEY`，控制端设置 `E2E_BASE_URL` 与目标 `WORKSPACE` 内的 `E2E_BASE_DIR`，运行 `E2E_REQUIRE_LLM=1 E2E_RUN_LLM=1 python3 gemini/e2e_test.py`。仅目标需要密钥。测试经远端 files API 创建失败源码和测试，显式 yolo 要求修复和新增产物，核对测试未改写，独立远端运行原测试与保留计算，最后删除唯一项目。仅返回标记不能通过。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py gemini`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵守[贡献规则](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)及工程记录。复用 [Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30)。失败、跳过和阻塞分别记录；缺真实密钥是必需 L3 的阻塞，不是通过。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI 报告使用 `[templates]` 前缀。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。
