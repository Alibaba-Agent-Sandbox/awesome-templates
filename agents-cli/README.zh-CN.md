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

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在本仓库目录中配置提供方构建凭据后运行：

```bash
abx template deploy ./agents-cli -y
abx create --template <template-id> -y
abx run <sandbox-id> agents_version
```

结果为 `codex 0.162.1; qwen-code 0.23.0`。提交模型任务前，在创建沙箱时通过
`--env OPENAI_API_KEY=<compatible-key>` 等参数注入所选上游兼容的凭据及端点/模型配置。
不要把密钥写入镜像或版本控制文件。结束后清理自己创建的资源：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

匹配的软件包发布前，按[配套固定源码说明](../docs/python-client-installation.md)安装
`agent-sandbox-client`。导入名保持 `agent_sandbox`。

```python
import asyncio
from agent_sandbox import Sandbox

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
该策略下通用 SDK 文件/进程操作返回 404。

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
未知/关闭的接口、运行时或会话，500 表示版本检查执行失败。模型执行错误体现在会话及
items 状态中；事件被接收不代表模型成功。HTTP 超时不会自动取消后台任务。

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

尚未记录任何通过的提供方测试。

本地真实 CLI 诊断、HTTP 契约与 fixture 协议测试分别记录，均不能证明镜像部署或真实
模型编码完成。L1/L2 及基于独立产物验证的 L3 仍需通过。

## 二次开发

保持 Dockerfile、commands.py、smoke 和 fixture 的固定版本一致。在仓库根目录运行：

```bash
python -m pytest --import-mode=importlib -q agents-cli/test_protocol.py
python scripts/check_template.py agents-cli
python scripts/run_local_e2e.py
```

协议测试仅给自己的子进程显式设置 `e2e-bin` PATH，覆盖两种启动方式、认证、关闭接口
及每个 adapter 的两轮任务。Dockerfile 不复制这些 fixture。默认 e2e 要求真实 CLI，
不提交模型任务。设置 `E2E_REQUIRE_LLM=1` 或 `E2E_RUN_LLM=1` 时退出非零，因为受限接口
套件尚无带外产物验收器。回复标记不能计作 L3；声称真实编码完成前，必须独立检查
已有源码修改、新建产物及测试结果。

## 贡献

阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)和
[设计](../docs/design/agents-cli.md)。工作关联 [Issue #25](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/25)。

## 问题反馈

模板和策略集成：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
运行时/API：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。上游 CLI 保留各自许可证。
