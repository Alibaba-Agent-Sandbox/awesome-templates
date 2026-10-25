# SWE 本地评测切片

## 做什么

使用官方 `mini-swe-agent==2.4.6` 修复真正的 SWE-bench Verified 题目 `pallets__flask-5014`。准备固定 Flask base commit 和原始测试补丁，重现 1 个失败与 59 个通过；显式授权后由代理改源码，在另一个全新检出目录和 venv 中评测，交回源码补丁及 JSON 报告。

这只是单题的环境可移植性切片。没有运行官方 Docker harness，也没有复刻其完整原始依赖和系统环境，不产生官方 SWE-bench 分数。评测解释器现固定为原题的 Python 3.11.10；下列依赖和 Debian 基础镜像仍属于单独验证的环境。完整 SWE-agent、SWE-rebench、任意题目和批量评测不在本切片范围内。

## 技术栈

构建器解析的阿里云 `v0.0.49` 基础镜像，Python 3.13 服务端/代理、官方 SHA 固定的独立 Python 3.11.10 评测运行时，保留原 Node.js 20，mini-swe-agent 2.4.6、LiteLLM 1.82.6、pytest 8.3.5。沙箱服务端源码固定于 `e2cb27e24fde0a67112f82b8d44af463445a5d1a`。所有固定依赖见 [Dockerfile](./Dockerfile)。不需要嵌套 Docker、运行时系统安装或下载整份数据集。

## 解决的问题

