# amp

Agent Sandbox 里的 Sourcegraph Amp CLI。镜像钉住 `@ampcode/cli`，在端口 9000 上提供命名命令。

## 做什么

安装 Amp CLI（命令名 `amp`），并注册四个命令：

| 命令 | 实际执行 |
|---|---|
| `amp_version` | `amp version` |
| `amp_setup_check` | `amp version`，然后只读检查现有设置文件 |
| `amp_execute` | `amp --no-color --no-notifications --no-ide -x <prompt>` |
| `amp` | `amp_execute` 的旧名字。参数相同。 |

`stream_json` 为 true 时，`amp_execute` 加上 `--stream-json`。HTTP 响应是进程退出后的完整标准输出，不是实时流。

`amp_execute` 在启动 CLI 之前检查 `AMP_API_KEY`。变量缺失或只有空白时，命令返回的错误里写明 `AMP_API_KEY`，并说明 CLI 自己会进入设备登录并等待。2026-10-15 实测：不带密钥执行 `amp -x` 会打印设备登录 URL 并一直等待。这个命令不会走那条路径。

Amp 不接受 DashScope 密钥、`ABX_LLM_API_KEY` 或 OpenAI 兼容的 base URL。令牌是 Amp 自己的访问令牌，在 [ampcode.com 设置](https://ampcode.com/settings/security#access-token) 创建。

`--dangerously-allow-all` 是 `0.0.1792022479-ge66e24` 这个二进制接受的标志。该版本的 `amp --help` 选项列表里没有它。帮助文本里写的是设置项 `amp.dangerouslyAllowAll`。仅显式传入 `dangerously_allow_all=true` 时，`amp_execute` 才会添加该标志。已有设置保持原样，可用 `amp_setup_check` 检查其权限值。镜像默认值为 false。

## 技术栈

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template deploy` 把 `<region>` 换成 `ALIBABA_CLOUD_REGION_ID` 或 `cn-hangzhou`，把 `<tag>` 换成 `ABX_BASE_IMAGE_TAG` 或 `v0.0.49`。
- 基础镜像里的 Node.js 20，只用来跑 `npm`。`amp` 二进制是同版本可选包 `@ampcode/cli-linux-x64` 里的 glibc ELF。
- `@ampcode/cli@0.0.1792022479-ge66e24`，来自 2026-10-15 的 `npm view @ampcode/cli version`。目录里原来的 pin 是 `0.0.1791964847-g13f24a`。基础镜像把 npm 源设成 `registry.npmmirror.com`，该源对这个版本的 `@ampcode/cli-linux-x64` 返回 404，所以 Dockerfile 从 `https://registry.npmjs.org` 安装。构建时会跑 `amp version`，原生二进制没解出来时构建失败。
- `agent-sandbox-server` 来自 python-sdk 提交 `61c43e0be65a1f57aa09186d578e7b399e48429b`（PR #21）。这个发行包不在 PyPI 上。
- git 和 ripgrep。
- 工作目录 `/home/user/app`。运行用户 `user`。平台用 `start_cmd` 启动进程。Dockerfile 没有 `CMD` 或 `ENTRYPOINT`。

## 解决的问题

generation 2 沙箱可以在没有 TUI 的情况下运行钉死版本的 Amp CLI；不带密钥就能只读检查版本和已有设置文件；`AMP_API_KEY` 缺失时拒绝执行，而不是堵在设备登录上。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
abx --provider alicloud-express template launch ./amp --workflow application --yes
abx run <sandbox-id> amp_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。OpenSandbox 的配置、每次调用的提供方选择和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('amp_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/amp_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.0.1792022479-ge66e24"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `amp_version` | 无 | 字符串 | `amp version` 的第一个字段，例如 `0.0.1792022479-ge66e24`。 |
| `amp_setup_check` | 无 | 对象 | `installed`、`package`、`version`、`api_key_set`、`settings_path`、`settings_exists`、`dangerously_allow_all`、`updates_mode`。不写文件；文件缺失时报告 false 和 `default`。 |
| `amp_execute` | `prompt` 字符串，必填。`stream_json` 布尔，可选，默认 `false`；`dangerously_allow_all` 布尔，可选，默认 `false`。 | 字符串 | `amp -x` 的标准输出。`stream_json` 为 true 时加上 `--stream-json`。 |
| `amp` | 与 `amp_execute` 相同 | 字符串 | 旧命令名。 |

`POST /commands/amp_execute`，请求体 `{"prompt":"hi"}`，CLI 退出码为 0 时响应 `{"result":"<stdout>"}`。缺少 `prompt` 是 HTTP 400。缺少 `AMP_API_KEY`、找不到二进制，或 `amp` 非零退出，是 HTTP 500，响应体含 `error` 和 `type`。`api_key_set` 只是布尔值，不返回密钥。成功与错误输出均会替换环境中配置的秘密值，包括 JSON 转义形式。命令超过 600 秒后会终止自己创建的进程组；客户端超时不等于取消。

镜像预置以下 JSON；检查和执行命令均不创建或覆盖设置：

```json
{
  "amp.dangerouslyAllowAll": false,
  "amp.updates.mode": "disabled",
  "amp.notifications.enabled": false
}
```

路径优先用 `AMP_SETTINGS_FILE`；设置了 `WORKSPACE` 时用 `$WORKSPACE/.e2e_amp/settings.json`；`HOME` 为 `/home/user` 时用 `/home/user/.config/amp/settings.json`。镜像里设置了 `AMP_SETTINGS_FILE=/home/user/.config/amp/settings.json`。

## 配置

该子进程生命周期实现要求 Linux。命令在成功、错误及执行截止时都会清理自己创建的进程组。读取输出期间保留未回收的 leader，组清理完成后才回收，避免重定向输出的后台后代在命令结束后继续运行。

| 名称 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `AMP_API_KEY` | `amp_execute` 需要 | 空 | Amp 访问令牌。不是 DashScope 或 OpenAI 密钥。`template.yaml` 里的值是空字符串。 |
| `AMP_URL` | 否 | `https://ampcode.com/` | Amp 服务地址。这是 CLI 自己的默认值，镜像不覆盖它。 |
| `AMP_SETTINGS_FILE` | 否 | 镜像内为 `/home/user/.config/amp/settings.json` | 调用者管理的设置文件，仅作只读检查。 |
| `AMP_LOG_FILE` | 否 | 镜像内为 `/home/user/.cache/amp/logs/cli.log` | CLI 日志路径。 |
| `ABX_SERVER_TOKEN` | 是 | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地执行 `python3 commands.py` 时 `start()` 监听的端口。 |

在 `template launch` 前安全导出清单中声明为空的秘密变量，让应用启动时读取；不要写入镜像、YAML 或日志。

在镜像外启动 `commands.py` 之前请设置 `AMP_SETTINGS_FILE` 或 `WORKSPACE`。否则当 `HOME` 不是 `/home/user` 时，进程会检查当前目录的 `.e2e_amp/settings.json`，不会创建目录。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs，极速版大约 10G |

带工具的真实 agent 回合没有测过内存。不需要密钥的命令（`amp_version`、`amp_setup_check`）在这个规格下可以跑。`amp` 二进制大约 130 MB。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

版本钉在 Dockerfile 的 `AMP_CLI_VERSION`（`@ampcode/cli@0.0.1792022479-ge66e24`）和 `template.yaml` 里 `amp_version` 的 smoke 期望值。跑过 `npm view @ampcode/cli version` 之后，同时改这两处，以及 `e2e_test.py` 里的 `PINNED_VERSION`，再跑一次 `amp version`，让 smoke 字符串等于输出的第一个字段。

`amp_execute` 用参数数组调用 CLI。不要把 prompt 拼进 shell 字符串。`AMP_API_KEY` 检查必须放在 `subprocess` 之前，避免缺密钥时堵在设备登录。检查必须只读，权限绕过只能显式启用。在仓库根目录运行 `python -m pytest amp/test_commands.py` 和 `python scripts/run_local_e2e.py` 验证本地行为；本地通过不等于模型验收。目标具有兼容密钥时，设置 `E2E_BASE_URL`、`E2E_WORKSPACE` 并运行 `E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python amp/e2e_test.py`：先证明源码测试失败，再验证真实文件修改、新建产物、原测试未改动，以及隔离 Python 测试和独立额外断言。该显式验收允许工具修改唯一的临时项目并在结束后清理；回复标记本身不能通过。

要加命令，再注册一个用参数数组调用 `amp` 的 `@command`。`start()` 只放在 `if __name__ == "__main__"` 下面。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py amp`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md)。设计说明在 [docs/design/amp.md](../docs/design/amp.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。

### 2026-10-20完整 step 检查点：模板1.2.0

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154625Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，7 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
