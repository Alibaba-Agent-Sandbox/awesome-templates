# opencode

`text` 包含中间步骤的说明；严格最终回复验收从 `stdout` 读取同一会话最后一个以 `stop` 完成的步骤，并继续执行独立代码、产物和会话续接检查。

Agent Sandbox 里的 OpenCode（`sst/opencode`）。镜像安装 npm 包 `opencode-ai@1.19.0`。命名命令调用这个 CLI。主调用是无头的 `opencode run`。`opencode serve` 是端口 4096 上的另一套 HTTP 服务。

## 做什么

`agent-sandbox-server` 监听端口 9000，并注册调用 `opencode` 的命令。`opencode_run` 执行一次非交互的 `opencode run --format json`，返回助手文本、脱敏后的 JSON 事件和会话 id。`opencode_version` 和 `opencode_setup_check` 检查钉死的二进制和 `opencode.json`，不调用模型。

`opencode_serve_start` 在端口 4096 上启动 `opencode serve`，绑定 `0.0.0.0`。该进程是 OpenCode 自己的 HTTP API（`GET /global/health`）。通过 `await sb.network.resolve(4096)` 取得地址，保留返回的网关头及 OpenCode 自身认证。平台的 `start_cmd` 不会启动它。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template deploy` 把 `<region>` 换成 `ALIBABA_CLOUD_REGION_ID` 或 `cn-hangzhou`，把 `<tag>` 换成 `ABX_BASE_IMAGE_TAG` 或 `v0.0.49`。Python 3.13 和 Node.js 20 来自该镜像。
- `opencode-ai@1.19.0`（2026-10-15 的 npm `latest`）。包提供的命令名是 `opencode`。上游是 [sst/opencode](https://github.com/sst/opencode)。
- git 和 ripgrep。
- 工作目录 `/home/user/app`。运行用户 `user`。镜像没有 `CMD` 或 `ENTRYPOINT`。
- Generation 2。`start_cmd` 是 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`。`ready_cmd` 是 `agent-sandbox-server healthcheck --port 9000`。

## 解决的问题

