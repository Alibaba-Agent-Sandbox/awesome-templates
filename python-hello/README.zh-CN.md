# python-hello

[English](./README.md)

## 做什么

提供最小 Python 开发沙箱：问候、执行内联 Python、运行上传的脚本和 pytest 测试，同时演示隐藏命令和自定义 GET 路由。`agent-sandbox-server` 在 9000 端口提供命名命令。

## 技术栈

- Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 自带 Python 3.13、Node.js 20。部署时默认解析为 `cn-hangzhou` 和 `v0.0.49`。
- 服务端固定到 python-sdk 提交 `e2cb27e24fde0a67112f82b8d44af463445a5d1a`，部署注入的 SDK wheel 优先。
- 镜像安装 `pytest==8.4.2`，供 `test` 命令使用。
- 非 root 用户 `user`，工作目录 `/home/user/app`，generation 2。平台执行 YAML 的 `start_cmd` 并用 `ready_cmd` 探测就绪。

## 解决的问题

用于学习命名命令协议，或通过同一沙箱上传、运行、测试 Python 程序。内联代码、脚本路径、pytest 路径统一使用一个工作目录，避免上传文件与执行目录不一致。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./python-hello --workflow application --yes
abx run <sandbox-id> hello --json-args '{"name": "Express"}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('hello', name='Express'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/hello`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{"name": "Express"}
```

该检查的预期响应：

```json
{"result": "Hello, Express!"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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
| `ABX_SERVER_TOKEN` | 是 | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `WORKSPACE` | 否 | `commands.py` 所在目录 | 所有 Python 子进程使用的已有目录，调整时同步修改上传路径。 |
| `ABX_SERVER_BASE_DIR` | 否 | `/home/user` | 文件 API 路径边界；自定义工作目录需位于该边界内。此设置不限制任意 Python 代码。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 监听端口；云端 `start_cmd` 固定指定 9000。 |
| `LANG` | 否 | `C.UTF-8` | Unicode 输出。 |

在 `template launch` 前安全导出清单中声明为空的秘密变量，让应用启动时读取；不要写入镜像、YAML 或日志。

## 资源

2 vCPU、2048 MB 内存、9000 端口，使用 provider 根文件系统（Express 约 10G）。无需 GPU、Docker、KVM 或模型 API key。大任务可能超出内存或执行期限，应选择合适的进程 API/provider。

## 源码运行验证

2026-10-16，当前命令源码和 pytest 8.4.2 在 `alicloud-express` 完成外部 HTTP
测试（20 条 PASS、无失败），包括真实脚本/pytest 执行和远端文件传输。本次沙箱已删除。
[运行证据](evidence/runtime-express-2026-10-16.json)记录源码/包哈希，另有
[检查日志](evidence/runtime-express-2026-10-16.log)。本次在平台基础沙箱内运行时安装依赖，
不等同于此版本 Dockerfile 镜像构建或新模板部署通过。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

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

### 显式选择通用镜像构建方案

在 OpenSandbox 上使用 `abx template launch` 时，显式传入
`--workflow application --build-profile portable`。`Dockerfile.portable` 使用
摘要固定的 Python 基础镜像，创建非 root 用户并直接安装固定源码版本的命令服务。
默认 Dockerfile 保留 Express 平台占位参数；Provider 不会改写构建文件或注入 wheel。
创建完成后，application 工作流通过 `exec.run` 启动服务。所选构建方案与源码实际
字节都属于启动身份。声明此方案本身不代表已经通过真实后端验收。

独立的 `application-image` 工作流让 Python `launch_workflow` 消费已准备好的不可变 OCI 镜像；它不执行源码准备。
