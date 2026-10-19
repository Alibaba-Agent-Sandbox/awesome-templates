# python-hello

[English](./README.md)

## 做什么

提供最小 Python 开发沙箱：问候、执行内联 Python、运行上传的脚本和 pytest 测试，同时演示隐藏命令和自定义 GET 路由。`agent-sandbox-server` 在 9000 端口提供命名命令。

## 技术栈

- Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 自带 Python 3.13、Node.js 20。部署时默认解析为 `cn-hangzhou` 和 `v0.0.49`。
- 服务端固定到 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505`，部署注入的 SDK wheel 优先。
- 镜像安装 `pytest==8.4.2`，供 `test` 命令使用。
- 非 root 用户 `user`，工作目录 `/home/user/app`，generation 2。平台执行 YAML 的 `start_cmd` 并用 `ready_cmd` 探测就绪。

## 解决的问题

用于学习命名命令协议，或通过同一沙箱上传、运行、测试 Python 程序。内联代码、脚本路径、pytest 路径统一使用一个工作目录，避免上传文件与执行目录不一致。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在仓库根目录执行，使用已经配置好的 Express provider：

```bash
abx template deploy ./python-hello -y
abx create --template <template-id> -y
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> run_script --json-args '{"code":"print(21 * 2)"}'
abx upload <sandbox-id> ./main.py /home/user/app/main.py
abx run <sandbox-id> run --arg file=main.py
abx upload <sandbox-id> ./test_main.py /home/user/app/test_main.py
abx run <sandbox-id> test --arg path=test_main.py
```

部署结果提供 `<template-id>`，创建结果提供 `<sandbox-id>`。`hello` 返回 `Hello, Ada!`，`run_script` 返回 `42\n`。脚本与测试文件由你提供。`abx run` 调用命名命令，shell 使用 `abx exec`。完成后清理：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

客户端发行名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。配套版本发布前，请按[固定提交的双包安装说明](../docs/python-client-installation.md)安装。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
        print(await sb.run("run_script", code="print(21 * 2)"))
        await sb.files.write("/home/user/app/main.py", "print(6 * 7)\n")
        await sb.files.write(
            "/home/user/app/test_main.py",
            "def test_answer():\n    assert 6 * 7 == 42\n",
        )
        print(await sb.run("run", file="main.py", timeout=70))
        print(await sb.run("test", path="test_main.py", timeout=130))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`Sandbox.connect` 可连接已有沙箱。`sb.run` 返回 JSON 中的 `result`，`sb.commands.run` 是进程/shell API。`sb.run` 的 `timeout` 单位为秒，控制 HTTP 等待时间；各命令的执行期限固定，见下表。客户端超时不能保证服务端工作取消；后台运行、重连、取消应使用进程 API。

## 快速开始（HTTP POST）

`ABX_SERVER_URL` 使用沙箱的 `sb.network.get_url(9000)`，本地可用 `http://127.0.0.1:9000`。Express 的 9000 端口服务不要求沙箱网关 token；匿名服务器不应接收 envd 的 `X-Access-Token`。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello" \
  --header 'Content-Type: application/json' \
  --data '{"name":"Ada"}'
# {"result":"Hello, Ada!"}
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/run_script" \
  --header 'Content-Type: application/json' \
  --data '{"code":"print(21 * 2)"}'
