# polyglot-toolchain

[English](README.md)

## 做什么

在一个非 root 沙箱中运行 Go 1.25.14、Rust/Cargo 1.90.0 和 Eclipse Temurin JDK 21.0.12.1+1。`toolchain_smoke` 分别编译并运行三个语言的真实程序，结束后删除本次源文件、二进制和 Go 缓存。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云 FC base v0.0.49，generation 2，2 vCPU / 2048 MB，9000 端口运行 agent-sandbox-server。[toolchains.json](toolchains.json) 固定 x86_64/aarch64 官方下载地址及 SHA256。安装独立 rustc、标准库和 Cargo 组件，不安装多版本管理器；GOTOOLCHAIN=local 禁止自动下载其他 Go 版本，GCC 提供链接器。安装后实际根文件系统已用空间超过 8 GiB 即失败。

## 解决的问题

让编码 Agent 直接编译 Go、Rust 和 Java 项目，无需在模型执行期间安装编译器。无需模型密钥；编译检查完全本地运行。用户项目下载第三方依赖由调用者控制。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//polyglot-toolchain --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" toolchain_smoke --json-args '{}'
```

编译并运行 Go、Rust、Java 示例，返回 `go: GO_OK`、`rust: RUST_OK`、`java: JAVA_OK` 和 `cleanup_verified: true`。

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
            result = await client.commands.run('toolchain_smoke')
            print(result)
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/toolchain_smoke`

```json
{}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| 命令 | 参数 | 返回值 |
| --- | --- | --- |
| toolchain_versions | 无 | 实际版本、磁盘与 non_root 对象 |
| toolchain_smoke | 无 | go/rust/java/cleanup_verified 对象 |

两个命令均无参数。`toolchain_versions() -> dict` 返回实际版本、根文件系统已用和可用字节、非 root 状态；本地缺少编译器时对应值为 null。`toolchain_smoke() -> dict` 要求所有编译器可用，执行 go build、rustc、javac 及生成的程序，必须得到 `{go: GO_OK, rust: RUST_OK, java: JAVA_OK, cleanup_verified: true}`。每个可信子进程最多 90 秒，清理自己创建的进程组。不接受调用者的程序或 shell 字符串。

## 配置

无需模型密钥。`ABX_SERVER_TOKEN` 在 manifest 中保留空值占位，通过服务进程环境注入实际值。`JAVA_HOME=/opt/toolchains/java`，`GOTOOLCHAIN=local`；镜像 PATH 只选择已固定工具链。编译检查独占本次 Go 缓存并在结束后删除。

原生子进程仅继承 PATH/HOME/JAVA_HOME/TMPDIR，另固定语言环境与 GOTOOLCHAIN=local；不继承云端、模型、服务端凭据或注入的编译器/加载器选项。输出每路限制 256 KiB，每条命令时限 90 秒并清理自有进程组。

响应中的旧字段名 `rootfs_used_bytes`、`rootfs_free_bytes` 是可见文件系统的 statvfs 容量计数，可能包含共享底层存储；它们不是镜像层大小，也不能证明 8 GiB 镜像预算通过。安装器单独使用 `du -sx` 检查该预算。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2 vCPU、2048 MB、端口 9000。安装器在实际可见根文件系统已用空间超过 8 GiB 时拒绝。运行用户为非 root，无需 KVM、Docker 或额外特权。每个工具子进程最多 90 秒；成功响应前删除本次临时源文件、二进制和缓存。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/polyglot-toolchain.md)。

## 问题反馈

CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，本模板由 [Issue 62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62) 跟踪；SDK 问题提交到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板：Apache-2.0。Go：BSD-3-Clause 及附带声明。Rust：MIT OR Apache-2.0 及第三方声明。Temurin/OpenJDK：GPL-2.0 WITH Classpath-exception-2.0 及上游 legal 声明。安装后保留各发行版原始 LICENSE/COPYRIGHT/legal 文件。参阅 [Go](https://go.dev/LICENSE)、[Rust](https://github.com/rust-lang/rust/tree/1.90.0)、[Temurin](https://github.com/adoptium/temurin21-binaries/releases)。
