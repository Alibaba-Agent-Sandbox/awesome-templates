# agents-cli

通过受限的本地 Agents HTTP API 调用固定版本的 Codex 和 Qwen Code。

## 做什么

安装 `@openai/codex@0.162.1`、`@qwen-code/qwen-code@0.23.0`，提供版本检查和六个
会话/运行时接口。客户端创建会话、提交消息并轮询输出。响应头
`X-Agent-Sandbox-Local: 1` 表示本地实现，不表示 OpenAI 托管 Agents 服务。

直接运行和模板配置的 canonical `serve` 启动方式都加载
[server-policy.json](./server-policy.json)。通用 shell、文件、进程、模型列表以及
其余 Agents 接口关闭。关闭 HTTP shell/文件接口不会移除上游 CLI 的工作区工具权限。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- 阿里云 generation 2 基础镜像及其 Python；安装经 SHA256 校验的官方 Node.js `24.16.0`，替换基础 Node 20，满足 Qwen Code 的 Node >=22 要求。
- Codex `0.162.1`、Qwen Code `0.23.0`，镜像构建时断言两个实际版本。
- 非 root 用户 `user`；程序 `/home/user/app`，工作区 `/home/user/workspace`，端口 9000。

## 解决的问题

用一套 HTTP 会话接口选择两个已安装的编码 CLI，同时保持通用沙箱接口关闭。
版本检查调用真实 CLI；关闭模型测试时不会自动换成模拟程序。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./agents-cli --yes
abx run <sandbox-id> agents_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('agents_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/agents_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "codex 0.162.1; qwen-code 0.23.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回 | 执行 |
|---|---|---|---|
| `agents_version` | 无，`{}` | 缓冲字符串 | 真实 `codex --version` 和 `qwen --version`，各最多 20 秒；缺 CLI 或版本不符返回错误，不输出原始 CLI 内容 |

| 开放接口 | 用途 |
|---|---|
| `GET /commands`、`POST /commands/agents_version` | 发现/执行版本检查 |
| `POST /v1/agents/sessions` | 创建会话；`adapter` 支持 `codex`、`qwen-code`，默认 Codex |
| `GET /v1/agents/sessions`、`GET /v1/agents/sessions/{id}` | 列表/重连 |
| `POST /v1/agents/sessions/{id}/events` | 消息入队 |
| `GET /v1/agents/sessions/{id}/items` | 轮询输出 |
| `GET /v1/agents/runtimes` | 检查声明、实现及已安装的运行时 |

会话记录和输出在服务进程内保存，重启后丢失。删除/取消/更新/SSE，以及通用 shell/
文件接口均不在 allowlist 中。销毁自己创建的沙箱可结束其中的服务及资源。

## 配置

| 名称 | 必需 | 用途 |
|---|---|---|
| `ABX_SERVER_TOKEN` | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `OPENAI_API_KEY` | 兼容模型调用需要 | Qwen 及兼容 Codex 配置的模型凭据，清单中为空 |
| `CODEX_API_KEY` | Codex 可选替代项 | 清单中为空；实际支持取决于上游及提供方配置 |
| `OPENAI_BASE_URL`、`OPENAI_MODEL` | 取决于提供方 | Qwen 兼容端点和模型配置 |
| `CODEX_HOME` | 否 | Codex 状态目录，默认 `/home/user/.codex` |
| `WORKSPACE` | 否 | `/home/user/workspace`；会话请求应显式指定目标目录 |
| `ABX_SERVER_POLICY_FILE` | 镜像已设置 | 随附策略文件路径；canonical start_cmd 还显式传入 `--policy` |

修改策略会改变 HTTP 接口范围；本模板契约基于随附 allowlist。
`E2E_RUN_LLM=0` 仅控制测试，不修改生产 PATH，也不安装 fixture。

## 资源

2 vCPU、4096 MB 内存、端口 9000。Express rootfs 约 10 GB。
尚未测量模型/工具任务的内存和时延，也未声称镜像大小验收。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该历史记录采用 e2cb27e 服务端来源覆盖，与当时的镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

## 二次开发

保持 Dockerfile、commands.py、smoke 和 fixture 的固定版本一致。在仓库根目录运行：

```bash
python -m pytest --import-mode=importlib -q agents-cli/test_protocol.py
python scripts/check_template.py agents-cli
python scripts/run_local_e2e.py
```

协议测试仅给自己的子进程显式设置 `e2e-bin` PATH，覆盖两种启动方式、认证、关闭接口
及每个 adapter 的两轮任务。Dockerfile 不复制这些 fixture。默认 e2e 要求真实 CLI，
不提交模型任务。设置 `E2E_REQUIRE_LLM=1` 或 `E2E_RUN_LLM=1` 时仍退出非零，并提示运行
`e2e_sdk.py`，不会信任外部回执或任意 verifier hook。无网络负控可运行
`python -m pytest --import-mode=importlib -q agents-cli/test_sdk_verifier.py`；它们与实际
模型/提供方验收分别记录。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py agents-cli`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)和
[设计](../docs/design/agents-cli.md)。工作关联 [Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25)。

## 问题反馈

模板和策略集成：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
运行时/API：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。上游 CLI 保留各自许可证。

### 2026-10-20完整 step 检查点：模板2.0.1

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154625Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，18 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
