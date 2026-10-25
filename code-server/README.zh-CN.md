# code-server

## 做什么

在沙箱里运行固定版 code-server 浏览器 IDE。必须密码认证，支持独立启动、状态和停止；配置、用户数据和扩展目录均隔离，不修改调用者原有 IDE 配置。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

阿里云 FC base v0.0.49；官方 code-server4.141.0 Linux x86_64/aarch64 独立包，包含上游 Node/VS Code 运行时。[assets.json](assets.json) 固定下载地址、准确字节数和官方 SHA256。保留包内许可证。服务端 SDK 固定提交 e2cb27e；generation2，非 root user。

## 解决的问题

给需要浏览器编辑工作区的用户提供真实 VS Code 界面，无需本地 Docker、KVM、桌面显示器或模型密钥。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./code-server --yes
abx run <sandbox-id> code_server_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('code_server_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/code_server_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "4.141.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| code_server_version | none | actual installed version string |
| code_server_start | password: str optional empty=server CODE_SERVER_PASSWORD; port: int=8443,1024..65535 excluding9000; cwd: str empty=WORKSPACE,existing workspace directory; timeout_s: int=60,1..120 | {port,running:true,auth:password} after actual health |
| code_server_status | none | {running:false}, or {running:true,port,auth:password} |
| code_server_stop | none | {running:false} only after owned processes exit, kernel listener absence and private-state cleanup |
| code_server_self_test | none; existing owned IDE must be stopped | CODE_SERVER_OK after real password rejection/login/workbench and cleanup |

密码必须12..256个 UTF-8 字节且不含 NUL。启动已占用端口或重复启动均拒绝；停止不会按进程名批量杀服务。异常启动/停止不发布成功状态。上游子进程继承本次随机归属标识，使用 Linux pidfd 固定身份再清理；退出后回查内核监听表。

## 配置

保留上游 TLS 校验的 SDK 本机预览见[操作指南](../docs/preview-proxy.zh-CN.md)。控制器明确区分直接域名和 sdk-local 两种结果。


WORKSPACE 默认 /home/user/app。CODE_SERVER_PASSWORD、ABX_SERVER_TOKEN 都是空占位符；前者也可逐次传 password 参数，后者只保护9000命令 API，不替代8443的 IDE 密码。预热服务的环境设置见[运行环境](../docs/runtime-environment.md)。配置文件权限0600，私有目录0700；不把云或模型密钥传入 IDE 进程。服务端关闭更新检查与遥测。

## 资源

2vCPU、2048MB；9000 为命令 API，8443 为 IDE。其他自选端口只保证本地监听，外部暴露需提供方配置。安装时以 du -sx 检查镜像可见根文件系统不超过8GiB；下载最多240秒，单包大小严格匹配。启动最多120秒；检查、子进程与输出均有界。停止清理本次 IDE 的配置/用户数据/扩展，工作区文件保留。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

本地验证可把 install_runtime.py 的 --prefix 指向自己的工具目录；镜像构建显式启用 --check-rootfs，以免把 Docker 宿主机的 statvfs 使用量误当成镜像大小。部署可用[平台 steps](../docs/platform-steps.zh-CN.md)：`python scripts/prepare_steps.py code-server --output /tmp/ide-steps`，真实验收 `python scripts/run_steps_e2e.py code-server`。修改版本时同步资产哈希、实际版本检查与双语文档。WebSocket/终端交互须单独记录，认证页面成功不能推断它们通过。

## 贡献

遵循[贡献规范](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)与[设计](../docs/design/code-server.md)。用真实密码会话、错误密码、跨请求状态和内核/进程回查测试，不接受空端口 TCP 连接成功作为监听证明。

## 问题反馈

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53)；CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)；SDK：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板：Apache-2.0；code-server：MIT。保留官方发行包中的 LICENSE 和第三方声明，包括随包 VS Code/Node 组件的声明。用户安装的扩展各自遵守许可证。上游：[coder/code-server](https://github.com/coder/code-server/releases/tag/v4.141.0)。

### 当前版本新增平台 step 验收

[真实 step](evidence/express-2026-10-20T135352Z.json) 与 [外部 HTTP 尝试](evidence/verification-steps-2026-10-20T135352Z.json)：官方 READY、Python SDK 创建、CLI/SDK 冒烟，HTTP 5 通过、0 失败、0 跳过。本回执模型调用仍为 NOT_RUN；沙箱/模板及同账户私有资产缓存对象/bucket 都独立确认清理后才发布。既有镜像/模型回执保留其独立范围。
