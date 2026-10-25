# muse

## 做什么

在一个自建Express计算机中运行官方原版Meta Muse Code1.4.11-R6667.1无头agent、原版miniswe工具与原生运行记录。编码显式选择兼容Responses模型。自编本地代理补充所选模型目录，将上游密钥留在父进程，原样转发Responses请求与流；使用原版二进制。[官方文档](https://dev.meta.ai/docs/muse-code)。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

阿里云generation2 basev0.0.49/Linuxx64/Python3.13；root所有的原版ELF384809176字节及官方SHA256，Python标准库代理/进程控制，已发布服务端包，无新增Python/Node依赖。[Dockerfile](Dockerfile)、[来源](upstream.json)、[上游声明](UPSTREAM-NOTICE.md)、[设计](../docs/design/muse.md)。模板源码许可证不重新授权原版上游文件。可将任务自有gzip缓存重新校验后流式上传私有OSS，避免在操作端另占384.8MB原始文件；目标端仍检查未修改的原版字节。

## 解决的问题

通过SDK/HTTP命名命令提供原版Muse文件与工具执行，采用逐次私有配置及所有权清理。普通兼容网关没有原版CLI必需的`/muse-code/models`；本地代理补充目录，随后将原版`/responses`字节转发到明确配置的端点，不转换模型/工具协议，不回退到厂商默认账号或订阅。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./muse --yes
abx run <sandbox-id> muse_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('muse_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/muse_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "Muse Code 1.4.11 (1.4.11-R6667.1)"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果与副作用 |
| --- | --- | --- |
| muse_version | 无 | 校验原版ELF后返回`Muse Code 1.4.11 (1.4.11-R6667.1)`，不调用模型 |
| muse_native_check | 无 | 原版无头帮助对应`{original_native:true,headless_json:true,anonymous_api_key_stdin:true,no_session_log:true}`，不调用模型 |
| muse_setup_check | 无 | mode为`original-native-muse-explicit-responses`；native_present/model_key_set/model_base_set/model_set存在性标志；model_account_verified:false/provider_default_fallback:false/catalog_relay:true；不返回配置值、不访问网络 |
| muse | prompt：必填非空字符串1..32768UTF8字节、无NUL；cwd：可选字符串、默认空、最长4096字节、解析后必须是WORKSPACE内已有目录；command_timeout：整数1..600秒、默认300、拒绝布尔值 | 原版最终stdout、native_completed、真实model_calls/native_tool_results、exit_code0、原版二进制/版本/模型/协议及完成的relay_calls计数；原版工具可修改调用方项目，不返回原始轨迹 |

固定原版argv：`exec --json --api-key-stdin --provider meta --model <configured> --preset miniswe --reasoning-effort minimal --max-model-steps16 --no-session-log --disable-reminders --no-foreign-personal-context --disable-web-tools --yolo --workspace <contained-project>`。逐次私有配置包含schema_version1、endpoint_transport base_url/auth bearer和agents.execution_capacity1。原版miniswe没有可用subagent_spawn，不选择委派模型/工具树。显式信任后可能加载调用方项目指令。

完成判定要求原版模型/usage/终态记录精确关联，完成模型调用数为正，无失败/取消/子调用，最终文本非空。编码验收还要求原版工具结果为正和独立产物/测试。代理最多32个模型请求，每请求2MiB、每响应4MiB，原版最多16模型步；原生stdout/stderr各256KiB。已发代理请求须排空后才判完成。自建关闭/进程清理最多额外50秒，SDK timeout建议至少command_timeout+80。并发模型调用返回busy。

## 配置

| 变量 | 默认与要求 | 含义 |
| --- | --- | --- |
| MUSE_MODEL_API_KEY | 空；编码必需 | 明确选择的兼容端点密钥，仅留在父代理中 |
| MUSE_MODEL_BASE_URL | 空；编码必需 | 显式HTTPS Responses基址，最长2048字符，无userinfo/query/fragment；自编fixture仅可用字面loopback HTTP |
| MUSE_MODEL | 空；编码必需 | 实际上游模型标识，1..200个允许字符 |
| WORKSPACE | `/home/user/app` | 调用方已有项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

commands.py导入时捕获配置；存在标志不证明账号有效。key最长8192且无控制字符。原生进程仅通过匿名stdin取得逐次随机本地代理token。父代理只向固定授权Responses端点使用上游密钥，拒绝重定向及错误路由/token/model，不留轨迹。原版工具采用最小环境及私有HOME/缓存/配置，调用方项目产物保留。同一用户仍有OS访问权限，cwd检查和环境过滤不构成额外租户边界；`--yolo`选择自建外层沙箱作为执行边界。

## 资源

声明2vCPU/2048MB/Linuxx64、9000端口、8GiB镜像rootfs预算，无KVM/Docker/GPU/额外权限。原版下载384.8MB；模型需授权出口。下方有界镜像/steps/完整HTTP/模型流程实际通过，未测量峰值内存。其他提供方、交互/保留会话恢复、voice/本地权重、MCP/plugin服务与Meta托管订阅不在本流程内。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q muse/test_commands.py muse/test_relay.py muse/test_terminal.py
python scripts/check_template.py muse --strict
python scripts/check_docs.py
python scripts/run_steps_e2e.py muse --asset-transport oss
```

本地代理/解析器fixture仅用固定不可执行回复；原版及生成代码验收只在全新且明确自建的云端目标运行。保留原版二进制与声明、精确边界、重定向拒绝、匿名输入及进程/代理清理。正式编码检查须有源码修改、原测试字节、新报告/精确nonce、原3项及4项新增用例/返回后新ACK，独立确认自建资源不存在。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.md)、[文档规范](../docs/documentation-standards.md)、[模板规范](../docs/template-spec.md)。同一变更包含本仓库笔记/实际证据与双语README；真实必需检查和review通过后才合并。

## 问题反馈

[模板Issue71](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/71)跟踪交付。[模板问题](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)分别归属对应仓库；原版Muse行为向其上游支持反馈。不附凭据或原始私有轨迹。

## 许可证

自编模板代码与文档使用[Apache-2.0](../LICENSE)。Meta原版文件条款与声明单列，见[来源说明](UPSTREAM-NOTICE.md)；不据此声明上游开源授权、厂商背书或已具备托管模型账号。
