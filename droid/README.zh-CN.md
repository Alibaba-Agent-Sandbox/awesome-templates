# Factory Droid

## 做什么

模板1.2.0 新增 `droid_byok`：真实固定版本 CLI 使用显式兼容模型接口，无需 Factory 账号；原有 `droid` 账户模式保留。两种模式均使用每次调用独立状态及有界自有进程清理。当前1.2的原生 SDK/极速版/BYOK 验收已通过，详见下节；旧回执保留历史范围。

在现有项目上无头运行 Factory Droid 0.241.1。具名命令提供有执行时限的编码调用、版本查询与不调用模型的安装检查。

## 技术栈

官方 npm `@factory/cli@0.241.1` 与 `@factory/cli-linux-x64@0.241.1`、完整 npm integrity [锁文件](package-lock.json)、未修改原生二进制 SHA256 `1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1`、阿里云 FC 基础镜像、Python3.13及固定 servere2cb27e。禁用安装 hooks，直接执行固定原生路径，每次原生命令和构建均检查 SHA256。见[来源](upstream.json)、[上游声明](UPSTREAM-NOTICE.md)、[Dockerfile](Dockerfile)。上游标记为私有 `UNLICENSED`，仓库元数据不证明源码公开。非 root `user`、generation2、9000端口。

## 解决的问题

