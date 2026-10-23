# 使用与验证模板

先阅读本页的安装和调用约定，再查目标模板 README 中的准确命令、参数、运行限制
与示例。[模板规范](template-spec.zh-CN.md)负责开发和验收规则；
[源码运行诊断](express-source-runtime.md)是另一类测试，不能证明镜像部署通过。

## 安装

2026-10-18 查询 `@agent-sandbox/cli`、`agent-sandbox-client` 和
`agent-sandbox-server` 的公开 0.3.0 元数据均返回 HTTP 404。包名不代表已发布。
Python 客户端和服务端须按[固定提交的双包说明](python-client-installation.md)
一起安装。CLI 使用 Node 20 或 22，可从固定源码构建：

```bash
git clone https://github.com/Alibaba-Agent-Sandbox/agent-sandbox.git agent-sandbox-cli
git -C agent-sandbox-cli checkout 850a9bb780c44857630ac7928c2361c7be270921
npm --prefix agent-sandbox-cli ci
npm --prefix agent-sandbox-cli run build
ABX_CLI_ENTRY="$(pwd)/agent-sandbox-cli/dist/bin/abx.js"
abx() { node "$ABX_CLI_ENTRY" "$@"; }
abx --version
```

该 shell 函数通过绝对路径调用构建入口。独立二进制参见 CLI 仓库的
[安装指南](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/binary-installation.md)，
下载前确认目标 release 实际存在。这里的源码提交只是安装基线，不能证明后续
模板、SDK 或 CLI 版本已经验收。

部署前通过安全配置提供凭据。Express 沙箱调用需要 `ABX_SANDBOX_API_KEY`
及对应的 `ABX_SANDBOX_BASE_URL`、`ABX_SANDBOX_DOMAIN`。Docker/ACR 模板部署
还需要可用 Docker daemon、授权的阿里云控制面凭据和 ACR namespace。
不要把密钥放进命令参数、报告或 Issue。

## CLI、SDK 与 HTTP

在模板仓库中、Express 配置完成后部署目标目录，以 `python-hello` 为例：

```bash
abx template deploy ./python-hello -y
abx create <template-id> --detach
abx sandbox command list <sandbox-id>
abx run <sandbox-id> hello --arg name=Ada
```

尖括号内容须替换为上一条命令返回的 ID，不是可直接执行的 shell 语法。
`abx run` 调用注册命令；`abx exec` 是进程/脚本接口。数字和布尔参数使用
`--json-args`。每个模板 README 展示自己的具体调用示例。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

SDK 返回 `result` 的值。将打印的网址设为 `ABX_SERVER_URL`，可直接 POST：

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello"   --header 'Content-Type: application/json' --data '{"name":"Ada"}'
# {"result":"Hello, Ada!"}
```

请求体直接是参数 JSON，不包一层 `args`。`GET /commands` 发现公开命令。
服务端鉴权、厂商凭据和网关鉴权是独立的。Express 的匿名 9000 端口服务不需要
转发 envd token。若配置 `ABX_SERVER_TOKEN`，HTTP 加服务端 token 的 Bearer
头，SDK 使用 `await sb.application_client(9000, token=...)` 并关闭返回的应用客户端。
认证失败不会触发匿名重试。需要网关访问头的厂商还要带上
其文档规定的头。不要把一个厂商的密钥发送给另一个厂商。

缺失/非法参数返回 400，服务端鉴权失败 401，未知命令 404，执行失败 500，
错误体含 `error`、`type`。客户端超时不能证明远端操作已取消；具体执行期限、
进程和清理约定查模板 README。结束后删除本次沙箱及自己拥有的模板：

```bash
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## 验收与厂商

| 证据 | 能证明 | 不能证明 |
|---|---|---|
| 静态检查 | YAML、索引、文档符合规范 | 产品实际可运行 |
| L0 本地 HTTP | 启动服务后的命令断言 | 镜像依赖、云端部署、被跳过的模型调用 |
| L1 真实镜像构建 | 构建和声明的镜像无密钥检查 | 生产 CLI 部署封装或真实云验收 |
| 源码云端运行诊断 | 现有基础沙箱上的准确源码和依赖 | 变更后的 Dockerfile、模板部署 |
| L2 标准部署 | Docker/ACR 部署、READY、新沙箱、外部 CLI/SDK smoke、资源清理 | 未明确执行的全部 HTTP 命令或模型编码 |
| L3 产品/模型 | 记录中的任务和独立验证结果 | 其他源码/版本或上游所有能力 |
| L4 其他厂商 | 实际测试的厂商及工作负载 | 没有配置的其他厂商 |

`tested_on` 与 README 已验证表必须对应当前版本通过的厂商证据。保留历史记录，
但不要把旧版本徽章复制到新代码。镜像 CI 绿色不等于其他层级通过；跳过也不是
通过。现有草稿 PR 继续遵守这些边界。

目录源码提供 Express Dockerfile 工作流。已安装提供方各有自己的能力声明；
能接受镜像 URI 或已有模板 ID，不等于能构建和部署这些 Dockerfile。先读厂商
README，并完成该厂商实际测试，再增加已验证标记。

## 文档与目录归属

- 模板 README：CLI/SDK/HTTP 示例、参数、配置、限制、验收和二次开发。
- `docs/design/<name>.md`：设计理由与可行性。
- `template-spec.md`：开发和验收的规范来源。
- `python-client-installation.md`：唯一的配套源码安装步骤。
- `.agents/`：工程决策与日期化验证，不是用户 API 文档。
- `awesome-templates.yaml`：CLI 和[registry 仓库](https://github.com/Alibaba-Agent-Sandbox/registry)
  消费的模板源目录。

旧的 `registry/index.html`、`registry/catalog.json` 不被 CLI、SDK、正式 registry
聚合或 CI 使用，且包含过时的厂商描述，本次退役。网站 UI 归
[website 仓库](https://github.com/Alibaba-Agent-Sandbox/website)，registry 从源仓库
生成公开目录；不要把这些前端或生成目录再复制回来。

[English](using-templates.md)

本地验收清理会保留 Python 验收源码（包括 `e2e_sdk.py`），仅移除生成产物和缓存。源码应留在工作树中供后续 SDK 验收使用。


## 客户端入口兼容性

自定义命令、provider、会话和 `sb.server` 示例显式导入
`from agent_sandbox.api.sandbox import Sandbox`。这个原生异步入口可用于当前
主分支及标准客户端候选版本，避免根入口切换为同步 `Sandbox` 后误用 await。
标准 `Sandbox` / `AsyncSandbox` 与解释器导入属于另一个契约，见
[SDK47](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47)。

当前极速版使用位置模板参数；本页及模板 README 的示例与上述 CLI 源码提交一致。旧版原生 CLI 的参数不同，应使用对应版本的帮助。

| 操作 | 当前极速版入口 |
| --- | --- |
| 脚本创建 | `abx create <template-id> --detach` |
| Shell | `abx exec --cwd /tmp <sandbox-id> sh -c 'echo hello'` |
| 清理本任务沙箱 | `abx kill <sandbox-id>` |

`template deploy`、命名命令 `abx run`、上传/下载仍为项目扩展。标准 create 不带 `--detach` 会打开 PTY。模板源代码和厂商验收等级不因示例更新而改变。
