# Factory Droid

## 做什么

模板1.2.0 新增 `droid_byok`：真实固定版本 CLI 使用显式兼容模型接口，无需 Factory 账号；原有 `droid` 账户模式保留。两种模式均使用每次调用独立状态及有界自有进程清理。当前1.2的原生 SDK/极速版/BYOK 验收已通过，详见下节；旧回执保留历史范围。

在现有项目上无头运行 Factory Droid 0.241.1。具名命令提供有执行时限的编码调用、版本查询与不调用模型的安装检查。

## 技术栈

官方 npm `@factory/cli@0.241.1` 与 `@factory/cli-linux-x64@0.241.1`、完整 npm integrity [锁文件](package-lock.json)、未修改原生二进制 SHA256 `1f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1`、阿里云 FC 基础镜像、Python3.13及固定 servere2cb27e。禁用安装 hooks，直接执行固定原生路径，每次原生命令和构建均检查 SHA256。见[来源](upstream.json)、[上游声明](UPSTREAM-NOTICE.md)、[Dockerfile](Dockerfile)。上游标记为私有 `UNLICENSED`，仓库元数据不证明源码公开。非 root `user`、generation2、9000端口。

## 解决的问题

自动化可通过 Agent Sandbox 上传项目，让 Droid 修改源文件，再读取产物并独立运行测试。旧 Factory 模式缺少账户凭据会在启动前拒绝登录；BYOK 使用独立的兼容模型配置。`WORKSPACE` 指定项目根目录；成功输出与错误消息均对已配置秘密值脱敏。

## 快速开始（CLI）

主要路径为显式 BYOK。占位符替换为本次唯一目录和所属资源 ID，准备前先发布固定源码。编码调用前须按三个 `DROID_MODEL_*` 配置启动服务，密钥不要放在 CLI 参数中。以下原生 CLI0.4.1 语法已核对源码，当前版本云验收已通过，CLI 示例仅核对源码；要求官方 READY 并独立确认所属资源清理。

```bash
python scripts/prepare_steps.py droid --output /tmp/droid-steps-<unique-run> --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/droid-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> droid_version
abx --native run <owned-sandbox-id> droid_byok_setup_check
abx --native run <owned-sandbox-id> droid_byok --arg prompt='Create hello.txt containing Hello from Droid.'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

以下保留示例使用独立的 Factory 账户命令。

示例使用当前极速版 CLI：`abx create <template-id> --detach` 输出沙箱 ID，`abx kill <sandbox-id>` 清理沙箱；命名命令使用 `abx run`。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

按[官方安装说明](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox#readme)安装 CLI，在 `alicloud-express` 构建：

```bash
abx template install alibaba-agent-sandbox/awesome-templates//droid
abx create <template-id> --detach
abx run <sandbox-id> droid_version
abx run <sandbox-id> droid_setup_check
abx run <sandbox-id> droid --arg prompt='Review the existing project' --arg auto=''
```

使用安装返回的模板 ID。创建沙箱时通过私有环境配置注入 `FACTORY_API_KEY`；提供方凭据与 Factory 产品密钥不同。最后一条命令需要 Factory 密钥。编码前通过 SDK 文件 API 上传项目。结束后执行 `abx kill <sandbox-id>`。

## 快速开始（Python SDK）

BYOK 示例使用配套 `agent-sandbox-client`，按[源码安装说明](../docs/python-client-installation.md)安装。配置在服务导入时捕获，须检查 setup 标志；预热进程需要[显式环境启动](../docs/runtime-environment.zh-CN.md)。模型密钥不经具名命令参数传递。示例已通过语法检查，记录中的云验收已通过显式9010服务执行这些 SDK 操作。

```python
import asyncio
import os
import secrets

import httpx
from agent_sandbox.api.sandbox import Sandbox

