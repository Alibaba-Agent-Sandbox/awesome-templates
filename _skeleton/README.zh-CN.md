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

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./_skeleton --workflow application --yes
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

| Command | Parameters | Returns | Description |
|---|---|---|---|
| hello | `name`：字符串，可选，默认 `World` | 字符串 | 打招呼。 |

`POST /commands/hello`，请求体 `{"name":"Ada"}`，响应 `{"result":"Hello, Ada!"}`。缺少必填参数是 HTTP 400。函数里抛出的异常是 HTTP 500，响应体含 `error` 和 `type`。

## 配置

| 名称 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 是 | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |
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

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

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