自动化可通过 Agent Sandbox 上传项目，让 Droid 修改源文件，再读取产物并独立运行测试。旧 Factory 模式缺少账户凭据会在启动前拒绝登录；BYOK 使用独立的兼容模型配置。`WORKSPACE` 指定项目根目录；成功输出与错误消息均对已配置秘密值脱敏。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./droid --yes
abx run <sandbox-id> droid_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('droid_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/droid_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.241.1"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回值 / 上游调用 |
| --- | --- | --- |
| `droid_byok` | 必填 `prompt: str`，1–32768个 UTF-8 字节、非空、无 NUL；`cwd: str=""`，最多4096字节，工作区内已存在且解析后不越界；`command_timeout: int=300`，1–600秒，拒绝 bool | 对象：原生 `stdout`、`stderr`、`exit_code`、`native_version`。固定 `droid exec --model custom:<configured-model> --output-format json --auto low --disable-builtin-skills --settings <private-settings> --only-tools Read,Edit,Create,Grep,Glob,LS`，任务经匿名 stdin。修改所选项目，所有路径清理私有状态。 |
| `droid_byok_setup_check` | 无 | 模型/base/key 存在布尔值、`mode: openai-compatible-byok`、`factory_account_required: false`；无模型请求及秘密值。 |
| `droid_version` | 无 | `droid --version` 的版本字符串；不需要模型密钥。 |
| `droid_setup_check` | 无 | 对象：`installed`（布尔），`package`、`version`、`expected_version`（字符串），`api_key_set`、`workspace_exists`、`auto_update_enabled`（布尔）。不调用模型、不返回密钥值。 |
| `droid` | `prompt`：必填非空字符串；`auto`：字符串，默认 `low`，可为 `""`、`low`、`medium`、`high`；`cwd`：字符串，默认 `""`，必须为 `WORKSPACE` 内现有目录；`command_timeout`：整数，默认 300，范围 1–600 秒 | `droid exec [--auto LEVEL] -- PROMPT` 的缓冲 stdout 字符串。非零退出或超时抛出脱敏执行错误。 |

相对 `cwd` 从 `WORKSPACE` 解析；绝对路径在解析符号链接后也必须位于根目录内。`auto=""` 不传该选项，使用上游只读模式；`low` 允许项目编辑，`medium` 还允许开发命令，`high` 允许风险更高的操作。模板不传 `--skip-permissions-unsafe`。**兼容性：** 1.1.0 将 `/app` 改为 `/home/user/app`，编码命令默认显式传 `--auto low`；需要原先只读行为时传 `auto=""`。

1.2.0 增加 BYOK，不改变旧参数；固定原生路径并检查 SHA256，每条输出流上限256KiB。两种模式均排除操作端云/GitHub 凭据，使用私有 HOME 及身份固定的进程组/nonce/pidfd，在成功、失败、溢出和超时清理。BYOK 固定 low 权限，不启用不安全跳过权限选项。原生进程从私有临时 Git 根目录启动，通过匿名任务上下文传入所选项目的绝对路径，避免项目 `.factory` 配置影响模型路由；不会自动加载目标项目的原生配置。通过固定 `--settings` 传入私有运行配置，仅启用原生 Read/Edit/Create/Grep/Glob/LS 文件工具，不启用 Execute、子智能体或 MCP 工具。项目文件归调用者，cwd 选择不是操作系统隔离边界。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 默认值 | 作用 |
| --- | --- | --- |
| `DROID_MODEL_API_KEY` | 空；BYOK 必填 | 最多8192字符，禁 CR/LF/NUL，仅进入私有原生环境。 |
| `DROID_MODEL_BASE_URL` | 空；BYOK 必填 | 显式 HTTPS 兼容接口，最多2048字符，无 userinfo/query/fragment；仅本地字面 HTTP 用于合成测试。 |
| `DROID_MODEL` | 空；BYOK 必填 | 显式1–200字符模型标识。 |
| `FACTORY_API_KEY` | 空 | 创建时注入的 Factory 账户 API 密钥；仅 `droid` 需要。 |
| `ABX_SERVER_TOKEN` | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `WORKSPACE` | `/home/user/app` | 现有项目根目录；显式配置无效目录会报错。 |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | 子进程强制禁用自动更新，保持固定版本。 |

Factory 凭据在 [Factory API 密钥设置](https://app.factory.ai/settings/api-keys)获取。DashScope 或 OpenAI 密钥不能替代 `FACTORY_API_KEY`。`droid_byok` 使用私有原生 `customModels` 配置，provider 为 `generic-chat-completion-api`，显式模型/base 及 `apiKey: "${ABX_DROID_MODEL_KEY}"`。真实密钥不写入设置或 argv，不注入 Factory 密钥、交互登录或替代二进制。输出脱敏密钥/base 并删除私有状态。[官方 BYOK 文档](https://docs.factory.com/model-independence/byok)；固定0.241.1 已通过仅合成固定响应探测，该探测不是实际模型验收。上游行为见 [Droid Exec](https://docs.factory.com/droid-exec/overview)，具体选项以固定版本的真实帮助为准。脱敏涵盖 stdout、错误中的原始与 JSON 转义的已配置秘密值；Agent 写出的项目文件仍需遵守正常的秘密管理要求。cwd 约束用于选择项目，不是操作系统安全隔离边界。

## 资源

默认 2 vCPU、2048 MB 内存、9000 端口。BYOK 需要访问配置的模型服务，旧 Factory 模式需要其外部网络。平台启动 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，就绪探针为 `agent-sandbox-server healthcheck --port 9000`。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

## 二次开发

保留阿里云基础镜像、精确 CLI/server 版本和非 root 用户。通过 `@command` 扩展 [commands.py](commands.py)，直接传 argv，保留密钥检查、脱敏和超时清理。使用 BuildKit 构建，部署可注入 server wheel。运行：

```bash
python3 -m pytest -q droid/test_commands.py droid/test_e2e_protocol.py droid/test_byok.py droid/test_model_controller.py
python3 scripts/check_template.py droid
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py droid
```

源码本地执行明确跳过缺失的原生版本，不能据此认证提供商。L1 实际构建 Dockerfile 并检查原生 SHA/版本；L2 要求真实 SDK 创建、标准步骤、完整 HTTP 及独立所属清理。L3 设置 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1`，在新建自有云服务配置 BYOK，执行 [e2e_test.py](e2e_test.py)：原生成功 JSON、正数 turns、精确新鲜最终 nonce、修改已有源码、生成产物、原测试字节不变、独立完整原测试和隐藏用例、返回后新鲜 ACK 及项目不存在。生成代码不在操作端运行。旧 Factory 控制器保留于 [factory_e2e.py](factory_e2e.py)，需真实 Factory 密钥，不声明该模式当前模型已通过。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py droid`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计](../docs/design/droid.md)。同步[英文 README](README.md)，PR 包含回归、工程记录与真实验证证据。必要验收通过前保持 experimental。

## 问题反馈

继续使用 [Droid issue #19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19)。模板问题提交至 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/server 问题至 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题至 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。附版本、提供方、generation 和脱敏复现；不要附密钥或原始私有日志。

## 许可证

模板代码使用 [Apache-2.0](../LICENSE)。Factory Droid 独立按上游条款分发；安装 CLI 不改变其许可证。

### 2026-10-20完整 step 检查点：模板1.1.1

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T155022Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，9 PASS/0 FAIL/0 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。

新运行时保留私有软件[上游声明](UPSTREAM-NOTICE.md)。
