# grok

## 做什么

运行真正的 xAI 官方 `@xai-official/grok@1.0.62` 无头编码 CLI。Rust 原生程序经 --prompt-file /dev/stdin 读取匿名 stdin，使用真实工具修改项目，返回缓冲 JSON 与实际退出码。本模板是官方 Grok Build；兼容模型通过不代表 xAI 托管模型或订阅已验证。

[Official xAI source snapshot](https://github.com/xai-org/grok-build/tree/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8), [native custom models](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/11-custom-models.md), [headless protocol](https://github.com/xai-org/grok-build/blob/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-pager/docs/user-guide/14-headless-mode.md).

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

Alibaba generation2 basev0.0.49／Python3.13、SHA256 固定 Node24.16.0、npm integrity 锁定 Grok Build1.0.62及原始 Linuxx64/Rust 二进制。每次调用前校验二进制 SHA2562a46d9e4d7ebd7a9cff7f95716714b19dad5f21dd2a497822400b1fb128969aa。server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a，以 user 运行，应用目录／工作区、端口9000。[Dockerfile](Dockerfile)、[依赖锁](package-lock.json)、[设计](../docs/design/grok.md)。

## 解决的问题

通过命名命令使用真实 Grok Build 编码能力，无需交互登录、共享开发者配置或宿主 CLI。已检查真实包名、帮助和源码快照，不假设参数，不替换原生 agent。模型／端点明确；验收中的生成代码只在新建自有云沙箱执行。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./grok --yes
abx run <sandbox-id> grok_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('grok_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/grok_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"native_version": "1.0.62"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| grok_version | 无 | 实际固定原生版本 `{"native_version":"1.0.62"}`；不调用模型／登录 |
| grok_setup_check | 无 | mode=openai-compatible-byok、base_url_set／api_key_set／model_set 布尔值、xai_account_required:false；不联网／返回秘密 |
| grok | prompt：必填非空字符串，1..32768 UTF-8字节且无 NUL；cwd：可选字符串，默认空，最多4096字节，解析后必须为 WORKSPACE 内现存目录；command_timeout：整数1..600秒，默认300 | `{stdout:string,stderr:string,exit_code:int,native_version:"1.0.62"}`；原生工具执行及工作区文件修改 |

固定参数为 --output-format json、--always-approve、--no-plan、--no-subagents、--disable-web-search、--sandbox off、--model abx-approved、--max-turns20、--prompt-file /dev/stdin。工具白名单为 read_file/search_replace/grep/list_dir/run_terminal_cmd，禁用 Agent。原生 sandbox off 保留工具在外层沙箱内的 OS 权限；cwd 仅为参数边界。仅用于受信任调用者与全新自有一次性沙箱，无回滚承诺。提示和密钥值均不进入 argv。

stdout／stderr 各限256KiB；成功／失败／超时／溢出均清理自有进程组、pidfd 和唯一归属标记后代。调用串行，并发报 busy，不使用原 HOME。返回前脱敏显式模型密钥／端点及其 JSON 转义形式。只保留调用者请求的工作区产物，原生 HOME／配置／缓存／会话／team 状态均在调用后删除。


## 配置

| 名称 | 必需／默认 | 含义 |
| --- | --- | --- |
| GROK_MODEL_API_KEY | 模型必需，空 | 授权兼容端点密钥，仅作为原生 ABX_GROK_MODEL_KEY 传递 |
| GROK_MODEL_BASE_URL | 模型必需，空 | 显式 HTTPS API base；仅固定本地地址可用 HTTP；无用户信息／query／fragment；最多2048字符 |
| GROK_MODEL | 模型必需，空 | 实际模型标识，最多200个允许字符 |
| WORKSPACE | `/home/user/workspace` | 已存在工作区根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在 commands.py 加载时捕获。私有0600 config.toml 仅含显式 model/base 与 env_key="ABX_GROK_MODEL_KEY"，不保存密钥值，固定 chat_completions 后端。每次调用使用并删除私有 GROK_HOME/HOME/cache/session；关闭更新、leader、遥测/trace、记忆及后台 workflow。原生 shell_environment_policy 继承 core 并排除秘密变量；不转发调用者云/GitHub/厂商账号凭据。

## 资源

仅 Linuxx64，2vCPU、4096MB、9000端口、Express约10GiB rootfs；镜像限制8GiB。CLI 不需嵌套 Docker／KVM／GPU；真实编码需要兼容工具调用的模型和授权网络。未声明 Grok Build 托管／扩展／其他提供方验收或模型任务内存估计。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q grok/test_commands.py grok/test_model_controller.py
python scripts/check_template.py grok --strict
python scripts/check_docs.py
```

官方二进制实际报告 grok1.0.62 (1474f9cbdd91)，并核对 SHA256。公开源码快照2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 用于核对无头/自定义模型协议，不声称为二进制构建 commit。控制器通过真实 Python SDK 调用模型命令，再独立核对完整原始测试字节、源码修改、报告与随机产物，以及返回后的原始/隐藏用例和新 ACK。JSON 必须含 end_turn、正整数 num_turns 和真实 session/request ID，不能仅凭 marker 通过。生成源码仅在新建自有云沙箱执行。

## 贡献

阅读 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。维护版本、固定来源、双语和历史不可变证据。

## 问题反馈

[模板 Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 和 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不发布凭据／私有日志。

## 许可证

包装器与官方 Grok Build 均为 Apache-2.0。[仓库许可](../LICENSE)、[上游许可](UPSTREAM-LICENSE.md)、[官方二进制第三方声明](THIRD_PARTY_NOTICES.md)。保留原始依赖声明，不提供托管账号或商标权利。