async def example():
    settings = {name: os.environ[name] for name in ('DROID_MODEL_API_KEY', 'DROID_MODEL_BASE_URL', 'DROID_MODEL')}
    token = secrets.token_urlsafe(32)
    settings.update(HOME="/home/user", WORKSPACE='/home/user/app',
                    ABX_SERVER_BASE_DIR='/home/user/app', ABX_SERVER_TOKEN=token,
                    PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin")
    sb = await Sandbox.create(template="<owned-template-id>", timeout=1200)
    stream = drain = server = None
    try:
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py",
            env=settings, timeout=1100)
        started = asyncio.Event()
        async def consume():
            async for chunk in stream:
                if chunk.pid:
                    started.set()
        drain = asyncio.create_task(consume())
        await asyncio.wait_for(started.wait(), 90)
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(60):
                try:
                    response = await client.get(sb.network.get_url(9010) + "/health",
                                                headers=sb.network.get_access_headers())
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("configured server not healthy")
        server = sb.server_at(9010, token=token)
        print(await server.commands.run('droid_version', timeout=90))
        setup = await server.commands.run('droid_byok_setup_check', timeout=60)
        if not all(setup.get(k) is True for k in ("api_key_set", "base_url_set", "model_set")):
            raise RuntimeError("model configuration not present in this server")
        await sb.files.write("/home/user/app/calc.py", "def add(a, b): return a - b\n")
        result = await server.commands.run("droid_byok", prompt="Fix calc.py so add returns the sum.",
                                           command_timeout=600, timeout=660)
        if result["exit_code"] != 0:
            raise RuntimeError("native Droid did not complete successfully")
        print(await sb.files.read("/home/user/app/calc.py"))
    finally:
        try:
            if server is not None:
                await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                if drain is not None:
                    drain.cancel()
                    await asyncio.gather(drain, return_exceptions=True)
                if stream is not None:
                    await stream.cancel()