# {"result":"42\n"}
```

请求体直接包含参数，没有 `args` 包装。`POST /commands/run` 加 `{"file":"main.py"}` 运行已上传脚本；`POST /commands/test` 加 `{"path":"test_main.py"}` 运行测试。成功返回 `{"result":"<stdout>"}`。`GET /commands` 列出公开命令；`GET /hello/Ada` 返回 `{"greeting":"Hello, Ada!"}`。

服务端认证与 provider 网关认证分别配置。如果沙箱设置了 `ABX_SERVER_TOKEN`，受保护的请求需携带 `Authorization: Bearer $ABX_SERVER_TOKEN`；`/health` 不要求 server token。SDK 可使用 `sb.server_at(9000, token=server_token).commands.run(...)`，token 从应用的安全配置获得。需要网关访问头的 provider 还需添加该访问头，例如 `sb.network.get_access_headers()` 提供的 `X-Access-Token`，同时保留服务端 bearer token。本模板只有 Express 的历史证据，其他 provider 尚未验证。

缺少或无效参数返回 HTTP 400，认证失败 401，未知命令 404，执行失败 500；错误对象包含 `error` 和 `type`。命令完成后一次返回完整输出。HTTP 客户端超时仅结束等待，不能保证服务端取消。

## 命令参考

下列参数均为字符串，模板没有额外长度限制。路径可相对于工作目录，也可为绝对路径，需运行用户 `user` 可访问；代码以该用户权限执行。这些命令用于执行调用者提供的 Python，应只向可信调用者开放。

| 命令 | 参数 | 必填/默认值 | 返回值 | 执行期限 |
|---|---|---|---|---|
| `hello` | `name: str` | 可选，`World` | `Hello, <name>!` | 不启动子进程 |
| `run_script` | `code: str` | 必填 | Python stdout | 30 秒 |
| `run` | `file: str` | 可选，`main.py` | 脚本 stdout | 60 秒 |
| `test` | `path: str` | 可选，`.` | pytest stdout | 120 秒 |
| `_debug_info` | 无 | 发现列表隐藏，但可调用 | 含 `python`、`system` 的对象 | 不启动子进程 |

`run_script` 使用服务器自身的 Python 加 `-c`；`run` 将文件作为 argv 参数；`test` 执行 `python -m pytest -p no:cacheprovider <path>`。不进行 shell 插值。非零退出（包括 pytest 没有找到测试）、进程启动失败和执行超时返回 HTTP 500，使用固定诊断，退出码存在时会附上。失败消息不包含 argv、源码或捕获的输出；成功 stdout 按设计返回，可能包含程序打印的数据。镜像不自带示例测试，需自行上传。空字符串可通过字符串类型检查，后续可能导致子进程错误。

## 配置

| 变量 | 必填 | 默认值 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 空 | 可选服务端 bearer 认证，在创建沙箱时注入。 |
| `WORKSPACE` | 否 | `commands.py` 所在目录 | 所有 Python 子进程使用的已有目录，调整时同步修改上传路径。 |
| `ABX_SERVER_BASE_DIR` | 否 | `/home/user` | 文件 API 路径边界；自定义工作目录需位于该边界内。此设置不限制任意 Python 代码。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 监听端口；云端 `start_cmd` 固定指定 9000。 |
| `LANG` | 否 | `C.UTF-8` | Unicode 输出。 |

通过已有安全配置和 `Sandbox.create(envs=...)` 传入秘密值，YAML 只保留空的秘密变量声明。不要记录 token 或上传凭据文件。

## 资源

2 vCPU、2048 MB 内存、9000 端口，使用 provider 根文件系统（Express 约 10G）。无需 GPU、Docker、KVM 或模型 API key。大任务可能超出内存或执行期限，应选择合适的进程 API/provider。

## 源码运行验证

2026-10-16，当前命令源码和 pytest 8.4.2 在 `alicloud-express` 完成外部 HTTP
测试（20 条 PASS、无失败），包括真实脚本/pytest 执行和远端文件传输。本次沙箱已删除。
[运行证据](evidence/runtime-express-2026-10-16.json)记录源码/包哈希，另有
[检查日志](evidence/runtime-express-2026-10-16.log)。本次在平台基础沙箱内运行时安装依赖，
不等同于此版本 Dockerfile 镜像构建或新模板部署通过。

## 已验证

尚未记录任何通过的提供方测试。

此状态对应 **1.1.0**。[2026-10-15 Express 历史证据](./evidence/express-2026-10-15.json) 仅证明 **1.0.0** 的 `hello` 经 CLI 和 SDK 成功，不能证明新版基础镜像、pytest、文件或脚本操作已通过。新 provider 验证成功前 `tested_on` 保持空列表。本地 HTTP 是 L0，不能代替镜像构建或云端验收。

## 二次开发

在 `commands.py` 新增带类型签名的 `@command("name")` 函数，`start()` 保留在 main guard 中。返回 JSON 可序列化值，子进程失败应抛异常，参数使用 argv 列表。新增依赖固定版本并放在 Docker 前面的安装层，最后复制命令文件以复用依赖层。同步维护中英文文档、YAML smoke 和[设计说明](../docs/design/python-hello.md)。

仓库根目录安装开发服务端、`httpx`、pytest、PyYAML 后：

```bash
python3 scripts/check_template.py python-hello
python3 -m pytest python-hello/test_command_errors.py -q
python3 scripts/run_local_e2e.py
python3 scripts/express_e2e.py python-hello
```

本地 runner 启动真实 HTTP 服务和工作目录，测试文件上传/下载/列表/删除、上传脚本执行、pytest 成功和故意失败的用例。文件错误视为失败，不再 SKIP。Express harness 需要已配置凭据和 Docker，仅在 CLI/SDK smoke 全部通过后写入证据，并清理本次创建的资源。Express smoke 通过不代表所有本地回归都已在云端执行。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py python-hello`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

遵守 [CONTRIBUTING.md](../CONTRIBUTING.md) 和[模板规范](../docs/template-spec.zh-CN.md)，分别报告本地、构建、云端结果，保留历史证据。

## 问题反馈

模板跟踪：[awesome-templates#21](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/21)。模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，Python 客户端/服务端问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI 标题使用 `[templates]`，提供无秘密的复现、provider、generation 和源码版本。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。
