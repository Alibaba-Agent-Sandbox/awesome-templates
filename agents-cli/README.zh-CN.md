# agents-cli

通过受限的本地 Agents HTTP API 调用固定版本的 Codex 和 Qwen Code。

## 做什么

安装 `@openai/codex@0.162.1`、`@qwen-code/qwen-code@0.23.0`，提供版本检查和六个
会话/运行时接口。客户端创建会话、提交消息并轮询输出。响应头
`X-Agent-Sandbox-Local: 1` 表示本地实现，不表示 OpenAI 托管 Agents 服务。

直接运行和模板配置的 canonical `serve` 启动方式都加载
[server-policy.json](./server-policy.json)。通用 shell、文件、进程、模型列表以及
其余 Agents 接口关闭。关闭 HTTP shell/文件接口不会移除上游 CLI 的工作区工具权限。

## 技术栈

- 阿里云 generation 2 基础镜像及其 Python；安装经 SHA256 校验的官方 Node.js `24.16.0`，替换基础 Node 20，满足 Qwen Code 的 Node >=22 要求。
- Codex `0.162.1`、Qwen Code `0.23.0`，镜像构建时断言两个实际版本。
- `agent-sandbox-server` 固定到 python-sdk 提交
  `e2cb27e24fde0a67112f82b8d44af463445a5d1a`，也支持注入源码构建的 wheel。
- 非 root 用户 `user`；程序 `/home/user/app`，工作区 `/home/user/workspace`，端口 9000。

## 解决的问题

用一套 HTTP 会话接口选择两个已安装的编码 CLI，同时保持通用沙箱接口关闭。
版本检查调用真实 CLI；关闭模型测试时不会自动换成模拟程序。

## 快速开始（CLI）

示例使用当前极速版 CLI：`abx create <template-id> --detach` 输出沙箱 ID，`abx kill <sandbox-id>` 清理沙箱；命名命令使用 `abx run`。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在本仓库目录中配置提供方构建凭据后运行：

```bash
abx template deploy ./agents-cli -y
abx create <template-id> --detach
abx run <sandbox-id> agents_version
```

结果为 `codex 0.162.1; qwen-code 0.23.0`。模型配置必须在服务进程启动前传入；
创建时的环境变量不会追配已经预热的 9000 进程。下方 SDK 验证器显式配置并启动
新的 9010 进程。不要把密钥写入镜像或版本控制文件。结束后清理自己的资源：

```bash
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

匹配的软件包发布前，按[配套固定源码说明](../docs/python-client-installation.md)安装
`agent-sandbox-client`。导入名保持 `agent_sandbox`。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("agents_version", timeout=60))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

如果创建时设置了 `ABX_SERVER_TOKEN`，通过
`await sb.server_at(9000, token="<server-token>").commands.run("agents_version", timeout=60)`
传入匹配的服务端凭据。

命名检查命令缓冲返回字符串；模型任务使用下方 HTTP 会话接口。
该策略下命名服务端的 HTTP 文件/进程接口返回 404；提供方原生 SDK 管理通道独立保留。

### Qwen 独立编码验收

在安装配套 SDK 的 checkout 中，导出支持工具调用的兼容端点 `OPENAI_API_KEY` 和
`OPENAI_BASE_URL`，并将 `OPENAI_MODEL` 设为实际模型，例如 `qwen3.8-flash`：

```bash
mkdir -m 700 /tmp/agents-cli-private-<unique-run>
python agents-cli/e2e_sdk.py --template <owned-agents-cli-template-id> \
  --journal /tmp/agents-cli-private-<unique-run>/journal.json \
  --report /tmp/agents-cli-private-<unique-run>/result.json
