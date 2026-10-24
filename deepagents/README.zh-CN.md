# DeepAgents

[English](README.md).

## 做什么

运行真实DeepAgents0.7.25本地文件/shell后端及显式兼容OpenAI聊天模型。默认不开放工具；allow_tools=true仅启用ls/read_file/write_file/edit_file/glob/grep/execute/delete八项。关闭通用及显式子Agent，工具中没有task/委派。

## 技术栈

阿里云FC、generation2、非root user、SDK固定e2cb27e。[requirements.lock](requirements.lock)固定全部解析依赖及SHA256，包括[DeepAgents0.7.25](https://pypi.org/project/deepagents/0.7.25/)与langchain-openai1.7.2。由[requirements.in](requirements.in)通过uv0.11.28/Python3.13生成；镜像安装校验哈希并执行pip check。无远程E2B/OpenSandbox后端或模型权重。

## 解决的问题

让真实LangChain Deep Agent在自有沙箱中执行文件/shell操作，不额外创建远程沙箱。采用已验证Python API短驱动，不假设存在控制台入口。每次独立进程、模型、profile及HOME/数据，保留调用者状态。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./deepagents --workflow application --yes
abx run <sandbox-id> deepagents_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('deepagents_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/deepagents_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.7.25"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| deepagents_version | none | actual installed0.7.25 |
| deepagents_setup_check | none | installed/version/api_key_set/base_url_set/model_set flags; read-only |
| deepagents | task:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

实际[驱动](worker.py)显式构造ChatOpenAI(use_responses_api=False)、LocalShellBackend(inherit_env=False)，不传自定义或子Agent，GeneralPurposeSubagentProfile(enabled=False)。默认排除八项工具。上游profile注册会累加排除集合，因此每次使用新进程；许可工具也不能启用委派。任务/模型配置仅通过私有文件stdin进入。

图递归上限40表示图步骤，不等于40次模型调用。单模型请求60秒、零重试、最多8192输出token；单shell期限min(command_timeout,120)、原生shell输出100000字节为捕获后截断，不是峰值内存限制；外层期限1..1800秒及每路输出256KiB。原生非零码保留。超时/输出溢出500，普通结构化非零结果仍为HTTP200。返回替换配置密钥和地址完整值，项目输出仍可能私密。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| DEEPAGENTS_API_KEY | model calls | empty | explicit compatible-provider credential |
| DEEPAGENTS_BASE_URL | model calls | empty | HTTP(S), no userinfo/query/fragment |
| DEEPAGENTS_MODEL | model calls | empty | explicit model identifier |
| DEEPAGENTS_PYTHON | no | /opt/deepagents/bin/python | exact native dependency environment, version checked |
| WORKSPACE | no | /home/user/app | existing owned project directory |
| ABX_SERVER_TOKEN | 是 | 空 | application 工作流启动前必须导出独立应用令牌；与模型及网关凭据分开 |

显式模型配置保留在私有stdin，不作为环境传入生成的shell。运行时仅PATH/可选CA、私有HOME/XDG、关闭LangSmith追踪；LocalShellBackend只接收PATH/HOME/locale及随机非秘密进程归属标记，不继承模型/云/GitHub/服务密钥。不加载skills/memory/profile文件。虚拟文件路径映射至cwd，但shell仍有沙箱用户全部权限，该映射不是shell隔离边界。

## 资源

2vCPU/2048MB，服务9000及可选显式9010；CPU Linux Python3.13，依赖虚拟环境/opt/deepagents，镜像8GiB根文件系统门禁。任务256KiB，每路输出256KiB，期限1..1800秒另加有限进程组/身份固定子进程清理。每次删除私有配置/会话，项目修改由调用者清理；同用户恶意代码或服务被中断时仍以销毁自有沙箱为最终边界。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

python -m venv <new-prefix>后，用<new-prefix>/bin/python -m pip install --require-hashes -r deepagents/requirements.lock及pip check恢复。DEEPAGENTS_PYTHON指向虚拟环境Python，保留该路径，不解析其可执行文件符号链接。运行python -m pytest -q deepagents/test_commands.py deepagents/test_controller.py。真实DeepAgents配合人工HTTP/写文件工具及固定进程夹具，不在操作者主机运行真实模型生成命令。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py deepagents --output /tmp/deepagents-steps仅准备；python scripts/run_steps_e2e.py deepagents --timeout 1200实际执行。严格模型测试设置E2E_REQUIRE_LLM=1/E2E_REQUIRE_CLI=1。生成步骤或静态标记不是验收通过。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/deepagents.md)，保持双语、依赖哈希、上游声明及不可变验证记录一致。

## 问题反馈

[Issue67](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/67)；模板[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，客户端/服务[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装代码为[Apache-2.0](../LICENSE)。DeepAgents及langchain-openai为MIT，保留[DeepAgents原许可](upstream-LICENSE)与[集成库原许可](langchain-openai-LICENSE)。其余哈希固定依赖按各自许可证保留pip安装声明，不能统一重标Apache-2.0。

### 当前平台 step 验收

后续[当前版本真实 step 回执](evidence/express-2026-10-20T141151Z.json)及[完整外部 HTTP 结果](evidence/verification-steps-2026-10-20T141151Z.json)已通过：官方 READY、真实 Python SDK 创建和 CLI/SDK smoke，耗时 586.639 秒；9 HTTP PASS / 0 FAIL / 1 explicit model SKIP。自有沙箱、模板和临时私有缓存已独立确认清理。此前失败记录保留；本次未运行模型，既有镜像／模型回执保持原范围。
