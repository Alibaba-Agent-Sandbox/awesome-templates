# devin

[English](README.md)。

## 做什么

在自有一次性沙箱中，通过类型明确且有界的命名命令调用Cognition原版Devin CLI3000.11.92。推理与工具由原版负责；没有替代规划器或兼容模型兜底。自动工具必须显式allow_unsafe_tools=True。

## 技术栈

Alibaba generation2 Linuxx86_64基础镜像、Python3.13服务、[固定官方原包](https://static.devin.ai/cli/3000.11.92/devin-3000.11.92-x86_64-unknown-linux.tar.gz)。原版234文件／200878983字节，压缩67245544字节；SHA256为2d829139682e038cf122510f1170eee3d7060bcc7ebf92445cbc5d28c9fbcfa0，来自2026-10-21观察的官方平台manifest。[逐文件清单](upstream.json)、[server SDK固定来源](server-sdk.commit)。构建校验原包和文件，不执行原版；运行时检查root持有的原文件身份。厂商程序／文档／man手册保留独立条款。

## 解决的问题

提供可复现安装、明确权限、每次私有状态、输入输出／期限约束和自有进程清理。上游允许在用户自己的机器间复制原credentials.toml，因此无需把首次交互登录放入API流程；这条账号接入已实现，但没有账号时不宣称认证成功。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./devin --workflow application --yes
abx run <sandbox-id> devin_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('devin_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/devin_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "devin 3000.11.92 (7f4e64980e22)"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| devin_version | 无 | 原文件身份校验及真实--version字符串 |
| devin_native_check | 无 | 原版--help；original_native/headless_print/private_config/explicit_permission/workspace_trust_control布尔字段 |
| devin_setup_check | 无 | mode/installed/pinned_version/credentials_file_set/requires_unsafe_optin/vendor_authentication_verified/compatible_model_fallback；仅状态 |
| devin | prompt必填字符串；cwd字符串默认空；command_timeout整数300；allow_unsafe_tools布尔False；model字符串默认空 | 缓冲原版最终stdout；明确授权后可执行文件／工具动作 |

prompt为1..32768UTF8字节、非空且无NUL；cwd最长4096UTF8字节、无NUL，必须解析为WORKSPACE内已有目录，空选择根目录。command_timeout整数1..600秒，布尔拒绝；allow_unsafe_tools必须精确True。model为空使用厂商默认，非空最多200ASCII字符[A-Za-z0-9_.:/-]、字母数字开头，不声明可用模型。cwd及祖先出现原生.devin目录／符号链接时原样拒绝，以保留固定私有配置。

固定argv为--config <私有JSON> --permission-mode dangerous --respect-workspace-trust false，可选--model，再加--print及原样prompt；cwd为受限项目。配置关闭更新／subagents／其他agent配置导入，私有HOME/config/data/cache/TMP隔离用户状态。原生dangerous模式使用外层自有沙箱，不启用嵌套sandbox、认证绕过或cloud模式。

原版退出0且stdout非空才返回stdout、stderr空、exit_code0、native_completed:true、native_version、archive_sha256、permission_profile:explicit-owned-sandbox-bypass、requested_model。此固定原版print是纯文本，native_completed只表示进程完成；真实代码／产物／模型结果仍需独立远程控制器验收。非零／空输出／超时／超量均报错，不返回部分成功。无任意额外argv或shell拼接。

## 配置

| 变量 | 默认／要求 | 含义 |
| --- | --- | --- |
| DEVIN_CREDENTIALS_FILE | 空；诊断／错误路径可缺，账号任务需要 | 包装层变量，模块导入捕获路径；绝对路径、WORKSPACE外、root或当前UID持有的普通非符号链接、无组／其他权限、1..65536字节合法UTF8TOML |
| WORKSPACE | /home/user/app | 导入捕获的项目根目录 |
| ABX_SERVER_TOKEN | 必填；清单值为空 | 启动前导出独立应用令牌 |

缺文件时让原版print明确返回登录拒绝；不执行交互登录、不虚构DEVIN_API_KEY、不借用其他模型／云密钥。子进程只收到最小私有状态环境，不继承操作端密钥或源凭证路径。返回stdout脱敏已知TOML字符串、服务Bearer／私有HOME／源文件路径；原生错误隐藏原输出。同一服务最多一个操作，重叠返回busy。

stdout和stderr各限256KiB；命令1..600秒，加最多90秒自有后代清理；客户端超时至少command_timeout+120秒。同OS用户／工具权限不是多租户文件隔离边界，只用于自有一次性沙箱及明确授权任务。

## 资源

仅Linuxx86_64，非root用户，2vCPU／4096MB／9000端口，构建限制根盘8GiB。原包展开200.9MB／压缩67.3MB。不声明KVM／Docker／GPU／桌面要求。账号任务需要厂商出口／授权账号／CLI角色。峰值RSS、认证吞吐、其他架构／提供商、交互／恢复／cloud／ACP／MCP／插件／委派均未认证。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q devin/test_commands.py devin/test_controller.py devin/test_install.py
python scripts/check_template.py devin --strict
python scripts/check_docs.py
```

保留原字节／条款、官方固定哈希、显式权限、凭证输入隔离与清理。先发布COPY／helper源码再生成不可变steps，通用300MiB／15000线传限制不变。完整外部控制器必须真实执行原版无账号HTTP／SDK拒绝。取得真实账号后只在显式自有远程目标运行编码控制器：修改已有源码、原3项测试不变、报告／精确nonce、3原始和4held-out／返回后新ACK。生成代码不在操作端执行。

## 贡献

遵守[CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[文档规范](../docs/documentation-standards.zh-CN.md)及[模板规范](../docs/template-spec.zh-CN.md)。独立源码、类型契约、双语文档／设计／目录和索引证据保持一致，最终head检查／review及普通固定SHA合并必需。

## 问题反馈

[Issue72](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/72)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。厂商认证／模型行为属于Cognition；不附凭证或私有原始日志。

## 许可证

本包装层Apache-2.0；Cognition原程序／文档／手册保留独立条款，见[声明](UPSTREAM-NOTICE.md)。Git不提交或重许可原版二进制／源码，不宣称厂商背书或独立再分发授权。