```

控制器自行调用 `Sandbox.create(provider="alicloud-express")`，通过提供方原生命令
通道创建一次性项目，确认精确的初始失败。随后用镜像内未改动的 commands 和策略启动
9010 进程，显式传入选定模型配置、独立服务端 token、工作区和私有状态目录。
保留原 `HOME`，不转发宿主 GitHub/云凭据；按 `--adapter` 显式选择原生适配器（默认 `qwen-code`，也可 `codex`），实际提交会话/消息并重连轮询 items。每个适配器使用全新的 journal/report；`--adapter codex` 单独验证 Codex，不能继承 Qwen 结果。不选用模拟 CLI。新服务显式采用镜像固定 Node24 的 PATH，不转发操作者 PATH。

独立原生进程要求已有源码实际改变、原测试字节完全不变、JSON 产物数值精确、报告
非空、原测试及模型新增 unittest 模块完整运行通过，并额外执行六个隐藏用例。
验证器使用隔离 Python 编译源字节，要求模型结束后新生成的随机 ACK，拒绝 skip、
提前 exit0 和旧字节码假成功，文字标记不能过关。由于原策略关闭 turn 状态/SSE
接口，另通过管理通道只读固定服务端自身的私有持久化状态，确认该会话 turn 已完成。
这是固定 `e2cb27e` 的内部诊断，不是新公共 API 或可提交的产物回执。

当前会话 API 实际以 **full_access** 运行模型，不支持通过内联 JSON 设置单会话权限
或时限。关闭 HTTP shell/文件/进程接口不会隔离 CLI 工具或任意同用户代码。
只在新建且自有的一次性沙箱中运行，不放重要文件或其他凭据。验证器检查普通正确性，
不隔离能检查或篡改自身 OS 进程的恶意代码。宿主等待 turn 默认 540 秒，可设
30–600 秒；HTTP 断线不是取消。沙箱 TTL 为 1800 秒，新服务端上限为 1500 秒，留出
准备/独立验证时间，不替代立即清理。`finally` 销毁整个自有沙箱，再分页检查 ID 及随机
metadata nonce 均不存在。权限或回查失败会导致验收失败，并保留私有恢复 journal；
确认对应自有资源已处理后再删除它。

验证器不部署/删除模板或镜像仓库，这些资源由提供模板的 owner 另行管理。
Qwen 成功不代表 Codex 成功：Codex 0.162.1 要求兼容 Responses 端点，其编码分支需
单独验收。

## 快速开始（HTTP POST）

使用沙箱端口 9000 的 URL。提供方网关需要认证时，另外加其要求的访问头；网关凭据
与服务端 `ABX_SERVER_TOKEN` 是两层认证：

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/agents_version" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{}'
```

参数直接是 JSON 对象，没有 `args` 包装。200 响应为
`{"result":"codex 0.162.1; qwen-code 0.23.0"}`。服务端支持 Bearer 或
`X-Access-Token`；若网关已使用 `X-Access-Token`，把服务端 token 放入 Bearer。
`/health` 保持公开。

显式选择运行时及目标中已有的工作目录来创建会话：

```bash
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"adapter":"qwen-code","agent":{"model":"<compatible-model>"},"environment":{"type":"self_hosted","workspace_directory":"/home/user/workspace"}}'
```

从返回结果取 `id`，提交消息并轮询：

```bash
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions/<id>/events" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"events":[{"type":"agent.session.input.message","input":[{"role":"user","content":[{"type":"input_text","text":"Describe this workspace."}]}]}]}'
curl --fail-with-body "$ABX_SERVER_URL/v1/agents/sessions/<id>/items?limit=100&order=asc" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN"
```

事件提交返回 202，模型尚未完成。400 表示参数错误，401 表示服务端认证失败，404 表示
未知/关闭的接口、运行时或会话，500 表示版本检查执行失败。部分模型错误可见于 items，
当前会话视图可能返回 idle 而不暴露最终 turn 错误；事件被接收或观察到 idle 都不代表
模型成功。SDK 验证器独立检查结果。HTTP 超时不会自动取消后台任务。


使用 `--adapter codex` 时，控制器建立独立私有 CODEX_HOME，显式配置兼容 HTTP Responses 提供方并禁用 websockets。配置只引用 OPENAI_API_KEY，不写入密钥值。明确选择已配置端点，不依赖原生默认提供方；清理销毁整个自有 sandbox 和配置。

## 命令参考

| 命令 | 参数 | 返回 | 执行 |
|---|---|---|---|
| `agents_version` | 无，`{}` | 缓冲字符串 | 真实 `codex --version` 和 `qwen --version`，各最多 20 秒；缺 CLI 或版本不符返回错误，不输出原始 CLI 内容 |

| 开放接口 | 用途 |
|---|---|
| `GET /commands`、`POST /commands/agents_version` | 发现/执行版本检查 |
| `POST /v1/agents/sessions` | 创建会话；`adapter` 支持 `codex`、`qwen-code`，默认 Codex |
| `GET /v1/agents/sessions`、`GET /v1/agents/sessions/{id}` | 列表/重连 |
| `POST /v1/agents/sessions/{id}/events` | 消息入队 |
| `GET /v1/agents/sessions/{id}/items` | 轮询输出 |
| `GET /v1/agents/runtimes` | 检查声明、实现及已安装的运行时 |

