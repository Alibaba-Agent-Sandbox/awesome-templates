# SWE 本地评测切片

[English](README.md)

## 做什么

使用官方 `mini-swe-agent==2.4.6` 修复真正的 SWE-bench Verified 题目 `pallets__flask-5014`。准备固定 Flask base commit 和原始测试补丁，重现 1 个失败与 59 个通过；显式授权后由代理改源码，在另一个全新检出目录和 venv 中评测，交回源码补丁及 JSON 报告。

这只是单题的环境可移植性切片。没有运行官方 Docker harness，也没有复刻其完整原始依赖和系统环境，不产生官方 SWE-bench 分数。评测解释器现固定为原题的 Python 3.11.10；下列依赖和 Debian 基础镜像仍属于单独验证的环境。完整 SWE-agent、SWE-rebench、任意题目和批量评测不在本切片范围内。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

构建器解析的阿里云 `v0.0.49` 基础镜像，Python 3.13 服务端/代理、官方 SHA 固定的独立 Python 3.11.10 评测运行时，保留原 Node.js 20，mini-swe-agent 2.4.6、LiteLLM 1.82.6、pytest 8.3.5。已发布服务端包。所有固定依赖见 [Dockerfile](./Dockerfile)。不需要嵌套 Docker、运行时系统安装或下载整份数据集。

## 解决的问题

把实际修复与代理声称完成分开。评测器重新展开原始快照和测试补丁，只应用 `src/flask/blueprints.py` 的改动，要求准确运行声明的全部 60 个测试。代理修改自己的测试或输出 marker 都不能得到通过报告。`resolved_slice` 仅描述当前环境结果，不能作为官方 benchmark 分数。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

启动前填写下列模型配置：API Key、接入点、模型 ID 必须属于同一个模型服务与地域。`https://model.example.invalid/v1` 是占位符，请替换为供应商给出的 API base，不要填写网页聊天地址。模型 ID 使用该端点实际支持的名称。

此入口使用模型 API Key，无需运行浏览器 OAuth 登录，也不会继承你本机已登录的账号。模型接入要求见“配置”；本模板使用 **Chat Completions**，不能只凭“OpenAI 兼容”字样推断接口可用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export SWE_API_KEY='<your-model-api-key>'
export SWE_BASE_URL='https://model.example.invalid/v1'
export SWE_MODEL='<your-model-id>'
export ABX_HTTP_TIMEOUT=1200
abx template launch Alibaba-Agent-Sandbox/awesome-templates//swe --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" swe_prepare --json-args '{}'
```

返回 `pallets__flask-5014` 的 `run_id` 和失败基线，请保留该 ID 用于后续编码和评测。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

准备后复制 `run_id` 到 `RUN_ID`；只在同意模型执行 shell 时使用 `allow_execution:true`。以下执行模型修复、在全新副本评测、下载报告/补丁，然后删除该 run。模型效果不保证成功；检查返回的测试状态，而非把任何 200 当修复成功。

```bash
export RUN_ID='paste-run-id'
abx run "$SANDBOX_ID" swe_run_agent --json-args "{\"run_id\":\"$RUN_ID\",\"allow_execution\":true,\"max_steps\":30,\"command_timeout\":600}"
abx run "$SANDBOX_ID" swe_evaluate --arg run_id="$RUN_ID"
abx run "$SANDBOX_ID" swe_report --arg run_id="$RUN_ID"
# 把返回的报告/补丁路径分别下载到本机，再清理
abx download "$SANDBOX_ID" '<returned-report-path>' ./report.json
abx download "$SANDBOX_ID" '<returned-patch-path>' ./repair.patch
abx run "$SANDBOX_ID" swe_cleanup --arg run_id="$RUN_ID"
```

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

以下是 CLI 修复流程的完整 SDK 写法。先启动实例、设置 `SANDBOX_ID`，然后保存为 `use_template.py` 并执行 `python3 use_template.py`。`allow_execution=True` 明确授权模型执行 shell；脚本在本机保存报告与补丁，最终删除该 run 并关闭连接；外层沙箱仍需按后文释放。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=1200
        )
        try:
            prepared = await client.commands.run("swe_prepare")
            print(prepared)
            run_id = prepared["run_id"]
            try:
                print(await client.commands.run("swe_run_agent", run_id=run_id,
                    allow_execution=True, max_steps=30, command_timeout=600))
                report = await client.commands.run("swe_evaluate", run_id=run_id)
                print(report)
                Path("report.json").write_bytes(
                    await sb.files.read_bytes(report["report_path"]))
                Path("repair.patch").write_bytes(
                    await sb.files.read_bytes(report["patch_path"]))
            finally:
                await client.commands.run("swe_cleanup", run_id=run_id)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/swe_prepare`

