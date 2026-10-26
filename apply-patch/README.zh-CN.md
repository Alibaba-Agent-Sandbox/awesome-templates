# apply-patch

[English](README.md)

## 做什么

执行官方 Codex 的 *** Begin Patch 方言，支持新增、更新、移动和删除。补丁通过私有临时文件进入原生二进制 stdin，不经过 shell 或命令行参数。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云 FC base v0.0.49，generation2，非 root user。`npm ci --ignore-scripts` 依据 [package-lock.json](package-lock.json) 的完整性值安装 @openai/codex0.162.1 和对应架构的官方原生包。版本检查后用 apply_patch argv0 调用同一个原生二进制。对应发布 tag 的源码提交为 [092d3acd](https://github.com/openai/codex/tree/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d)。本模板使用官方预编译包，不宣称本地重新编译该提交。

## 解决的问题

为编码 Agent 提供真实 Codex 补丁工具，不需要模型账号、Rust 编译环境、Docker 或 KVM。支持 Linux x86_64/aarch64。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//apply-patch --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" apply_patch --json-args '{"patch_text":"*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n"}'
```

创建 `hello.txt`；检查 `exit_code == 0` 和实际文件。

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
            result = await client.commands.run('apply_patch', patch_text='*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n')
            print(result)
            Path('hello.txt').write_bytes(await sb.files.read_bytes('/home/user/app/hello.txt'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/apply_patch`

```json
{
  "patch_text": "*** Begin Patch\n*** Add File: hello.txt\n+Hello from a patch\n*** End Patch\n"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| apply_patch | patch_text: str required, nonempty UTF-8 up to256KiB; cwd: str optional empty=WORKSPACE, existing subdirectory | {stdout: str, stderr: str, exit_code: int} from actual native parser |
| apply_patch_version | none | actual native `codex-cli 0.162.1` |
| apply_patch_smoke | none | APPLY_PATCH_OK only after real add/update/move/delete/literal bytes and owned cleanup |

非零上游结果以非零 exit_code 返回，HTTP200 只表示命令完成，不表示补丁成功。缺失或未声明参数为400，未知命令404。SDK 会将 JSON 标量转成声明的字符串；无效补丁仍由原生解析器拒绝。所有文件路径和移动目标必须相对于选定 cwd，拒绝绝对路径、..、反斜杠与现存符号链接。整个补丁先检查路径。上游失败可能留下工作区内部分改动；操作不保证事务。

## 配置

无需模型密钥。WORKSPACE 默认 /home/user/app；ABX_SERVER_TOKEN 为空占位符，应在服务进程注入。参阅[运行环境](../docs/runtime-environment.md)。原生补丁进程只继承 PATH 和 LANG，不获得模型或云密钥。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx download "$SANDBOX_ID" /home/user/app/hello.txt ./hello.txt
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU、2048MB、9000端口。每次补丁最多30秒，每个输出流最多256KiB，清理自建进程组后才回收父进程。临时补丁文件自动关闭；补丁修改的用户文件由调用者管理。预检不是防御同一用户并发改名/符号链接竞态的系统隔离边界。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/apply-patch.md)。

## 问题反馈

[模板 Issue60](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/60)；CLI 问题：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)；SDK 问题：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板与 Codex：Apache-2.0。保留源码固定提交的 [upstream-LICENSE](upstream-LICENSE)，并保留官方 npm 原生包的元数据和通知。