会话记录和输出在服务进程内保存，重启后丢失。删除/取消/更新/SSE，以及通用 shell/
文件接口均不在 allowlist 中。销毁自己创建的沙箱可结束其中的服务及资源。

## 配置

| 名称 | 必需 | 用途 |
|---|---|---|
| `ABX_SERVER_TOKEN` | 对外暴露时建议 | 服务端认证，清单中为空 |
| `OPENAI_API_KEY` | 兼容模型调用需要 | Qwen 及兼容 Codex 配置的模型凭据，清单中为空 |
| `CODEX_API_KEY` | Codex 可选替代项 | 清单中为空；实际支持取决于上游及提供方配置 |
| `OPENAI_BASE_URL`、`OPENAI_MODEL` | 取决于提供方 | Qwen 兼容端点和模型配置 |
| `CODEX_HOME` | 否 | Codex 状态目录，默认 `/home/user/.codex` |
| `WORKSPACE` | 否 | `/home/user/workspace`；会话请求应显式指定目标目录 |
| `ABX_SERVER_POLICY_FILE` | 镜像已设置 | 随附策略文件路径；canonical start_cmd 还显式传入 `--policy` |

修改策略会改变 HTTP 接口范围；本模板契约基于随附 allowlist。
`E2E_RUN_LLM=0` 仅控制测试，不修改生产 PATH，也不安装 fixture。

## 资源

2 vCPU、4096 MB 内存、端口 9000。Express rootfs 约 10 GB。
尚未测量模型/工具任务的内存和时延，也未声称镜像大小验收。

## 已验证

当前工作流清单尚无项目认可的验收收据。历史验收记录仅证明原输入和原调用路径；参见[工作流验证](../docs/workflows.zh-CN.md)。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

<details>
<summary>较早检查点的历史说明（当前 steps 结果见上表）</summary>

2026-10-16，已审阅的实际 CI 镜像通过自有 Express/Qwen SDK 编码切片：真实
`qwen3.8-flash` 会话、已有源码修改、原测试字节不变、精确产物/报告、完整 unittest
模块及六个独立用例。八项清理标志全部通过，随后五项独立只读回查通过，详见
[镜像/SDK 证据](./evidence/qwen-image-sdk-2026-10-16.json)及
[严格回查](./evidence/qwen-image-sdk-strict-readback-2026-10-16.json)。

镜像源提交为 `a361f49`，官方 artifact12026073735；宿主验证器运行冻结的 `1f975ff`。
两者的 commands、policy、Dockerfile、YAML 字节相同，没有覆盖镜像内源码。
这是实际镜像注册/SDK/模型证据；完整本地 `abx template deploy` 包装链尚未执行，
因此正式 `tested_on` 仍为空。该套件未验证 Codex 编码或其他提供方。
fixture 协议测试和禁用模型的 HTTP 检查分别记录。

</details>

## 二次开发

保持 Dockerfile、commands.py、smoke 和 fixture 的固定版本一致。在仓库根目录运行：

```bash
python -m pytest --import-mode=importlib -q agents-cli/test_protocol.py
python scripts/check_template.py agents-cli
python scripts/run_local_e2e.py
```

协议测试仅给自己的子进程显式设置 `e2e-bin` PATH，覆盖两种启动方式、认证、关闭接口
及每个 adapter 的两轮任务。Dockerfile 不复制这些 fixture。默认 e2e 要求真实 CLI，
不提交模型任务。设置 `E2E_REQUIRE_LLM=1` 或 `E2E_RUN_LLM=1` 时仍退出非零，并提示运行
`e2e_sdk.py`，不会信任外部回执或任意 verifier hook。无网络负控可运行
`python -m pytest --import-mode=importlib -q agents-cli/test_sdk_verifier.py`；它们与实际
模型/提供方验收分别记录。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py agents-cli`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)和
[设计](../docs/design/agents-cli.md)。工作关联 [Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25)。

## 问题反馈

模板和策略集成：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
运行时/API：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。上游 CLI 保留各自许可证。

### 2026-10-20完整 step 检查点：模板2.0.1

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154625Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，18 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
