# cline

## 做什么

运行真实官方 `cline@3.0.73`，采用有界无头 JSON/yolo 模式，经匿名 stdin 读取提示，使用原生工具修改工作区并返回缓冲 NDJSON 与实际退出码。显式选择 OpenAI 兼容提供方，不选择 Cline 托管账号。这里只验证 CLI 产品，不声称 VS Code 扩展或桌面 UI。

## 技术栈

Alibaba generation2 basev0.0.49／Python3.13、SHA256 固定 Node24.16.0、npm integrity 锁定 Cline3.0.73及原始 Linuxx64/Bun 二进制。每次调用前校验二进制 SHA2561ff8841d17d4d83763134c193d414e4f7fcf2ef56af759e5ebbe96727fc2c8f7。server 固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a，以 user 运行，应用目录／工作区、端口9000。[Dockerfile](Dockerfile)、[依赖锁](package-lock.json)、[设计](../docs/design/cline.md)。

## 解决的问题

通过命名命令使用真实 Cline 编码能力，无需交互登录、共享开发者配置或宿主 CLI。已检查真实包名、帮助和源码 tag，不假设参数，不替换原生 agent。模型／端点明确；验收中的生成代码只在新建自有云沙箱执行。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./cline --workflow application --yes
abx run <sandbox-id> cline_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('cline_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/cline_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"native_version": "3.0.73"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 结果／副作用 |
| --- | --- | --- |
| cline_version | 无 | 实际固定原生版本 `{"native_version":"3.0.73"}`；不调用模型／登录 |
| cline_setup_check | 无 | mode=openai-compatible-byok、base_url_set／api_key_set／model_set 布尔值、cline_account_required:false；不联网／返回秘密 |
| cline | prompt：必填非空字符串，1..32768 UTF-8字节且无 NUL；cwd：可选字符串，默认空，最多4096字节，解析后必须为 WORKSPACE 内现存目录；command_timeout：整数1..600秒，默认300 | `{stdout:string,stderr:string,exit_code:int,native_version:"3.0.73"}`；原生工具执行及工作区文件修改 |

固定 argv 为 `--json --yolo --provider openai-compatible --model <configured> --cwd <resolved> --compaction off --retries 2 --timeout <seconds>`，并带本次私有 --config／--data-dir。提示经匿名 stdin 传入，不作为参数／shell。Yolo 为原生无监督 act／工具自动批准模式，上游该模式默认禁用 spawn／team。它不只读，不是文件系统／租户安全边界；只用于受信任调用者和全新自有、无重要文件／其他凭据的沙箱。cwd 参数边界不移除原生工具的 OS 权限，文件可能在失败前已修改，不承诺回滚。

stdout／stderr 各限256KiB；成功／失败／超时／溢出均清理自有进程组、pidfd 和唯一归属标记后代。调用串行，并发报 busy，不使用原 HOME。返回前脱敏显式模型密钥／端点及其 JSON 转义形式。只保留调用者请求的工作区产物，原生 HOME／配置／缓存／会话／team 状态均在调用后删除。

原生3.0.73在读取管道前检查 JSON 模式。模板使用固定、无秘密的占位句通过该前置条件；真实任务仍仅经匿名 stdin 传入，由上游追加。运行时1.0.1修复真实1.0.0云测失败，用户提示与凭据均不进入 argv。

运行时1.0.2将提供方配置写入原生实际读取的私有 data/settings/providers.json；上游 --data-dir 会在初始化前覆盖 CLINE_PROVIDER_SETTINGS_PATH。独立检查发现1.0.1原生实际配置缺少预期端点后，已停止该任务。必须先使用虚拟密钥验证原生请求确实到达本次自有端点，再注入已批准的真实模型密钥。

## 配置

| 名称 | 必需／默认 | 含义 |
| --- | --- | --- |
| CLINE_MODEL_API_KEY | 模型必需，空 | 授权兼容端点密钥，仅作为原生 OPENAI_API_KEY 传递 |
| CLINE_MODEL_BASE_URL | 模型必需，空 | 显式 HTTPS API base；仅固定本地地址可用 HTTP；无用户信息／query／fragment；最多2048字符 |
| CLINE_MODEL | 模型必需，空 | 实际模型标识，最多200个允许字符 |
| WORKSPACE | `/home/user/workspace` | 已存在工作区根目录 |
| ABX_SERVER_TOKEN | 必填；清单为空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在 commands.py 加载时读取。包装器只向私有0600设置文件写提供方／模型／base元数据，不写模型密钥值；原生密钥按其文档从环境读取。原生状态受私有目录保护并在返回／失败时删除。关闭全局 telemetry／自动更新／运行时文件日志，以及公共／私有模型目录刷新。config／data／team／MCP 路径均每次隔离，不传宿主 GitHub／云密钥、二进制替换配置或 Cline 账号 token，宿主控制端凭据不进入编码进程。

## 资源

仅 Linuxx64，2vCPU、4096MB、9000端口、Express约10GiB rootfs；镜像限制8GiB。CLI 不需嵌套 Docker／KVM／GPU；真实编码需要兼容工具调用的模型和授权网络。未声明 Cline 托管／扩展／其他提供方验收或模型任务内存估计。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q cline/test_commands.py cline/test_model_controller.py
python scripts/check_template.py cline --strict
python scripts/check_docs.py
```

固定上游 cli-v3.0.73／commitc718573538d76310f464541617ab665108a6c999 定义 JSON run_result，包含 completed finishReason／iterations／text。外部控制器使用真实成对 Python SDK ServerClient.commands.run 执行模型命令，再用独立 HTTP files／shell 校验。它要求真实终结事件，先上传已有故障源码、保留原测试字节，下载新报告／随机 marker 产物，再在自有云目标独立重跑完整原始测试与未提供给模型的用例，并要求新执行后 ACK，最后确认自有项目目录不存在。拒绝在宿主回环地址执行生成源码，且须显式自有远程 opt-in；强制真实模型不得静默跳过。本地固定进程／NDJSON／凭据 fixture 只证明验证器边界。[steps 指南](../docs/platform-steps.zh-CN.md)说明精确源码传输和资源恢复。

## 贡献

阅读 [CONTRIBUTING](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。维护版本、固定来源、双语和历史不可变证据。

## 问题反馈

[模板 Issue66](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/66)。[SDK/server](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) 和 [CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues) 使用 `[templates]` 前缀，不发布凭据／私有日志。

## 许可证

包装器和 Cline 均为 Apache-2.0。[仓库许可](../LICENSE)、[固定上游许可](UPSTREAM-LICENSE.md)。第三方运行时／依赖保持原始发行包声明，不暗示托管账号或商标授权。
