# polyglot-toolchain

## 做什么

在一个非 root 沙箱中运行 Go 1.25.14、Rust/Cargo 1.90.0 和 Eclipse Temurin JDK 21.0.12.1+1。`toolchain_smoke` 分别编译并运行三个语言的真实程序，结束后删除本次源文件、二进制和 Go 缓存。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

阿里云 FC base v0.0.49，generation 2，2 vCPU / 2048 MB，9000 端口运行 agent-sandbox-server。[toolchains.json](toolchains.json) 固定 x86_64/aarch64 官方下载地址及 SHA256。安装独立 rustc、标准库和 Cargo 组件，不安装多版本管理器；GOTOOLCHAIN=local 禁止自动下载其他 Go 版本，GCC 提供链接器。安装后实际根文件系统已用空间超过 8 GiB 即失败。

## 解决的问题

让编码 Agent 直接编译 Go、Rust 和 Java 项目，无需在模型执行期间安装编译器。无需模型密钥；编译检查完全本地运行。用户项目下载第三方依赖由调用者控制。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./polyglot-toolchain --yes
abx run <sandbox-id> toolchain_smoke --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('toolchain_smoke'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/toolchain_smoke`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"go": "GO_OK", "rust": "RUST_OK", "java": "JAVA_OK", "cleanup_verified": true}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回值 |
| --- | --- | --- |
| toolchain_versions | 无 | 实际版本、磁盘与 non_root 对象 |
| toolchain_smoke | 无 | go/rust/java/cleanup_verified 对象 |

两个命令均无参数。`toolchain_versions() -> dict` 返回实际版本、根文件系统已用和可用字节、非 root 状态；本地缺少编译器时对应值为 null。`toolchain_smoke() -> dict` 要求所有编译器可用，执行 go build、rustc、javac 及生成的程序，必须得到 `{go: GO_OK, rust: RUST_OK, java: JAVA_OK, cleanup_verified: true}`。每个可信子进程最多 90 秒，清理自己创建的进程组。不接受调用者的程序或 shell 字符串。

## 配置

无需模型密钥。`ABX_SERVER_TOKEN` 在 manifest 中保留空值占位，通过服务进程环境注入实际值。`JAVA_HOME=/opt/toolchains/java`，`GOTOOLCHAIN=local`；镜像 PATH 只选择已固定工具链。编译检查独占本次 Go 缓存并在结束后删除。

版本 1.0.1 显式修复运行工作区归属。原生子进程仅继承 PATH/HOME/JAVA_HOME/TMPDIR，另固定语言环境与 GOTOOLCHAIN=local；不继承云端、模型、服务端凭据或注入的编译器/加载器选项。并发读取输出，每路限制 256 KiB，操作时限 90 秒并清理自有进程组。此前 1.0.0 尝试不能证明新版本通过。

响应中的旧字段名 `rootfs_used_bytes`、`rootfs_free_bytes` 是可见文件系统的 statvfs 容量计数，可能包含共享底层存储；它们不是镜像层大小，也不能证明 8 GiB 镜像预算通过。安装器单独使用 `du -sx` 检查该预算。

## 资源

2 vCPU、2048 MB、端口 9000。安装器在实际可见根文件系统已用空间超过 8 GiB 时拒绝。运行用户为非 root，无需 KVM、Docker 或额外特权。每个工具子进程最多 90 秒；成功响应前删除本次临时源文件、二进制和缓存。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

修改版本时同步更新官方地址和哈希，并保留许可证。参阅 [steps 操作](../docs/platform-steps.zh-CN.md)：`python scripts/prepare_steps.py polyglot-toolchain --output /tmp/toolchain-steps` 仅生成文件。极速版实测：`python scripts/run_steps_e2e.py polyglot-toolchain --timeout 1800`；Dockerfile 路径：`python scripts/public_launch_e2e.py polyglot-toolchain --provider alicloud-express --application-controller`。`python scripts/run_local_e2e.py` 在本机缺少工具时明确跳过编译；镜像验证必须真实编译三个语言，本机跳过不能证明镜像通过。

## 贡献

遵循 [贡献规范](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)及[设计](../docs/design/polyglot-toolchain.md)。同步双语说明，保留历史证据。

## 问题反馈

CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，本模板由 [Issue 62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62) 跟踪；SDK 问题提交到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板：Apache-2.0。Go：BSD-3-Clause 及附带声明。Rust：MIT OR Apache-2.0 及第三方声明。Temurin/OpenJDK：GPL-2.0 WITH Classpath-exception-2.0 及上游 legal 声明。安装后保留各发行版原始 LICENSE/COPYRIGHT/legal 文件。参阅 [Go](https://go.dev/LICENSE)、[Rust](https://github.com/rust-lang/rust/tree/1.90.0)、[Temurin](https://github.com/adoptium/temurin21-binaries/releases)。

### 当前版本新增平台 step 验收

[真实 step](evidence/express-2026-10-20T135358Z.json) 与 [外部 HTTP 尝试](evidence/verification-steps-2026-10-20T135358Z.json)：官方 READY、Python SDK 创建、CLI/SDK 冒烟，HTTP 1 通过、0 失败、0 跳过。本回执模型调用仍为 NOT_RUN；沙箱/模板及同账户私有资产缓存对象/bucket 都独立确认清理后才发布。既有镜像/模型回执保留其独立范围。
