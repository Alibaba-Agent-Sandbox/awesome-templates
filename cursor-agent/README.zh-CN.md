# Cursor Agent

[English](README.md)。

## 做什么

通过类型化命名命令，在自有一次性沙箱中运行原版 Cursor Agent CLI。推理和工具执行由原生 Cursor 完成。agent任务需要独立的CURSOR_API_KEY；不会复用兼容模型或操作端其他密钥。自动工具执行必须显式传入allow_unsafe_tools=True。

## 技术栈

固定官方CLI2026.10.19-6bbf2c4、Linux x86_64，原版启动器、内置Node及原生模块保持不变。原包183,733,394字节，控制端实测SHA256为`cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f`，并非上游发布的校验和。460个普通文件共585,886,062字节。[完整清单](upstream.json)、[许可说明](UPSTREAM-NOTICE.md)、[设计](../docs/design/cursor-agent.md)。基础镜像为阿里云generation2，Python3.13；服务端源码固定34e7e011c5569f77b7f605e65313be7498f6cf02。

## 解决的问题

提供可复现安装、标量SDK/HTTP接口，以及有界执行和进程／私有状态清理。此模板是本地CLI运行环境；Cursor Cloud Agents及企业机器调度器不在认证范围内。真实厂商账号下的模型与代码行为，需要独立的真实凭证验收。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./cursor-agent --workflow application --yes
abx run <sandbox-id> agent_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('agent_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/agent_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "2026.10.19-6bbf2c4"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| agent_version | 无 | 验证原文件后执行原生--version，返回固定版本字符串 |
| agent_native_check | 无 | original_native/headless_print/json_output/explicit_force/contained_workspace布尔字段，执行原生--help，无模型调用 |
| agent_setup_check | 无 | mode/installed/pinned_version/api_key_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态，无值或网络 |
| agent | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原生最终响应；明确授权后可读写文件和执行工具 |

prompt为1..32768UTF8字节，非空且无NUL。cwd最长4096UTF8字节、无NUL，必须解析为WORKSPACE内已存在目录；空值选根目录。command_timeout为1..600秒，布尔值拒绝。allow_unsafe_tools必须精确为True。model为空时使用厂商默认选择；非空最多200个ASCII标识字符[A-Za-z0-9_.:/-]且字母数字开头，不声明模型可用性。

成功结果包含stdout字符串、stderr空字符串、exit_code:0、native_completed:true、native_version、archive_sha256、permission_profile:explicit-owned-sandbox-bypass、requested_model。原生JSON必须type=result/subtype=success/is_error=false且最终文本非空。非零、格式错误、未完成、超时或超量均抛错，不返回部分成功。实际模型与代码产物另行验收。

固定原生argv为--print --output-format json --disable-auto-update --disable-project-configs --sandbox disabled --trust --force --workspace <受限项目>，可选--model及原样prompt。该显式模式使用外层自有沙箱隔离，禁用原生嵌套沙箱。参数通过argv传递；不暴露任意参数、认证绕过、操作端其他密钥兜底或替代规划器。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| CURSOR_API_KEY | 空；agent必需 | 厂商凭证，命令模块导入时捕获 |
| WORKSPACE | /home/user/app | 项目根目录，导入时捕获 |
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

原生子进程只获得自身显式厂商密钥及私有HOME/config/data/cache/TMP等最小环境。固定原生参数关闭更新和项目配置加载；不使用操作系统钥匙串或原生持久会话。成功／失败／超时后删除每次私有状态。服务和工具共享OS用户，路径不是其他租户的隔离边界；自动工具仅用于自有一次性沙箱。

每个服务进程最多一个agent操作，重叠返回busy。stdout/stderr各限256KiB；命令1..600秒加最多90秒清理，客户端超时应至少command_timeout+120秒。已知厂商密钥、命令token、私有HOME值脱敏。私有会话或云资源ID不进入公开证据。

## 资源

仅Linux x86_64，2vCPU/4096MB/9000端口，非root用户，WORKSPACE为/home/user/app；构建检查8GiB根盘上限。原包解压585.9MB，压缩183.7MB。无需声明嵌套Docker、KVM、GPU或桌面能力。模型任务需要厂商出口与账号；峰值RSS和认证吞吐未测。其他架构／提供商、交互／恢复／MCP／插件／委派／云Agent功能未认证。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q cursor-agent/test_commands.py cursor-agent/test_controller.py cursor-agent/test_install.py
python scripts/check_template.py cursor-agent --strict
python scripts/check_docs.py
```

保留原文件摘要与许可、显式权限、私有状态和进程清理。变更的COPY／辅助源码必须先发布，再准备不可变steps；保持15000字节wire和通用300MiB原包限制。完整外部控制器必须执行真实原版HTTP及SDK无效密钥拒绝，安装／版本回执不能代替。有真实厂商凭证时，显式选择自有远程代码控制器：既有源码修复、原始3项测试字节不变、报告／精确随机标记、原始3项加独立4项断言、返回后新ACK。生成代码不在操作端运行。

## 贡献

阅读[贡献指南](../CONTRIBUTING.md)、[项目标准](../docs/project-standards.md)、[文档标准](../docs/documentation-standards.md)及[模板规范](../docs/template-spec.md)。独立模板、类型契约、双语文档、设计、目录、工程记录与当前源证据一起提交；完成最新CI／review后正常合并。

## 问题反馈

[Issue63](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/63)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。上游行为反馈给Cursor，不附凭证或私有会话。

## 许可证

自编写模板代码Apache-2.0；Anysphere原版软件和第三方许可保持原条款与声明，见[说明](UPSTREAM-NOTICE.md)。本Git仓库不分发上游二进制／源码，也不声称厂商背书。
