# polyglot-toolchain

## 做什么

在一个非 root 沙箱中运行 Go 1.25.14、Rust/Cargo 1.90.0 和 Eclipse Temurin JDK 21.0.12.1+1。`toolchain_smoke` 分别编译并运行三个语言的真实程序，结束后删除本次源文件、二进制和 Go 缓存。

## 技术栈

阿里云 FC base v0.0.49，generation 2，2 vCPU / 2048 MB，9000 端口运行 agent-sandbox-server。[toolchains.json](toolchains.json) 固定 x86_64/aarch64 官方下载地址及 SHA256。安装独立 rustc、标准库和 Cargo 组件，不安装多版本管理器；GOTOOLCHAIN=local 禁止自动下载其他 Go 版本，GCC 提供链接器。安装后实际根文件系统已用空间超过 8 GiB 即失败。

## 解决的问题

让编码 Agent 直接编译 Go、Rust 和 Java 项目，无需在模型执行期间安装编译器。无需模型密钥；编译检查完全本地运行。用户项目下载第三方依赖由调用者控制。

## 快速开始（CLI）

Use the native CLI syntax (`abx create --help` lists `--template`):

```bash
abx template deploy ./polyglot-toolchain -y
abx create --template <template-id> --timeout 300 -y
abx run <sandbox-id> toolchain_versions
abx run <sandbox-id> toolchain_smoke
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

For the standard CLI entry and paired client installation, see [using templates](../docs/using-templates.md).


## 快速开始（Python SDK）

Install the [paired `agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("toolchain_versions"))
        print(await sb.run("toolchain_smoke"))
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```


## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| toolchain_versions | none | version/disk/non_root object |
| toolchain_smoke | none | go/rust/java/cleanup_verified object |

两个命令均无参数。`toolchain_versions() -> dict` 返回实际版本、根文件系统已用和可用字节、非 root 状态；本地缺少编译器时对应值为 null。`toolchain_smoke() -> dict` 要求所有编译器可用，执行 go build、rustc、javac 及生成的程序，必须得到 `{go: GO_OK, rust: RUST_OK, java: JAVA_OK, cleanup_verified: true}`。每个可信子进程最多 90 秒，清理自己创建的进程组。不接受调用者的程序或 shell 字符串。

## 二次开发

修改版本时同步更新官方地址和哈希，并保留许可证。参阅 [steps 操作](../docs/platform-steps.zh-CN.md)：`python scripts/prepare_steps.py polyglot-toolchain --output /tmp/toolchain-steps` 仅生成文件。极速版实测：`python scripts/run_steps_e2e.py polyglot-toolchain --timeout 1800`；Dockerfile 路径：`python scripts/express_e2e.py polyglot-toolchain`。`python scripts/run_local_e2e.py` 在本机缺少工具时明确跳过编译；镜像验证必须真实编译三个语言，本机跳过不能证明镜像通过。

## 贡献

遵循 [贡献规范](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)及[设计](../docs/design/polyglot-toolchain.md)。同步双语说明，保留历史证据。

## 问题反馈

CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，本模板由 [Issue 62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62) 跟踪；SDK 问题提交到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 已验证

尚未记录任何通过的提供方测试。

## 许可证

模板：Apache-2.0。Go：BSD-3-Clause 及附带声明。Rust：MIT OR Apache-2.0 及第三方声明。Temurin/OpenJDK：GPL-2.0 WITH Classpath-exception-2.0 及上游 legal 声明。安装后保留各发行版原始 LICENSE/COPYRIGHT/legal 文件。参阅 [Go](https://go.dev/LICENSE)、[Rust](https://github.com/rust-lang/rust/tree/1.90.0)、[Temurin](https://github.com/adoptium/temurin21-binaries/releases)。

## 快速开始（HTTP POST）

Response: `{"result":{"go":"GO_OK","rust":"RUST_OK","java":"JAVA_OK","cleanup_verified":true}}`.

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' \
  -d '{}' '<sandbox-port-9000-url>/commands/toolchain_smoke'
```

The server token is set in the named-command server process. See [runtime environment](../docs/runtime-environment.md).

## 配置

No model key. `ABX_SERVER_TOKEN` is an optional empty manifest placeholder; inject the value into the server process. `JAVA_HOME=/opt/toolchains/java`, `GOTOOLCHAIN=local`; image PATH selects only the pinned toolchains. The smoke owns its Go build cache and removes it.

## 资源

2 vCPU, 2048 MB, port 9000. Installer rejects actual used rootfs above 8 GiB. Non-root runtime; no KVM, Docker or additional capabilities. Each tool subprocess deadline is 90 seconds. Temporary source/binary/cache artifacts are deleted before a successful response.

CLI defects: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

版本1.0.1显式修复运行工作区归属。原生子进程仅继承 PATH/HOME/JAVA_HOME/TMPDIR，另固定语言环境与 GOTOOLCHAIN=local；不继承云端、模型、服务端凭据或注入的编译器/加载器选项。并发读取输出，每路限制256KiB，操作时限90秒并清理自有进程组。此前1.0.0尝试不能证明新版本通过。

响应中的旧字段名 `rootfs_used_bytes`、`rootfs_free_bytes` 是可见文件系统的 statvfs 容量计数，可能包含共享底层存储；它们不是镜像层大小，也不能证明8GiB镜像预算通过。安装器单独使用 `du -sx` 检查该预算。
