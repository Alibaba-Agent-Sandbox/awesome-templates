# 配置实际承载命名命令的服务进程

[English](runtime-environment.md)

模型和网关配置必须在**命名命令服务进程**导入模板前进入该进程。`template.yaml` 只声明变量名，不提供密钥值。创建请求中的环境变量不能追溯修改一个已经运行的进程。

真实 Express 镜像复查中，`Sandbox.create(envs=...)` 后，预热的 9000 服务未获得全部 Aider 必需配置，模型命令在调用模型前拒绝执行。随后使用同一镜像、原始 `commands.py`，通过 `commands.start(env=...)` 在 9010 启动新服务，SDK、CLI、HTTP 三方均确认三项配置标志为 true，真实编码套件 21 项通过。这是该次提供方与启动方式的实测边界，不表示所有提供方都忽略创建环境变量。

## 现有快速开始示例

模板 README 中创建时注入密钥的示例，适用于提供方确实使用该环境启动命名服务的情况。调用模型前先查看模板的只读 setup 命令。预热服务缺少配置时，使用显式配置的新服务。只把密钥交给本地 HTTP 测试控制器，不会配置远端服务。

## 显式启动新服务

[英文页的完整 Python 示例](runtime-environment.md#explicit-server-process) 使用已安装 Qwen 模板的变量名与只读诊断演示进程 API；上述真实镜像验证用的是 Aider。按具体模板选择配置名，参考[客户端源码安装](python-client-installation.md)。

步骤为：创建自有沙箱；使用 `sb.commands.start("agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py", env=settings, timeout=900)` 启动原镜像中的命名服务；持续消费返回的进程流且不打印原始日志；等待新端口 `/health`；调用 `await sb.run("qwen_setup_check", server_port=9010)` 检查配置；最后在 `finally` 销毁自有沙箱并停止消费流。示例不覆盖源码、不接管其他进程、不修改 `HOME`。服务启动、CLI 或配置检查失败仍是失败。长任务需要足够的进程和沙箱期限，并遵守具体模板的取消契约。

所有调用者必须选中同一个新服务：

```bash
abx run <sandbox-id> qwen_setup_check --server-port 9010
```

HTTP 使用 `sb.network.get_url(9010)`，向 `/commands/qwen_setup_check` POST `{}`，保留提供方要求的网关认证。模型密钥只通过明确选择的进程环境传入，不放进命令参数、提示词、镜像或日志。

## 服务认证是另一层配置

`ABX_SERVER_TOKEN` 在服务启动时读取。后来的创建请求或第二个服务，不能给原有 9000 进程补上认证。如果新服务启动时设置了 bearer token，客户端向该服务发送匹配令牌，例如 `client = await sb.application_client(9010, token=server_token)`；当前服务的 `/health` 不要求 server token；提供方网关仍可能要求自己的凭据。health 成功本身不证明认证或模型配置正确。它与提供方网关凭据、上游模型密钥各自独立。

示例没有改变现有的服务认证默认设置。启动第二个服务不会保护或关闭默认服务。若要求所有服务认证，应在它们启动前配置提供方支持的启动环境，并逐一验证实际开放的服务，不能仅从 `Sandbox.create` 成功推断。

## 验证边界

Aider 验收使用原始镜像命令、显式配置的新服务、真实模型编码、独立测试和自有资源清理读回。它不证明当前统一源码启动验证、其他提供方的环境行为或全部模板的模型能力。[Aider PR](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/88) 分开记录这些结果。当前提供方验证结论需要各自准确输入的门禁与实测回执。
