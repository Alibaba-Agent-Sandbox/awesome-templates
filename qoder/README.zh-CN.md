# Qoder

## 做什么

通过真实 Qoder CLI 在沙箱中无头执行代码修改；保留原有 `qoder_run` Python 脚本命令。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Qoder CLI `@qoder-ai/qodercli@1.1.72`; platform Python 3.13 / Node.js 20; Agent Sandbox server.

[Dockerfile](Dockerfile) · [template.yaml](template.yaml) · [Upstream](https://docs.qoder.com/cli/run-in-scripts)

## 解决的问题

通过命名命令提供有执行期限的代码任务，返回完整缓冲输出；模型凭据在创建沙箱时注入。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./qoder --yes
abx run <sandbox-id> qoder_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('qoder_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/qoder_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "1.1.72"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该历史记录采用 e2cb27e 服务端来源覆盖，与当时的镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

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
