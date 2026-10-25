# Crush

[English](README.md).

## 做什么

运行官方原生Crush0.98.1，显式配置兼容OpenAI的提供方。默认无工具；allow_tools=true仅启用bash/edit/multiedit/view/write/ls/glob/grep八项。禁用子Agent、MCP、联网抓取、后台任务及LSP工具。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a3`，由 Dockerfile 直接安装。

阿里云FC generation2 CPU、非root user、已发布服务端包。[assets.json](assets.json)固定官方GNU Linux x86_64/aarch64下载长度与SHA256，源码[8b1824282eccc78cc62c188c245cf375230a18ce](https://github.com/charmbracelet/crush/tree/8b1824282eccc78cc62c188c245cf375230a18ce)。arm64固定版本不等于已验证运行。

## 解决的问题

在自有沙箱通过真实终端Agent编辑项目，每次使用独立配置和数据。本模板仅支持显式兼容提供方CLI模式；交互UI、调用者已有配置和其他上游提供方未认证。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./crush --yes
abx run <sandbox-id> crush_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('crush_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/crush_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "0.98.1"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| crush_version | none | actual pinned0.98.1 string |
| crush_setup_check | none | installed/version/api_key_set/base_url_set/model_set; read-only flags |
| crush | prompt:str required, nonempty/no NUL/max256KiB UTF-8; cwd:str="" existing inside WORKSPACE; allow_tools:bool=false; command_timeout:int=600,1..1800seconds | {stdout:str,stderr:str,exit_code:int} |

实际argv：crush run --quiet --model owned/ID --small-model owned/ID --cwd DIRECTORY --data-dir PRIVATE。提示通过私有文件stdin输入。CRUSH_CLIENT_SERVER=false选择前台模式。默认禁用全部29项原生工具，显式许可仅开放上述八项。成功、失败、超时、输出溢出均清理自有进程组及身份固定的标记子进程。同用户恶意程序、主动擦除归属标记或服务SIGKILL仍需销毁整个沙箱。

## 配置

| Name | Required | Default | Purpose |
| --- | --- | --- | --- |
| CRUSH_API_KEY | model calls | empty | explicit compatible-provider credential |
| CRUSH_BASE_URL | model calls | empty | HTTP(S) endpoint; no userinfo/query/fragment |
| CRUSH_MODEL | model calls | empty | bounded native model identifier |
| WORKSPACE | no | /home/user/app | existing caller workspace |
| ABX_SERVER_TOKEN | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| CRUSH_BINARY | diagnostics | image PATH | binary override; actual version still checked |

独立HOME/XDG/CRUSH配置数据目录，使用原生禁用默认提供方及自动更新开关。上游自动读取项目配置，因此cwd至最近Git根目录间存在.crushrc/crushrc/.crush.json/crush.json时，在运行前拒绝，保留调用者原文件；无Git时只检查cwd。子进程仅继承PATH/可选CA和私有运行设置，排除云/GitHub/服务密钥。显式模型密钥与地址写入私有0600配置，返回诊断替换其完整值；项目输出仍可能含项目私密内容。

## 资源

2vCPU/2048MB，命令端口9000，可显式启动9010。x64压缩包约26.8MB；下载预算240秒、套接字30秒，单执行文件上限400MiB；构建根文件系统8GiB门禁。提示256KiB，每路输出256KiB，执行1..1800秒另加有限清理时间。不虚构原生max-turn参数；单响应8192 token及执行截止时间约束运行。每次删除私有配置/会话数据，项目修改保留至调用者清理。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

python crush/install_runtime.py --prefix <new-private-prefix>安装至新的私有目录。实际固定版本在PATH后运行python -m pytest -q crush/test_commands.py crush/test_controller.py。夹具使用人工编写HTTP及工具响应，不在操作者主机执行真实模型生成命令。

[step指南](../docs/platform-steps.zh-CN.md)：python scripts/prepare_steps.py crush --output /tmp/crush-steps仅生成步骤；python scripts/run_steps_e2e.py crush --timeout 1200才实际运行。真实模型验收设置E2E_REQUIRE_LLM=1和E2E_REQUIRE_CLI=1，静态标记不能替代L3。

## 贡献

遵循[CONTRIBUTING](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)、[设计](../docs/design/crush.md)，同步双语API、限制和不可变验证记录。

## 问题反馈

[模板Issue65](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/65)；[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板封装代码为[Apache-2.0](../LICENSE)。Crush0.98.1为**FSL-1.1-MIT**，当前不能标为MIT或OSI批准开源。保留并阅读[上游原许可证](upstream-LICENSE.md)、未来许可生效日期及限制，不能推断商业再分发不受限制。安装未修改的官方二进制并保留捆绑声明，不包含模型权重。
