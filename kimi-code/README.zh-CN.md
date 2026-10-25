# kimi-code

## 做什么

在已有沙箱目录运行官方 Kimi Code 2.2.0 的一次无头任务。每次使用私有临时配置，结束、失败和超时清理自有进程组。上游 prompt 模式自动许可工具，wrapper 须显式 allow_tools=True 才启动；返回缓冲的 stream-JSON 字符串，不提供会话续接。

## 技术栈

阿里云 FC v0.0.49、SHA256 校验的固定 Node.js 24.16.0、MIT 许可的 `@moonshot-ai/kimi-code@2.2.0` 和 Dockerfile 中固定 server SDK 源码。使用现行 Node CLI，不安装旧 Python 发行包。

## 解决的问题

在单个极速版实例内提供可复现的 Moonshot CLI、兼容模型配置、类型参数和有界工具执行；不进行交互账号登录。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./kimi-code --yes
abx run <sandbox-id> kimi_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('kimi_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/kimi_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "2.2.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置名称已从实际 npm 2.2.0 runtime 核对，另见[官方配置](https://github.com/MoonshotAI/kimi-code/blob/main/docs/en/configuration/providers.md)。每次调用用独有 KIMI_CODE_HOME，保留用户配置，去除无关云端/registry 凭据，响应中脱敏 secret 及 JSON 转义形式。allow_tools=false 拒绝启动，不声称提供只读 prompt 模式。

## 资源

2 vCPU、2048 MiB、平台根文件系统、9000 端口。不需要 KVM/Docker/显示器/GPU。上游要求 Node >=22.19，固定构建已提供。镜像不含模型 key。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

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
