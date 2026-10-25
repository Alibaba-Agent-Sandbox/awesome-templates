# DeepSeek coding harness

## 做什么

使用 DeepSeek 官方 Chat Completions 工具协议执行真实代码循环：模型可读取、写入、列目录和执行 shell，工具结果回传模型，直到最终回答。

## 技术栈

Python 3.13; `httpx==0.28.1`; Agent Sandbox server. No third-party agent CLI.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://api-docs.deepseek.com/guides/tool_calls/)

## 解决的问题

通过命名命令提供有执行期限的代码任务，返回完整缓冲输出；模型凭据在创建沙箱时注入。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./deepseek-harness --yes
abx run <sandbox-id> deepseek_tools --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('deepseek_tools'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/deepseek_tools`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "list_files,read_file,run_shell,write_file"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

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

### 2026-10-20完整 step 检查点：模板1.1.1

[真实对应版本 step](evidence/express-2026-10-20T154957Z.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154957Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，9 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
