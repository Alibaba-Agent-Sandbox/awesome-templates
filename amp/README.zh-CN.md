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

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在本仓库检出目录，环境里放好极速版凭证：

```bash
abx template deploy ./amp -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> amp_version
abx run <sandbox-id> amp_setup_check
```

`template.yaml` 里已经写了 `generation`、`start_cmd` 和 `ready_cmd`。真正跑一轮需要 Amp 访问令牌。在创建时传入，不要写进镜像：

```bash
abx create --template <template-id> -y --env AMP_API_KEY=<amp-access-token>
abx run <sandbox-id> amp_execute --arg prompt='Reply with exactly: ABX_E2E_OK'
```

`stream_json` 是布尔值，用 `--json-args` 传递：

```bash
abx run <sandbox-id> amp_execute --json-args '{"prompt":"Reply with exactly: ABX_E2E_OK","stream_json":true}'
```

用完后删掉沙箱和模板：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py amp` 会用唯一别名部署，通过 `abx run` 和 Python SDK 跑 `smoke` 里的 `amp_version` 和 `amp_setup_check`，只在通过后写证据，并删除这次创建的沙箱和模板。

## 快速开始（Python SDK）

在配套包正式发布前，请按[固定提交的配套源码安装说明](../docs/python-client-installation.md)安装 `agent-sandbox-client`。导入名仍是 `agent_sandbox`。`pip install agent-sandbox` 是另一个无关项目。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("amp_version"))
        print(await sb.run("amp_setup_check"))
        # AMP_API_KEY 是 Amp 访问令牌，不是 DashScope 密钥。
        # print(await sb.run("amp_execute", prompt="Reply with exactly: ABX_E2E_OK"))
    finally:
        await sb.kill()

asyncio.run(main())
```

需要 `amp_execute` 时在创建时带上密钥：

```python
sb = await Sandbox.create(
    template="<template-id>",
    timeout=300,
    envs={"AMP_API_KEY": "<amp-access-token>"},
)
text = await sb.run("amp_execute", prompt="Reply with exactly: ABX_E2E_OK", stream_json=False)
```

`await sb.run(...)` 返回该命令的 `result`。`sb.commands.run` 跑的是 shell，不是这些命名命令。当前检出的 SDK 已在 [python-sdk#24](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/24) 修复同步类方法；旧提交遇到 TypeError 时请升级或使用异步构造。

## 快速开始（HTTP POST）

使用沙箱端口 9000 的 URL；本地默认 http://127.0.0.1:9000。服务启用了 ABX_SERVER_TOKEN 时才添加认证头。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/amp_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{}'
```

请求体直接包含命名命令参数，不嵌套在 args 中。HTTP 200 的响应为 `{"result":"0.0.1792022479-ge66e24"}`。参数错误为 HTTP 400，认证失败为 401，执行异常为 500；错误响应包含 error 和 type。命令响应在执行完成后整体返回。HTTP 客户端超时不保证取消服务端命令；长任务使用进程 API 管理。

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
| `ABX_SERVER_TOKEN` | 否 | 空 | 沙箱内设置之后，客户端发送 `Authorization: Bearer`。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地执行 `python3 commands.py` 时 `start()` 监听的端口。 |

密钥放在 `abx create --env` 或 `Sandbox.create(envs=...)`。不要写进镜像或日志。

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

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

尚未记录任何通过的提供方测试。

1.2.0 修改了权限默认值与检查接口；当前版本尚未完成镜像构建、部署和模型验收。
原有 [1.1.0 证据](./evidence/express-2026-10-15.json)保留为历史，仅覆盖版本和配置检查，
不能据此声称 1.2.0 或真实编码任务已通过。

2026-10-16 在真实 Express base 中通过固定 Amp 版本、无密钥检查、设置字节不变及 7 项外部 HTTP 检查，实例已清理。[证据](./evidence/runtime-express-2026-10-16-readonly.json)。模型执行明确关闭（1 项跳过），不声称真实编码验收或 1.2.0 镜像构建、部署通过。

</details>

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