asyncio.run(example())
```

保留的 Factory 账户模式示例：

客户端包名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。版本尚未发布时使用[配套源码安装](../docs/python-client-installation.md)。

```python
import asyncio
import os
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(
        template="<template-id>", timeout=600,
        envs={"FACTORY_API_KEY": os.environ["FACTORY_API_KEY"]},
    )
    try:
        await sb.files.write("/home/user/app/calc.py", "def add(a, b):\n    return a - b\n")
        print(await sb.run("droid_version"))  # "0.241.1"
        print(await sb.run("droid", prompt="Fix calc.py so add returns the sum.",
                           auto="low", command_timeout=300, timeout=360))
        print(await sb.files.read("/home/user/app/calc.py"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`command_timeout` 控制服务端执行期限；`Sandbox.run(timeout=360)` 控制客户端 HTTP 等待时间。客户端超时不保证取消进程。具名命令返回缓冲结果；后台执行、进度和取消使用 SDK 进程 API。

## 快速开始（HTTP POST）

BYOK 使用直接 JSON 参数对象，将自己的服务 URL/token 注入环境。返回 `{"result":{"exit_code":0,"native_version":"0.241.1","stdout":"<native JSON>","stderr":""}}`。原生非零退出保留在 `exit_code`，不能仅凭 HTTP200认定智能体成功。`POST /commands/droid_byok_setup_check` 接受 `{}`。参数结构错误400、认证401、未知命令404、语义/配置/期限错误500。结果缓冲返回，断开连接不会取消执行。

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/droid_byok" -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' -d '{"prompt":"Fix calc.py so add returns the sum.","command_timeout":300}'
```

保留的 Factory 账户 HTTP：

通过 `sb.network.get_url(9000)` 获取沙箱 9000 端口 URL：

```bash
curl -X POST '<sandbox-port-9000-url>/commands/droid' \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer ${ABX_SERVER_TOKEN}" \
  -d '{"prompt":"Fix calc.py so add returns the sum.","auto":"low","command_timeout":300}'
```

请求体直接为参数对象，不加 `args` 包装。成功响应为 `{"result":"<缓冲的 Droid 输出>"}`。`ABX_SERVER_TOKEN` 为空时去掉该头；非空时必须带 `Authorization: Bearer <token>` 或 `X-Access-Token: <token>`。Python SDK 使用 `sb.server_at(9000, token=...)`。提供方网关鉴权与服务端鉴权不同，需要另加所选提供方要求的访问头。`GET /commands` 返回签名；`POST /commands/droid_version` 与 `/commands/droid_setup_check` 接受 `{}`。

HTTP 400 表示缺少参数或类型错误；401 表示服务端鉴权失败；404 表示未知命令；500 表示参数范围无效、缺少 Factory 凭据、上游执行失败或执行超时。响应不流式返回。

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
| `ABX_SERVER_TOKEN` | 空 | 可选 HTTP 服务鉴权。 |
| `WORKSPACE` | `/home/user/app` | 现有项目根目录；显式配置无效目录会报错。 |
| `FACTORY_DROID_AUTO_UPDATE_ENABLED` | `false` | 子进程强制禁用自动更新，保持固定版本。 |

Factory 凭据在 [Factory API 密钥设置](https://app.factory.ai/settings/api-keys)获取。DashScope 或 OpenAI 密钥不能替代 `FACTORY_API_KEY`。`droid_byok` 使用私有原生 `customModels` 配置，provider 为 `generic-chat-completion-api`，显式模型/base 及 `apiKey: "${ABX_DROID_MODEL_KEY}"`。真实密钥不写入设置或 argv，不注入 Factory 密钥、交互登录或替代二进制。输出脱敏密钥/base 并删除私有状态。[官方 BYOK 文档](https://docs.factory.com/model-independence/byok)；固定0.241.1 已通过仅合成固定响应探测，该探测不是实际模型验收。上游行为见 [Droid Exec](https://docs.factory.com/droid-exec/overview)，具体选项以固定版本的真实帮助为准。脱敏涵盖 stdout、错误中的原始与 JSON 转义的已配置秘密值；Agent 写出的项目文件仍需遵守正常的秘密管理要求。cwd 约束用于选择项目，不是操作系统安全隔离边界。

## 资源

默认 2 vCPU、2048 MB 内存、9000 端口。BYOK 需要访问配置的模型服务，旧 Factory 模式需要其外部网络。平台启动 `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`，就绪探针为 `agent-sandbox-server healthcheck --port 9000`。

## 已验证


### 当前镜像验收 — 2026-10-22

| 提供方 | 当前版本与范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 1.2.0；常规镜像、真实 CLI/SDK、完整 HTTP 8 PASS / 0 FAIL / 0 SKIP、沙箱/模板/私有镜像仓库独立清理 | [运行与 HTTP 回执](evidence/image-http-2026-10-22T110246Z.json) |
| opensandbox | 1.2.0；原始 Docker 后端、逐项 CLI/SDK 命名 smoke、完整 HTTP 8 PASS / 0 FAIL / 0 SKIP、SDK/容器/进程独立清理 | [原生源码镜像回执](evidence/opensandbox-2026-10-22T111346Z.json) |

CLI 在 OpenSandbox 中通过实际 `abx exec` 调用容器内命名 HTTP API；通用 `run_code` 仍不支持，`template launch` 的能力检查仍生效。缺少模型或厂商账号的检查按回执明确跳过，不计为真实模型通过。[复现与验收范围](../docs/source-image-acceptance.zh-CN.md)。

<details>
<summary>此前验收记录（保留原有时间与范围）</summary>

模板1.2.0 为 experimental，`tested_on: [alicloud-express]`。
[同源码镜像 L1](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39500551739)、
[标准原生步骤及 SDK 创建](evidence/express-2026-10-20T212811Z.json)、
[完整 HTTP/模型记录](evidence/verification-steps-2026-10-20T212811Z.json)通过：HTTP8PASS/0FAIL/0SKIP，
真实批准模型 BYOK17PASS/0FAIL/0SKIP。传入真实模型密钥前，云端原生合成探测已确认正确模型/Bearer、
冲突项目配置零请求、六种原生文件工具和测试文件/端口清理。真实编码修复已有失败源文件，原测试字节不变，
生成新报告及 nonce 产物，返回后以不可预知 ACK 独立通过完整原测试与隐藏用例。所属项目、私有状态、
监听端口及外层沙箱/模板均独立确认清理，耗时134.596秒。不声明当前 Factory 账户模型或其他提供商通过。
SDK 示例已核对语法，云记录通过显式9010服务执行同样 SDK 操作；历史回执不改写。

</details>

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

2026-10-18 源码运行验收：原生 Python SDK 完成固定版本 Droid 后台安装、SDK 无密钥版本/配置检查、外部 HTTP 套件与自有资源清理，九项记录均通过。见[准确范围证据](../.agents/evidence/verify/2026-10-18-droid-native-runtime.md)。这不是镜像标准部署 L2 或模型验收，`tested_on` 不变。

尚未记录通过的标准镜像部署厂商验收。

</details>

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