```json
{}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 1200 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

后续按顺序请求：

- `POST /commands/swe_run_agent`: `{"run_id":"<returned-run-id>","allow_execution":true,"max_steps":30,"command_timeout":600}`
- `POST /commands/swe_evaluate`: `{"run_id":"<returned-run-id>"}`
- `POST /commands/swe_report`: `{"run_id":"<returned-run-id>"}`
- `POST /commands/swe_cleanup`: `{"run_id":"<returned-run-id>"}`

## 命令参考

| 命令 | 参数 | 返回 / 执行 |
|---|---|---|
| `swe_version` | 无 | 实际 `mini --help` 与已安装 distribution 版本，无需 key |
| `swe_setup_check` | 无 | 运行时、key、base、model 是否存在的布尔值，不返回秘密值 |
| `swe_prepare` | `instance_id: str = "pallets__flask-5014"` | `run_id` 及独立重现的基线；拒绝其他题目 |
| `swe_run_agent` | 必填 `run_id: str`；`allow_execution: bool = false`；`max_steps: int = 12`（1–30）；`command_timeout: int = 300`（30–900） | 实际 `mini -c <已安装 default.yaml 或 mini.yaml> -c <私有 config.yaml> -o <私有 trajectory>`；必须显式允许 shell；返回模型调用次数与 Submitted 状态 |
| `swe_evaluate` | 必填 `run_id: str` | 全新 base、原始测试和指定源码差异；准确测试状态、计数、`resolved_slice`、`official_benchmark_score: false`、补丁与报告路径 |
| `swe_report` | 必填 `run_id: str` | 上次评测及产物路径；未评测先拒绝 |
| `swe_cleanup` | 必填 `run_id: str` | 只删除该任务所属目录，返回 true |

类型错误或未知参数返回 HTTP 400。实例/任务无效、缺少显式权限或配置、上游失败、测试缺项及超时返回不含敏感输出的 HTTP 500。测试真正失败会生成 `resolved_slice: false` 报告；收集错误不产生分数。同任务操作使用排他锁，冲突直接拒绝。命令同步运行，HTTP 断开不等于取消；使用命令期限或销毁自有沙箱停止任务。

## 配置

此入口调用兼容 Chat Completions API，base 包含供应商要求的前缀（常见 `/v1`），不要额外添加 `/chat/completions`。默认 text 协议要求模型按上游格式返回 bash 操作与提交，不会自动改为原生 toolcall。

| 变量 | 要求 / 默认值 | 含义 |
| --- | --- | --- |
| `SWE_API_KEY` | 模型执行必需 | 兼容模型服务的 API Key。 |
| `SWE_BASE_URL` | 模型执行必需 | Chat Completions API base，例如供应商 HTTPS `/v1` 接入点。 |
| `SWE_MODEL` | 模型执行必需 | 端点实际模型 ID；包装层自行添加 LiteLLM `openai/` 前缀。 |
| `SWE_MODEL_PROTOCOL` | 当前模板固定默认 `toolcall` | `toolcall` 使用上游原生 bash function calls，要求模型/端点支持工具；`text` 使用上游文本协议。 |
| `ABX_SERVER_TOKEN` | 必需 | 独立的应用访问口令。 |

1.2.0 版本默认使用上游原生 bash 工具调用，模型和端点必须支持 Chat Completions 工具调用。旧版1.1.2 默认使用文本动作协议。`SWE_MODEL_PROTOCOL` 在当前 manifest 中是非空 `toolcall`，主机 export 不会覆盖它；如需保留旧版文本协议，请复制为自己的模板，显式设置 `SWE_MODEL_PROTOCOL: text` 后按[本地源码用法](../docs/using-templates.zh-CN.md)启动。模型 API Key、base、model 三个字段为空，按上面的 export 填入即可。

模型生成的 shell 命令拥有沙箱用户的文件与网络权限，应使用一次性沙箱和可信任务。当前只提供内置 Flask 实例，评测切片不是完整官方 Docker benchmark。启动前导出模型设置；在本机稍后修改变量不会重配已启动应用。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB，命令端口 9000。只内置一个固定 Flask 实例；Agent 与 Python 3.11.10 评测环境独立。每个 run 及独立评测复制自己的环境，运行文件持续占用磁盘直到 `swe_cleanup` 或删除沙箱。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/swe.md)。

## 问题反馈

[模板 Issue #35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35)负责本切片与剩余官方/完整部署门禁。SDK/服务端问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Wrapper 为 Apache-2.0；mini-swe-agent 2.4.6 为 MIT；Flask 为 BSD-3-Clause；SWE-bench Verified 元数据和测试补丁遵循数据集 MIT 许可证。随附 CPython 保留其 distribution 许可证文件。来源和许可证链接见 [NOTICE](./NOTICE.md)，原始源码归档保留自己的许可证文件。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
