# _skeleton

新模板的骨架。复制这个目录，再换掉命令和元数据。它不是目录里的一个模板条目。

## 做什么

在端口 9000 的 `agent-sandbox-server` 上注册一个命名命令 `hello`。命令返回 `Hello, <name>!`。

## 技术栈

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template deploy` 把 `<region>` 换成 `ALIBABA_CLOUD_REGION_ID` 或 `cn-hangzhou`，把 `<tag>` 换成 `ABX_BASE_IMAGE_TAG` 或 `v0.0.49`。
- 构建上下文里没有 wheel 时，从 python-sdk 提交 `35da216a300f1e2e84254a1cf4b4a7ea98681505` 安装 `agent-sandbox-server`：`pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40位hex>.tar.gz#subdirectory=server-sdk"`。`abx template deploy` 注入的 wheel 优先。另一个允许的钉是 `agent-sandbox-server==X.Y.Z`，前提是该版本已经在 PyPI 上。2026-10-15 时 `0.3.0` 不在 PyPI。
- 工作目录 `/home/user/app`。运行用户 `user`。
- 基础镜像自带 Python 3.13 和 Node.js 20。
- 平台用 `start_cmd` 启动进程。Dockerfile 在 `USER` 和 `EXPOSE` 之后结束。

## 解决的问题

让一份新模板从已经满足 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md) 的目录开始，不必各自发明布局、服务契约和 README 章节。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

运行配置：以下创建时注入密钥的示例，要求命名服务启动时实际获得这些值。预热服务请先检查模板提供的 setup 标志（如有），再按[显式进程配置](../docs/runtime-environment.zh-CN.md)操作；创建沙箱不会重新配置已运行的服务。

在本仓库检出目录，环境里放好极速版凭证（变量见规范）：

```bash
abx template deploy ./_skeleton -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> hello --arg name=Ada
```

`template.yaml` 里已经写了 `generation`、`start_cmd` 和 `ready_cmd`。当前 main 上的 `abx` 会读这些键。上面的标志把同一组值再写一遍，命令可以单独看懂。

用完后删掉沙箱和模板：

```bash
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

`python3 scripts/express_e2e.py _skeleton` 会做同样的部署、调用 `hello`、只在通过后写证据，并在 `finally` 里删除沙箱和模板。

## 快速开始（Python SDK）

客户端发行名为 `agent-sandbox-client`，导入名为 `agent_sandbox`。配套版本发布前，请按[固定提交的双包安装说明](../docs/python-client-installation.md)安装。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))
    finally:
        await sb.kill()

asyncio.run(main())
```

`await sb.run("hello", name="Ada")` 返回字符串 `Hello, Ada!`。`sb.commands.run` 跑的是 shell，不是这个命名命令。`sb.network.get_url(9000)` 是服务端口的 URL。当前检出的 SDK 已在 [python-sdk#24](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/24) 修复同步类方法；旧提交遇到 TypeError 时请升级或使用异步构造。

## 快速开始（HTTP POST）

使用沙箱端口 9000 的 URL；本地默认 http://127.0.0.1:9000。服务启用了 ABX_SERVER_TOKEN 时才添加认证头。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/hello" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" \
  --data '{"name":"Ada"}'
```

请求体直接包含命名命令参数，不嵌套在 args 中。HTTP 200 的响应为 `{"result":"Hello, Ada!"}`。参数错误为 HTTP 400，认证失败为 401，执行异常为 500；错误响应包含 error 和 type。命令响应在执行完成后整体返回。HTTP 客户端超时不保证取消服务端命令；长任务使用进程 API 管理。

## 命令参考

| Command | Parameters | Returns | Description |
|---|---|---|---|
| hello | `name`：字符串，可选，默认 `World` | 字符串 | 打招呼。 |

`POST /commands/hello`，请求体 `{"name":"Ada"}`，响应 `{"result":"Hello, Ada!"}`。缺少必填参数是 HTTP 400。函数里抛出的异常是 HTTP 500，响应体含 `error` 和 `type`。

## 配置

| 名称 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 空 | 沙箱内设置之后，客户端发送 `Authorization: Bearer`。`template.yaml` 里的值是空字符串。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地执行 `python3 commands.py` 时 `start()` 监听的端口。 |

密钥在命名服务启动前传入；仅在提供方实际使用创建环境启动服务时采用创建时注入。参考[运行环境](../docs/runtime-environment.zh-CN.md)。不要写进镜像、Dockerfile 或日志。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs，极速版大约 10G |

## 已验证

尚未记录任何通过的提供方测试。

## 二次开发

把 `_skeleton` 复制成符合 `^[a-z0-9][a-z0-9-]*$` 的目录名。`template.yaml` 的 `name` 与目录名相同。用真正调用上游程序的命令换掉 `hello`，并在 Dockerfile 里钉住每个安装版本。按 [docs/design/_TEMPLATE.md](../docs/design/_TEMPLATE.md) 写 `docs/design/<name>.md`。在 `awesome-templates.yaml` 加一条。运行 `python3 scripts/check_template.py <dir>`。

## 贡献

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 和 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md)。

## 问题反馈

| 主题 | 仓库 |
|---|---|
| 本模板、规范、检查器 | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| Python SDK 或 `agent-sandbox-server` | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，标题前缀 `[templates]` |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀 `[templates]` |

## 许可证

Apache-2.0，与本仓库相同。见 [LICENSE](../LICENSE)。
