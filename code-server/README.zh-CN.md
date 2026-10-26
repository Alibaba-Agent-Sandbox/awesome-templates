# code-server

[English](README.md)

## 做什么

在沙箱里运行固定版 code-server 浏览器 IDE。必须密码认证，支持独立启动、状态和停止；配置、用户数据和扩展目录均隔离，不修改调用者原有 IDE 配置。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云 FC base v0.0.49；官方 code-server4.141.0 Linux x86_64/aarch64 独立包，包含上游 Node/VS Code 运行时。[assets.json](assets.json) 固定下载地址、准确字节数和官方 SHA256。保留包内许可证。已发布服务端包；generation2，非 root user。

## 解决的问题

给需要浏览器编辑工作区的用户提供真实 VS Code 界面，无需本地 Docker、KVM、桌面显示器或模型密钥。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

将口令占位符换成至少 12 字节的独立口令。该口令不替代 `ABX_SERVER_TOKEN`。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export CODE_SERVER_PASSWORD='<choose-a-long-unique-password>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//code-server --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" code_server_start --json-args '{"port":8443,"timeout_s":60}'
```

返回 `running: true`、`port: 8443`、`auth: password`。解析 8443 端口地址后，使用 `CODE_SERVER_PASSWORD` 登录 IDE。

IDE 的入口不是 9000 命令 API。用 SDK `await sb.network.resolve(8443)` 获取访问地址和网关头，按[预览指南](../docs/preview-proxy.md)打开；不要丢失网关认证。扩展市场、Git 远程仓库等账号需单独登录，不继承本机凭据。IDE 文件根为 `/home/user/app`，停止 IDE 后文件仍在，删除沙箱后消失。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

在完成上述 CLI 启动、设置 `SANDBOX_ID` 后，将以下保存为 `use_template.py`，执行 `python3 use_template.py`。它连接同一实例，不另建沙箱。对于需要输入的示例，先在本机准备上面的文件。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('code_server_start', port=8443, timeout_s=60)
            print(result)
        finally:
            try:
                await client.commands.run('code_server_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/code_server_start`

```json
{
  "port": 8443,
  "timeout_s": 60
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/code_server_stop` with `{}`.

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

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx run "$SANDBOX_ID" code_server_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU、2048MB；9000 为命令 API，8443 为 IDE。其他自选端口只保证本地监听，外部暴露需提供方配置。安装时以 du -sx 检查镜像可见根文件系统不超过8GiB；下载最多240秒，单包大小严格匹配。启动最多120秒；检查、子进程与输出均有界。停止清理本次 IDE 的配置/用户数据/扩展，工作区文件保留。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/code-server.md)。

## 问题反馈

[Issue53](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/53)；CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)；SDK：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板：Apache-2.0；code-server：MIT。保留官方发行包中的 LICENSE 和第三方声明，包括随包 VS Code/Node 组件的声明。用户安装的扩展各自遵守许可证。上游：[coder/code-server](https://github.com/coder/code-server/releases/tag/v4.141.0)。