在沙箱里提供钉死版本的 OpenCode CLI：一条 JSON 命令完成一次无头对话，并可选地在沙箱端口上打开 OpenCode 自己的 HTTP 服务。供应商配置指向 OpenAI 兼容端点。本环境使用的密钥是 `ABX_LLM_API_KEY` 和 `ABX_LLM_BASE_URL`（DashScope 兼容模式）。镜像里不写入这些值。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./opencode --yes
abx run <sandbox-id> opencode_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('opencode_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/opencode_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "1.19.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回 | 上游 |
|---|---|---|---|
| `opencode_run` | 见下表 | 对象 | `opencode run --pure --format json --auto ...` |
| `opencode_version` | 无 | `"1.19.0"` | `opencode --version` |
| `opencode_setup_check` | 无 | `"ok"` | `opencode --version`，并读取 `opencode.json` |
| `opencode_serve_start` | `port` 整数，默认 `4096`；`hostname` 字符串，默认 `0.0.0.0` | 对象 | `opencode serve --pure --hostname --port` |
| `opencode_serve_status` | 无 | 对象 | 本机 `GET /global/health` |
| `opencode_serve_stop` | 无 | `"stopped"` | 向本模板启动的进程发 `SIGTERM` |

`opencode_run` 的参数：

| 参数 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `prompt` | 字符串 | 是 | | `--` 后的位置参数。不拼进 shell 字符串。 |
| `model` | 字符串 | 否 | `OPENCODE_MODEL`，否则 `dashscope/qwen3.8-flash` | `--model`，格式 `provider/model`。 |
| `agent` | 字符串 | 否 | 空（CLI 主代理 `build`） | 非空时传 `--agent`。 |
| `session` | 字符串 | 否 | 空 | `--session`，继续该会话 id。 |
| `continue_session` | 布尔 | 否 | `false` | `--continue`（上一个会话）。传 JSON 布尔值。 |
| `cwd` | 字符串 | 否 | 镜像中 `/home/user/app`，本地为模块目录 | `--dir` 以及子进程工作目录。必须是已存在的目录。 |

`opencode_run` 的返回：

| 字段 | 含义 |
|---|---|
| `text` | JSON 事件里 `type: text` 片段拼起来的文本。 |
| `stdout` | 已脱敏的 stdout，一行一个 JSON 事件。 |
| `session_id` | 这些事件里的 `sessionID`，没有则为空。 |
| `model` | 传给 `--model` 的选择器。 |
| `agent` | 传给 `--agent` 的名字，没有则为空。 |
| `cwd` | 传给 `--dir` 的目录。 |

缺少 `prompt` 时 HTTP 400。CLI 非零退出时 HTTP 500，正文是 `{"error","type":"RuntimeError"}`。消息里不含密钥。超时 600 秒。标准输入是 `/dev/null`。

`opencode_serve_start` 返回 `running`、`port`、`hostname`、`pid` 和 `healthy`。它会等到 `GET http://127.0.0.1:<port>/global/health` 返回 `{"healthy": true, "version": "1.19.0"}`。通过 `await sb.network.resolve(port)` 获取对外端点及网关头；localhost 地址仅供内部使用。同一端口与 hostname 再次启动会返回当前状态。start/status/stop 全程由进程内锁串行处理；stop 仅允许终止本解释器持有的 Popen 子进程，并校验进程组身份，不读取旧 PID 文件。命令服务器重启后不会接管旧 serve 进程；需要回收 sandbox 清理这类进程。

## 配置

| 名称 | 必填 | 默认 | 作用 |
|---|---|---|---|
| `ABX_LLM_API_KEY` | 调用 DashScope 时需要 | 空 | `opencode.json` 里的 `{env:ABX_LLM_API_KEY}`。创建沙箱时注入。 |
| `ABX_LLM_BASE_URL` | 调用 DashScope 时需要 | 空 | OpenAI 兼容的 base URL，包含 `/v1` 路径。`{env:ABX_LLM_BASE_URL}`。 |
| `OPENCODE_MODEL` | 否 | `dashscope/qwen3.8-flash` | `model` 为空时使用。 |
| `OPENCODE_API_KEY` | 否 | 空 | `model` 为 `opencode/<id>` 时的 OpenCode Zen 凭证。 |
| `OPENCODE_SERVER_PASSWORD` | 否 | 空 | `opencode serve` 的基本认证密码。未设置时 CLI 会警告。 |
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `OPENCODE_CONFIG` | 否 | `/home/user/app/opencode.json` | 子进程读取的配置文件。 |
| `OPENCODE_DISABLE_AUTOUPDATE` | 否 | 镜像里为 `true` | 阻止已钉死的 CLI 自行升级。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 时 `start()` 绑定的端口。 |

`opencode.json` 定义供应商 `dashscope`，npm 包是 `@ai-sdk/openai-compatible`。文件里带的模型 id 是 `qwen3.8-flash` 和 `qwen3.8-max`。`dashscope/` 下的其他 id 会在那一次 `opencode_run` 里写进临时配置。其他供应商的模型沿用现有配置文件；把该供应商写进 `opencode.json`，或传入文件已经允许的 `model`。

在 `template launch` 前安全导出清单中声明为空的秘密变量，让应用启动时读取；不要写入镜像、YAML 或日志。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| 端口 | 9000（命令服务），4096（`opencode serve`，仅在 `opencode_serve_start` 之后） |
| 磁盘 | 平台 rootfs，极速版大约 10G |

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史2.0.1镜像／模型验收

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 2.0.1；实际 SDK 创建的镜像沙箱、CLI/SDK 命令、28 项严格真实模型断言、独立沙箱/模板/仓库清理 | [2026-10-20](evidence/express-2026-10-20.json) · [模型](evidence/model-image-2026-10-20T142001Z.json) |

本次使用逐项核验源码和归档哈希的真实 CI 镜像。模型实际修改已有源码、生成新产物，并通过未改动的原始测试、独立断言和准确 session 延续。当时的运行时代码另有[真实平台 step 基础验证](evidence/verification-steps-2026-10-19T184023Z.json)，该记录本身不声称模型通过。该历史镜像注入的 server 为 e2cb27e；当时独立 Docker fallback 是另一条构建路径。完整来源、限制和历史失败见[验收记录](../.agents/evidence/verify/2026-10-20-native-coding-sdk-acceptance.md)。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该历史记录采用 e2cb27e 服务端来源覆盖，与当时的镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

## 二次开发

命令实现在 `commands.py`。`opencode_run` 组装 argv 列表；提示词和模型 id 保持为列表元素。新的安装步骤在 Dockerfile 里钉死版本（`npm install -g name@version` 或 `pip install name==version`）。

要改默认模型，编辑 `template.yaml` 里的 `OPENCODE_MODEL` 和 `opencode.json` 的 `model`。供应商是 `dashscope` 时，把 id 加到 `provider.dashscope.models`。该 id 必须存在于 `ABX_LLM_BASE_URL` 指向的端点。

只有在做另一个模板时才复制 `_skeleton`。本目录就是 OpenCode 条目。改动对照 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md) 和 [docs/design/opencode.md](../docs/design/opencode.md)。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py opencode`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。OpenCode CLI 是构建时安装的上游软件。

## 本地验收与模型验收

回归测试：`python3 -m pytest opencode/test_commands.py opencode/test_e2e_protocol.py -q`。真实 HTTP L0 要求服务端安装固定的 `opencode-ai@1.19.0`，然后运行 `E2E_BASE_URL=<目标地址> E2E_WORKSPACE=<目标工作目录> E2E_RUN_LLM=0 python3 opencode/e2e_test.py`。缺少 CLI 或版本不符直接失败，不依据测试机的 PATH 或密钥跳过核心能力。测试通过目标 `/shell` 执行真实 Python，并下载生成文件；OpenCode serve 的健康、版本与认证检查在目标内部执行，测试机不误探测自己的 localhost。setup_check 只读取配置并查询版本，不写配置或启动服务。

CLI 失败输出整体省略，避免在错误响应中暴露提示词、工具参数与凭据；成功 JSON 事件会对已知环境秘密值脱敏，包括短值与 JSON 转义值。serve 不保存原始日志。提示词在 `--` 后作为位置参数传递，`session` 与 `continue_session` 不能同时使用。serve 状态新增 `version`，健康检查支持配置的 Basic Auth 密码且要求固定版本。

L0 成功不能替代模型验收。默认明确输出 L3 NOT RUN。模型配置已注入服务端时，设置 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1` 才执行 L3：先通过远端文件 API 上传有缺陷的既有 calc.py 与固定 test_calc.py，运行并复现失败；要求 agent 修改源码、保持测试文件不变，并新建 report.txt 与 acceptance.txt。随后下载源码、测试及产物，校验测试字节未变、源码确已修改，再通过远端 /shell 显式指定项目 cwd 独立运行全部三个测试与额外隐藏断言。

