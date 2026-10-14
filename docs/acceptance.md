# 模板开发、上架与验收

一份模板要进 `awesome-templates.yaml` 并且 `status: official`，必须同时满足下面的开发、上架和验收条件。只写 README、或者命令没有真正调用上游 CLI，不能上架。

## 开发

每个可构建模板是一个目录，目录名、`template.yaml` 的 `name`、索引里的 `path` 相同。

目录里要有：

| 文件 | 作用 |
|---|---|
| `template.yaml` | 名字、能力、空的密钥名、资源 |
| `Dockerfile` | `python:3.12-slim`，安装并固定上游 CLI 版本，安装 `agent-sandbox-server` |
| `commands.py` | 使用 `agent_sandbox.server` 的 `@command` 和 `start()` |
| `e2e_test.py` | 对正在运行的 server 做 HTTP 检查 |
| `README.md` | 这个模板是什么、密钥名、怎么跑本地验收 |

`commands.py` 必须走 server SDK。命名命令注册在进程里，不写进 `template.yaml`。命令要调用该产品自己的 CLI，参数和上游非交互模式一致。密钥只从环境变量读取，提示词不能拼进 shell 字符串。

`template.yaml` 的 `env` 里可以出现密钥名，值必须是空字符串。不要把密钥写进镜像。

OpenSandbox 已经发布的沙箱镜像（`code-interpreter`、`code-interpreter-base`、`desktop`、`playwright`、`vscode`）由 SDK 把短名字解析成镜像。不要把这些 Dockerfile 再拷进本仓库。

## 上架

索引条目至少有 `name`、`description`、`repo`、`path`、`tags`、`author`、`capabilities`、`status`。`providers` 可以写，当前 CLI 会忽略它。

`status: official` 只给已经通过下面验收的模板。还在核对安装方式的用 `experimental`，并且不要出现在默认推荐里。

CLI 的 `abx template install` 只在阿里云极速版上构建。其他 provider 要在 README 里写明创建方式：已有模板 id，或 OpenSandbox 镜像名。

## 验收

三条都要过，模板才能标成 official。

1. 本地 server。在仓库根目录执行 `python3 scripts/run_local_e2e.py`。它会启动每个带 `commands.py` 的模板，并强制 `E2E_RUN_LLM=0`。`/health`、`/commands` 和该模板的命名命令必须可被发现。没有模型密钥时，真实模型调用记为 SKIP，不能记为通过。
2. 镜像。`docker build` 成功，并且构建日志里能看到固定版本的上游 CLI。这次构建不在当前 GitHub Actions 里，上架前要在 PR 里留下构建结果。
3. 有密钥的真实调用。提供对应的 API 密钥后，同一份 `e2e_test.py` 把模型调用跑通，输出里能看到约定的标记。没有这条记录，不能把模板写成“已支持该 Agent”。

本地验收通过，只说明 server SDK 接上了。它不代替镜像构建，也不代替云上创建沙箱。

## 不接收的模板

底层还不能跑的场景不要做目录项：

- 需要 Windows 虚拟机的评测，例如 Windows Agent Arena。
- 需要手机或 Android 模拟器的场景。是否支持等到底层决定。
- 需要特权嵌套容器的集群，例如在沙箱里再跑 K3s。
- 只有桌面配置、没有可调用 CLI 的项目。
- 安装方式还没核实的名字。先写在本文件的待定表里，不要建目录。
