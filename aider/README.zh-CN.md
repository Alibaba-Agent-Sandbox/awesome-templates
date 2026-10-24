# Aider

## 做什么

真实调用官方 `aider-chat==0.86.2` CLI。默认 **ask 只读模式**；只有显式
`allow_write=true` 才允许回写指定文件。工作目录必须属于已有 git 仓库。
每轮只把白名单文件复制进临时 git 工作区，完成后检查原文件未被并行修改，
再回写选中的结果，不自动提交。它不是交互式 Aider 的全部功能替代品。

## 技术栈

Alibaba FC base `v0.0.49` 的 Python 3.13 server 与 Node 20 保持原状。
Aider 官方要求 Python `>=3.10,<3.13`，因此单独安装经过 SHA256 校验的
python-build-standalone **3.12.12 / 20260211**，并在 `/opt/aider` 的独立
venv 中安装固定 Aider。server 使用源码构建的 wheel，或 Dockerfile 中的
固定 SDK commit。无需浏览器、Node 升级或另一套 HTTP server。

## 解决的问题

在沙箱中执行有边界的代码审查和修改，不把 Aider 的整套 Python 依赖装进
调用方环境，也不默认将整个仓库、配置与凭据发送给模型。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./aider --workflow application --yes
abx run <sandbox-id> aider_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('aider_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/aider_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "aider 0.86.2"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回与真实调用 |
| --- | --- | --- |
| `aider_version` | 无 | 字符串 `aider 0.86.2`；真实执行 `aider --version` |
| `aider_setup_check` | 无 | 安装/配置/home 阻断布尔值、固定版本和工作目录；不返回 key 或 endpoint |
| `aider` | 必填 `prompt: string`，1–100000 字符；`cwd: string=""`；`files: string="[]"`，内容是最多 32 个相对路径组成的 JSON 数组；`allow_write: boolean=false`；`command_timeout: integer=600`，范围 1–1800 | 脱敏 stdout/stderr、exit_code 与 changed_files 字典 |

每个文件最多 1 MiB。拒绝绝对路径、遍历、重复项、文件或父目录符号链接，以及
`.git`、`.env`、`.aider` 路径。尚不存在的选中路径表示新产物。未选中的 stage 输出丢弃。
显式设置 `yes-always: false` 禁用自动确认，受控 stdin 持续回答 `n` 直到进程退出，
使上游拒绝创建或编辑未加入 stage 的路径。固定版本的 config false 单独使用时
确认状态仍是未设置，而 EOF 会接受默认 Yes，因此不能用空 stdin 代替明确拒绝。
检测到并行修改会拒绝回写，但不能把它视为对恶意并行写者的隔离机制。
写入按单个文件原子替换，保留旧文件权限，不是跨全部文件的事务。
默认 ask 即使 stage 被修改也不会回写。

真实 argv 使用 `--chat-mode ask|whole`、`--message-file`、明确文件、model/base/settings，
并关闭自动提交、自动 lint/test、shell 建议、URL 检测、浏览器、analytics 与更新。
固定文字前缀使以 `/` 或 `!` 开头的 prompt 仍作为模型文本，避免上游 slash/bang
命令分派。prompt 和 API key 不出现在 argv；key 只通过子进程环境传递。

## 配置

| 名称 | 默认与含义 |
| --- | --- |
| `AIDER_API_KEY` | 空；必需兼容 API 凭据 |
| `AIDER_BASE_URL` | 空；必需 HTTP(S) endpoint，不允许内嵌凭据、query、fragment |
| `AIDER_MODEL` | 空；必需 model ID，自动加 LiteLLM `openai/` 前缀 |
| `WORKSPACE` | `/home/user/app`；默认工作目录 |
| `ABX_SERVER_TOKEN` | 启动 application 工作流前必填；独立于模型和网关凭据 |

在 `template launch` 前导出 `AIDER_API_KEY`、`AIDER_BASE_URL`、`AIDER_MODEL` 和独立应用令牌。当前 launch 路径启动该实例的命名服务，无需另启 9010 服务。修改宿主机环境不会重新配置已运行的应用；更改配置后启动新实例。

兼容配置使用 `extra_body.enable_thinking=false`，用于已验证的 Qwen 兼容路由；
扩展其他后端时调整并重新验收。key 不写入 stage 文件；选中源码仍会发往模型服务。

**原生 home 限制：** 固定上游源码总是先搜索 home 默认文件，再追加
`--config` / `--env-file`，这两个参数不能承诺完全隔离。已有 home
`.aider.conf.yml`、`.env`、model settings/metadata、OAuth key 文件时启动前拒绝。
包装层不替换 `HOME`、不修改共享 profile、不导入项目配置；
`PYTHON_DOTENV_DISABLED=1` 禁用 dotenv 加载。上游自己的 cache/install 与
analytics-disabled 状态可能保留在该专用沙箱原生 `.aider`，随实例整体销毁。
不要在共享宿主 home 中执行真实调用。

## 资源

2 vCPU、2048 MiB、9000 端口。Python 3.11 Linux x86-64 的 metadata 解析共
108 个兼容发行包、118 MiB 压缩 wheel；这不是实际镜像安装体积。
独立 Python 3.12 的 x86-64 压缩归档约 32 MiB。镜像验收另行记录。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

[Express 实际镜像补充验收](evidence/image-runtime-2026-10-16-configured.json)
已通过：实际 CI 构建镜像的官方 READY、源码/server 字节溯源、SDK/HTTP/CLI
版本与配置目标、真实 CLI 正负控，以及 qwen3.8-flash 真实编程 21 项检查，
包括独立测试和取回的产物。模型 server 在 9010，预热 9000 是独立进程。
自有 helper、实例、模板、registry 均已清理并回查。
保留[首轮失败记录](evidence/image-runtime-2026-10-16-attempt1.json)。

[加固验收器后的镜像复验](evidence/image-runtime-hardened-2026-10-16.json)
使用 `f76687e` 验收器与同一不可变镜像，真实模型检查 21 项通过，零失败、零跳过。
直接编译源码、完整执行原始测试及新的完成确认值，可以拒绝提前退出和旧缓存造成的误通过。
七项自有资源清理检查和单独的官方模板严格缺席回查均通过；旧记录保留，
其真实模型结果发生在这次完成性校验加固之前。

目录仍是 experimental，`tested_on: []`：canonical
`scripts/express_e2e.py` → `abx template deploy` 的 L2 wrapper 尚未通过。
其他 provider 未验。参见[设计](../docs/design/aider.md)。

## 二次开发

修改 `commands.py` 后补充带边界的新命令、API 表、中英文文档和正负控。
保留白名单、原文件校验和进程组清理。升级 Python/Aider pin 必须重新查官方
metadata、真实 help/version，并重跑镜像与模型测试。保留安装依赖和 Python 归档许可证。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py aider`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵循[仓库规则](../CONTRIBUTING.md)，运行
`python3 scripts/check_template.py aider`、`python3 -m pytest aider -q` 与
`python3 scripts/run_local_e2e.py`。本地无 key 检查只有 L0。
真实 coding 需专用新沙箱、`E2E_REQUIRE_LLM=1`、独立测试与文件取回，不能只看 marker。
不改旧证据，不提交 key 或原始模型日志。

## 问题反馈

[模板 Issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50)。
SDK/server 问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，
CLI/deploy 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 glue 为 Apache-2.0。[Aider](https://github.com/Aider-AI/aider) 也采用 Apache-2.0；
安装依赖与 [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
保留各自 notices。参见[官方安装](https://aider.chat/docs/install.html)与
[兼容 API 指南](https://aider.chat/docs/llms/openai-compat.html)。

实际 CLI 负控（只在全新专用沙箱运行）：

```bash
python3 aider/verify_upstream_guards.py
```

此命令使用确定性的 loopback 模型验证 slash/bang 分派与未选中路径拒绝，
不代表真实模型 coding 或实际镜像部署通过。

### 独立测试完整执行

编程控制器在隔离的 Python 进程中直接编译实际源码，核验三个原始测试逐字节不变且全部执行成功，
拒绝跳过、预期失败或未完整执行的测试。测试和隐藏用例分别要求在 Agent 退出后才生成的独立完成确认。
静态 marker、提前退出及旧字节码不能证明通过。这些检查用于确认任务完成，不构成操作系统隔离边界。
原先真实模型证据作为历史保留；加固后的验证器须单独进行真实模型测试。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。

### 当前版本新增平台 step 验收

[真实 step](evidence/express-2026-10-20T135354Z.json) 与 [外部 HTTP 尝试](evidence/verification-steps-2026-10-20T135354Z.json)：官方 READY、Python SDK 创建、CLI/SDK 冒烟，HTTP 9 通过、0 失败、1 跳过。本回执模型调用仍为 NOT_RUN；沙箱/模板及同账户私有资产缓存对象/bucket 都独立确认清理后才发布。既有镜像/模型回执保留其独立范围。
