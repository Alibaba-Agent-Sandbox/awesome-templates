# claude-code

## 做什么

运行官方未修改的 Claude Code2.0.76无交互规划及 Read/Edit/Write/Bash 工具。原 `claude` 保留面向 Anthropic 的接口；新增 `claude_byok` 显式使用本项目编写的 Messages 到 OpenAI Chat 文本和工具协议适配器。兼容模型模式属于实验功能，[Anthropic 不支持将其用于非 Claude 模型](https://code.claude.com/docs/en/llm-gateway)，不代表获得 Claude 模型、订阅或官方背书。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

阿里云 generation2基础镜像v0.0.49/Linuxx64/Python3.13/Node20；官方npm包2.0.76以锁文件 SHA512 校验，[upstream.json](upstream.json) 固定原始 cli.js SHA256。`npm ci --omit=optional --ignore-scripts` 排除可选图像编解码器和安装钩子，原 CLI、内置工具代码和许可声明保持原样。已发布服务端包；适配器与进程管理仅依赖标准库。见 [Dockerfile](Dockerfile)、[上游声明](UPSTREAM-NOTICE.md)、[设计](../docs/design/claude-code.md)。

## 解决的问题

通过 SDK/HTTP 调用原始工具。在授权网关只提供 Chat 时，新增显式选择的文本工具兼容模式。适配器转换消息协议、保留原始工具名称、参数和结果，工具执行仍由原始 CLI 完成；不会实现替代规划器或将密钥发往默认厂商。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./claude-code --yes
abx run <sandbox-id> claude_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('claude_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/claude_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "2.0.76 (Claude Code)"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果与副作用 |
| --- | --- | --- |
| claude_version | 无 | 原 CLI `2.0.76 (Claude Code)`；无模型调用 |
| claude_native_check | 无 | 原 cli.js 哈希与帮助参数：original_native/isolated_settings/no_session_persistence/strict_mcp 布尔值 |
| claude_setup_check | 无 | mode及model_key_set/model_base_set/model_set存在标志、vendor_account_verified:false/provider_default_fallback:false/requires_unsafe_optin:true；不返回值、不发网络请求 |
| claude_byok | prompt必需字符串，非空、1..32768UTF8字节、无NUL；cwd默认空字符串、最多4096字节、解析后位于WORKSPACE内的已有目录；command_timeout整数1..600秒，默认300，拒绝布尔值；allow_unsafe_tools布尔默认False，需显式True才能使用该可丢弃沙箱权限模式 | stdout/exit_code0/native_completed/native_version/cli_sha256/model/permission_profile/protocol/model_calls/native_tool_results/relay_calls；原始工具修改项目，不返回完整轨迹 |
| claude | prompt必需非空字符串；model字符串默认sonnet；cwd默认空字符串、已有且位于工作区内；allowed_tools默认Read,Edit,Write；resume默认空字符串；command_timeout整数默认300、范围1..900秒 | 旧接口将原生JSON编码为字符串并脱敏环境密钥；保留原Anthropic凭据和设置行为，新增隔离模式的保证不覆盖旧接口 |

新增BYOK必须显式allow_unsafe_tools=True，默认False或缺失会在模型调用前失败。以自有可丢弃外层沙箱作为执行边界，并为仅四种可见工具显式选择原CLI权限旁路；旧claude仍为dontAsk。仍要求原生成功、失败响应为零、独立产物和清理，不预设先前断流的根因。

新增固定参数：`-p --model <selected> --output-format json --dangerously-skip-permissions --tools Read,Edit,Write,Bash --allowedTools Read,Edit,Write,Bash --settings <owned> --setting-sources '' --no-session-persistence --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands --no-chrome --max-turns16`。禁用钩子，思考token为0；不提供Task、子Agent、MCP、插件或项目/本地设置加载。项目指令仍是不可信输入，仅在自有可丢弃目标运行。

转换文本及原始工具schema和结果；拒绝图像、thinking、不支持的内容或工具、截断回复、错误模型、token、路径及重定向。上游Chat缓冲后输出原生Messages SSE。最多32请求，每请求2MiB、响应4MiB、原生16轮、stdout/stderr各256KiB。成功要求原CLI成功结果和正数传输完成次数；编码验收另要求原生工具结果、独立下载产物及测试。返回前回收自有进程、私有状态、已发RPC；清理最多额外210秒，客户端超时至少command_timeout+240；并发BYOK返回忙。

## 配置

| 名称 | 默认与要求 | 含义 |
| --- | --- | --- |
| CLAUDE_MODEL_API_KEY | 空，BYOK必需 | 明确授权的兼容上游密钥，仅父适配器持有 |
| CLAUDE_MODEL_BASE_URL | 空，BYOK必需 | HTTPS Chat基址，无userinfo/query/fragment、最多2048字符；固定测试允许字面环回HTTP |
| CLAUDE_MODEL | 空，BYOK必需 | 选定模型，1..200允许的标识字符 |
| ANTHROPIC_API_KEY | 空，仅旧模式 | 旧Anthropic兼容配置；新增入口不会隐式复用 |
| WORKSPACE | /home/user/app | 已有项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

新增配置在模块导入时捕获。密钥最多8192字符且无控制字符；不默认回退厂商、模型或密钥。原CLI和工具仅获得临时本地适配器token、最小环境以及私有HOME/config/cache；真实密钥仅父进程持有并只发往明确指定的Chat来源。结果与错误不含凭据、私有地址或完整轨迹。同用户OS访问仍存在；环境过滤和cwd约束不构成另一个租户边界。旧接口resume与设置行为保留，不纳入BYOK隔离承诺。

## 资源

声明2vCPU2048MB、Linuxx64、9000端口、8GiB镜像rootfs预算；无需KVM/Docker/GPU/显示器。官方npm压缩包26.4MB、展开70.9MB，基础镜像已含Node20。需授权模型出网，排除可选图像编解码器。未测峰值内存。完整Claude服务、OAuth/订阅、交互/恢复会话、图像/thinking/MCP/插件/委派未验证。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q claude-code/test_byok.py claude-code/test_adapter.py
python scripts/check_template.py claude-code --strict
python scripts/check_docs.py
python scripts/run_steps_e2e.py claude-code
```

保留原包与声明、锁文件与完整性/哈希、显式授权来源、工具环境无真实密钥、拒绝不支持内容、自有后代进程/监听器/私有目录清理。本地仅使用不执行代码的固定协议回复。原生/模型生成代码仅在新建自有云目标运行；原测试字节不变，并独立核对产物和返回后的隐藏测试。

## 贡献

遵循 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[文档规范](../docs/documentation-standards.zh-CN.md) 和[模板规范](../docs/template-spec.zh-CN.md)。包含双语文档、所属仓库记录、当前提交review及检查。

## 问题反馈

[Issue15](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/15)、[模板缺陷](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[Python SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原始上游问题遵循其支持渠道。不得附加密钥或私有轨迹。

## 许可证

本项目模板和适配器：[Apache-2.0](../LICENSE)。原Anthropic包保留全部权利并遵循[上游条款和声明](UPSTREAM-NOTICE.md)，不重新授权或暗示官方背书。

模板1.3.1仅对固定原版的异步Bash文件路径分析请求，且上游完整响应后对端断连时，单独记录cancelled_auxiliary_responses（无工具、单条用户命令／输出、固定系统文本SHA256匹配）。原生CLI显式忽略这种请求取消。主任务或未知请求、上游超时／错误及其他失败仍拒绝完成；completed_required_responses必须大于零。取消的辅助请求不计为已送达，也不计为成功模型调用。独立代码／产物／返回后测试仍必需；新版本须重新验收。
