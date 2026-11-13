# _skeleton

新模板的骨架。复制这个目录，再换掉命令和元数据。它不是目录里的一个模板条目。

本分支模板使用 YAML v1，需要匹配的开发构建；已发布 CLI 0.5.10 不支持此格式。模板属性在 `sandbox.agent.template`；运行默认值在 Dockerfile，私有运行值在创建实例时显式传入。用途和凭据来源见本页配置部分。详情见[配置规范](../docs/template-spec.zh-CN.md)。

## 做什么

在端口 9000 的 `agent-sandbox-server` 上注册一个命名命令 `hello`。命令返回 `Hello, <name>!`。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`。`abx template build` 把 `<region>` 换成 `ALIBABA_CLOUD_REGION_ID` 或 `cn-hangzhou`，把 `<tag>` 换成 `ABX_BASE_IMAGE_TAG` 或 `v0.0.49`。
- 工作目录 `/home/user/app`。运行用户 `user`。
- 基础镜像自带 Python 3.13 和 Node.js 20。
- `abx deploy` 执行模板的 `sandbox.agent.template.startCommand` 启动进程。Dockerfile 在 `USER` 和 `EXPOSE` 之后结束。

## 解决的问题

让一份新模板从已经满足 [docs/template-spec.zh-CN.md](../docs/template-spec.zh-CN.md) 的目录开始，不必各自发明布局、服务契约和 README 章节。

## 快速开始（CLI）

`abx deploy` 只准备模板。下载本目录源码后，从该目录执行下面的部署，再将 `<prepared-template-id>` 改成返回的模板 ID，运行 `run.py` 创建实例并显式启动业务服务。脚本只传入本页列出的运行配置，自动生成并将应用令牌保存在本地 `.sandbox-session.json`（仅当前用户可读）；不会打印令牌。已有会话文件不会被覆盖，可用 `--session` 选择新文件。


先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；将该 ID 填入下面的 `ABX_SANDBOX_ID`。

```bash
export ABX_PROVIDER=alicloud-express
abx deploy ./_skeleton --yes
python3 -m pip install "agent-sandbox-client==0.4.0a7"
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command run "$ABX_SANDBOX_ID" hello --json-args '{"name": "Express"}'
```

`deploy` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

在虚拟环境安装 `agent-sandbox-client==0.4.0a7`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

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

资源配置改 `template.yaml` 的 `sandbox.agent.template`；镜像默认值改 Dockerfile。运行时值从当前进程环境传给 `run.py`，允许的名称直接列在脚本 `RUNTIME_ENV_NAMES` 中。空值不会作为秘密写入镜像。业务启动命令在 `run.py`；不在模板快照阶段启动带动态认证的服务。外部 SDK/HTTP 客户端可从私有 `.sandbox-session.json` 读取 `application_token`，或复用显式设置的 `ABX_SERVER_TOKEN`。

| 名称 | 必填 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 自动生成 | run.py 自动生成，或显式提供；外部客户端从私有会话文件读取。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地执行 `python3 commands.py` 时 `start()` 监听的端口。 |

密钥在命名服务启动前传入；仅在提供方实际使用创建环境启动服务时采用创建时注入。参考[运行环境](../docs/runtime-environment.zh-CN.md)。不要写进镜像、Dockerfile 或日志。

## 资源

| 资源 | 值 |
|---|---|
| cpu | 2 vCPU |
| memory | 2048 MB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs，极速版大约 10G |

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