把实际修复与代理声称完成分开。评测器重新展开原始快照和测试补丁，只应用 `src/flask/blueprints.py` 的改动，要求准确运行声明的全部 60 个测试。代理修改自己的测试或输出 marker 都不能得到通过报告。`resolved_slice` 仅描述当前环境结果，不能作为官方 benchmark 分数。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./swe --yes
abx run <sandbox-id> swe_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('swe_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/swe_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "mini-swe-agent 2.4.6"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

实测实例工作流显式允许30步和600秒，HTTP时限660秒。公开API默认值仍为12步/300秒；较早尝试中，所用模型未在该保守预算内完成。另一次自有云沙箱诊断在25次调用后提交，并由独立评测器通过原有全部60个测试身份。随后使用该预算的严格重跑仍未提交；诊断成功不能作为模板验收。版本1.1.0新增上游原生 bash 工具调用协议：启动配置服务时设置 `SWE_MODEL_PROTOCOL=toolcall`，选择官方 `mini.yaml` 和 LiteLLM 原生函数调用。默认 `text` 保留原有 `default.yaml` 文本协议；未知取值在运行前拒绝。诊断返回 `native_tool_calls`，严格验收要求其为真。原始测试身份、全新评测器和评分断言保持原样。新构建1.1.0镜像的真实云端/模型验收已通过，见下方回执。


YAML 声明空的 `SWE_API_KEY`、`SWE_BASE_URL`、`SWE_MODEL`，必须明确注入服务进程。模型 key 只传给代理进程环境，不进入模型 shell action 的环境。凭据不放 argv、配置 JSON、返回错误或持久报告。私有 trajectory/config 目录由 finally 删除。这是进程卫生措施，不能防止同用户恶意代码读取其他进程。

保留 HOME 原值。官方 `MSWEA_GLOBAL_CONFIG_DIR` 指向新的私有目录，`MSWEA_CONFIGURED=true` 禁交互 setup，禁 dotenv，并使用已安装包中 default config 的绝对路径。不继承模型、提供方、代理和 Git 环境覆盖项。上游默认 local backend 每个 action 自建 session；这里通过其公开环境扩展接口，让普通子代继承一个代理所属进程组，退出/超时清理整个组。主动 setsid/daemonize 脱组的恶意进程不在该保证内。

只对可信任务和模型使用一次性沙箱：mini 会以当前用户文件/网络权限执行模型生成的 bash。限定补丁只限制评测输入，不限制运行中的代理写入位置。最终销毁整个自有沙箱才是清理边界。run_id 不是认证机制。

## 资源

2 vCPU、2048 MiB。默认 9000 端口；显式配置示例使用 9010。固定 Flask 压缩包为 692792 字节，只带一道题。代理与 Python 3.11.10 评测依赖分别装入 venv，避免包冲突；每次任务及独立评测再复制固定评测 venv。显式 cleanup 释放任务文件，之后销毁沙箱。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

尚未记录任何通过的提供方测试。

L0 可以跳过缺失的上游运行时/模型前置，这不证明代理运行。L1/L2/L3 结果以 PR 和 owner evidence 为准。首版 Python3.13 真实镜像因上游把 pkgutil.get_loader 弃用视为错误，得到 2PASS/58ERROR；保留原测试和 warning filter，现固定原题 Python3.11.10，真实 CI 镜像已通过准确1FAIL59PASS基线、实际mini/Qwen3.8-flash修复、全新环境60PASS与远端补丁/报告读取（14PASS/0FAIL/0SKIP）。10项自有资源清理和额外严格不存在性回查均通过，见[实际镜像证据](./evidence/image-runtime-2026-10-16-configured.json)和[严格回查](./evidence/image-runtime-2026-10-16-strict-readback.json)。完整本地abx template deploy尚未运行，因此正式提供方验证仍为空。官方完整 Docker harness 与其他提供方未验证；不要把本报告发表为 benchmark 分数。

## 二次开发

阅读[设计](../docs/design/swe.md)与[规范](../docs/template-spec.md)。新增题目前核对固定源归档、许可证、原始测试补丁、精确 FAIL_TO_PASS/PASS_TO_PASS、兼容的固定依赖及独立失败/通过结果。不要通过 API 暴露任意 shell 测试命令、URL 下载或调用者自带补丁。manifest 故意不包含上游标准答案补丁。

### Agent Sandbox step 构建
实际1.1.0 step尝试在1200秒内未独立确认READY，保留为[失败](evidence/verification-steps-2026-10-20T091943Z.json)，并有[单独清理回查](evidence/steps-cleanup-2026-10-20.json)。不认定step构建通过；当前镜像/模型通过回执独立保留。


在仓库 checkout 执行 `python scripts/run_steps_e2e.py swe`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

执行 `python -m pytest -q swe/test_commands.py swe/test_e2e_protocol.py`、`python3 scripts/check_template.py swe`、`python3 scripts/test_spec_tools.py` 与 `python3 scripts/run_local_e2e.py`。构建真实镜像，跑[标准 Express 部署](../scripts/express_e2e.py)，再配置兼容模型后执行 `E2E_REQUIRE_LLM=1 E2E_RUN_LLM=1 E2E_BASE_URL=<已配置服务> python swe/e2e_test.py`。保留失败/跳过，记录准确版本、测试身份、补丁读取与自有资源清理。不要提交原始 trajectory、凭据或私有资源 ID。

## 问题反馈

[模板 Issue #35](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35)负责本切片与剩余官方/完整部署门禁。SDK/服务端问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Wrapper 为 Apache-2.0；mini-swe-agent 2.4.6 为 MIT；Flask 为 BSD-3-Clause；SWE-bench Verified 元数据和测试补丁遵循数据集 MIT 许可证。随附 CPython 保留其 distribution 许可证文件。来源和许可证链接见 [NOTICE](./NOTICE.md)，原始源码归档保留自己的许可证文件。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。

### 当前平台 step 验收

后续[当前版本真实 step 回执](evidence/express-2026-10-20T143844Z.json)及[完整外部 HTTP 结果](evidence/verification-steps-2026-10-20T143844Z.json)已通过：官方 READY、真实 Python SDK 创建和 CLI/SDK smoke，耗时 1090.426 秒；5 HTTP PASS / 0 FAIL / 1 explicit model SKIP。自有沙箱、模板和临时私有缓存已独立确认清理。此前失败记录保留；本次未运行模型，既有镜像／模型回执保持原范围。
