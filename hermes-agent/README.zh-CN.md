# Hermes Agent

## 做什么

运行真实 NousResearch Hermes Agent CLI，启用本地终端和文件工具。当前交付代码任务切片，未配置消息网关、浏览器、桌面或外部终端后端。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

NousResearch Hermes Agent v0.22.1, commit `297552a9d646119871391d202509822cd86330df`; private Python 3.14.6; `uv==0.12.3`; upstream frozen `uv.lock`; platform Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://github.com/NousResearch/hermes-agent/tree/297552a9d646119871391d202509822cd86330df)

## 解决的问题

通过命名命令提供真实 Hermes 无头 CLI 调用，限制 CLI 进程的等待时间并返回完整缓冲输出；模型凭据在创建沙箱时注入。网关已接受的任务具有独立生命周期。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./hermes-agent --yes
abx run <sandbox-id> hermes_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('hermes_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/hermes_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "<command result>"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

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