首次编码检查全部通过后，验收器再次调用 `opencode_run`，把首次返回的确切 `session_id` 显式传入 `session`，不用全局 `continue_session`。该轮必须读取已有报告及源码，新建此前不存在的 resume.json，包含原报告真实字节的 SHA-256，以及通过现有 `add` 函数计算的额外结果。控制端独立计算预期摘要和加法结果，不在提示词提供答案；下载新产物后校验返回会话 ID 一致、原源码/测试/报告/acceptance 字节未变，并在远端重新执行隐藏断言。错误会话、缺失或错误的续会话产物、篡改原文件都会导致验收失败，最后只清理自建的唯一项目目录。仅回复 marker 或生成新文件不能通过验收。不要求测试机持有模型密钥；应用 Bearer 认证使用 `ABX_SERVER_TOKEN`；provider 网关头使用 `E2E_GATEWAY_HEADERS_JSON`。`/code/run` 属于 SDK 可选的 dev-tools 端点，capabilities 元数据本身不会启用它。这些源码运行时检查不等于 Dockerfile L1 或模板部署 L2 验收。

访问外部目标的 HTTP 客户端遵循环境代理配置；仅 sandbox 内部的 loopback serve 健康探测直连自身进程。fake-remote 协议回归通过真实本地子进程验证编码与确切会话恢复，包括拒绝错误会话、摘要或计算结果及原文件篡改；它不构成真实模型/云端验收证据。

2026-10-16 的 Express 源码运行态验证使用真实 `dashscope/qwen3.8-flash` 模型，28 项 HTTP 检查全部通过，覆盖上述精确 session 续接以及项目目录、沙箱清理。本次向已有 base 沙箱上传源码和配置，并单独安装固定版本依赖。镜像构建 L1 与新模板部署 L2 仍未验证，`tested_on` 保持为空。详见[验证记录](../.agents/evidence/verify/2026-10-16-opencode-session-resume-clean-wheel.md)。

独立测试与隐藏断言使用隔离 Python，预加载标准库后直接编译实际源码字节。
原始三个测试必须全部成功执行，不允许跳过或预期失败。每次 agent 完成后的校验，
包括确切会话恢复后的复验，都需要新生成的完成确认值；静态文本、提前零退出和
旧字节码不能替代检查完成。这不是对同用户权限恶意代码的操作系统隔离保证。
既有真实模型记录早于此次加固；新验收器须单独完成实际镜像/模型复验才能声明通过。

### 模板2.0.2运行目录属主

2.0.1真实非 root step 中版本／setup 通过，但原生 serve 启动、状态及幂等检查失败；独立沙箱诊断复现 ~/.local/share/opencode/log/opencode.log 的 PermissionDenied。首次 HOME 属主交接发生在 root 安装／版本探测之前，最后仅修复 app。2.0.2在安装后递归交接模板自己的 app／.local／.config 给 user，保留 USER user 和 OpenCode1.19.0。只读 setup 检查不可写的原生状态，不读取日志或创建文件。[Issue156](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/156)记录回归与复测。既有2.0.1镜像／模型回执保持历史范围，不算2.0.2通过；新2.0.2真实 step／完整 HTTP已通过15/0/0，耗时100.59秒，见[回执](evidence/verification-steps-2026-10-20T160725Z.json)。
