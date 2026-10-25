# Goose

[English](README.md)。

## 做什么

运行官方 Goose1.54.0 终端 agent，对接 OpenAI 兼容服务。每次使用私有配置和
文件 stdin；默认无工具聊天，只有显式 `allow_tools=true` 才开启开发工具。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

阿里云 FC 基础镜像v0.0.49、generation2、非root用户user、已发布服务端包。
官方Linux x86_64/aarch64 CPU GNU资产的字节数和SHA256固定在
[assets.json](assets.json)，对应[源码cd643d2126fffab4c6a6186905211ba868d6a657](https://github.com/block/goose/tree/cd643d2126fffab4c6a6186905211ba868d6a657)。
不需要GPU、Docker daemon、桌面或浮动安装脚本。目前本机测试为Linux x86_64；
arm64资产pin不代表arm64提供方通过。

## 解决的问题

在自有沙箱中使用真正Goose完成终端、文件工作，保留调用者已有提供方、扩展、
hint和会话配置。本配置选择上游支持的OpenAI兼容服务，不代表验证全部提供方
或Goose桌面应用。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./goose --yes
abx run <sandbox-id> goose_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('goose_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/goose_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "1.54.0"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回 |
| --- | --- | --- |
| goose_version | 无 | 真实固定版本字符串1.54.0 |
| goose_setup_check | 无 | installed/version及api_key_set/base_url_set/model_set；不修改配置或登录 |
| goose | 必填prompt:str，非空UTF-8/无NUL/最大256KiB；cwd:str=""，WORKSPACE内现有目录；allow_tools:bool=false；command_timeout:int=600，1..1800 | {stdout:str,stderr:str,exit_code:int} |

实际调用 `run --instructions - --no-session --no-profile --max-turns 20`，固定
quiet文本输出和提供方/模型，工具模式仅加载developer builtin。默认chat不公布
任何工具。输入是私有文件stdin，不拼接shell或prompt argv。每路输出上限256KiB；
超时/超量先清理未reap的自有进程组再回收leader。每次删除私有Goose配置/数据，
项目改动保留至调用者清理或销毁沙箱。返回诊断会遮盖已配置key和base URL，
但项目stdout仍可能包含项目私有内容。

## 配置

| 名称 | 必需 | 默认 | 用途 |
| --- | --- | --- | --- |
| GOOSE_API_KEY | 模型调用 | 空 | 兼容服务凭据，仅映射为原生子进程OPENAI_API_KEY |
| GOOSE_BASE_URL | 模型调用 | 空 | 显式HTTP(S)地址，无userinfo/query/fragment，映射上游OPENAI_BASE_URL |
| GOOSE_MODEL | 模型调用 | 空 | 上游真实模型ID |
| WORKSPACE | 否 | /home/user/app | 自有工作目录 |
| ABX_SERVER_TOKEN | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| GOOSE_BINARY | 仅操作端诊断 | 镜像PATH中的Goose | 独立安装的二进制，仍检查精确版本 |

私有GOOSE_PATH_ROOT/HOME和XDG目录，关闭keyring、遥测、自动会话命名，
设置 `CONTEXT_FILE_NAMES=[]`、`--no-profile`，保留调用者状态。原生子进程仅接收
PATH/可选CA与私有运行/模型设置，不继承云端、GitHub或命令server凭据。

启动第二个服务时保留镜像 PATH；显式覆盖 PATH 时必须包含 `/opt/goose`。诊断只报告该服务进程实际可见的二进制。

## 资源

2vCPU/2048MB，命令API9000，可显式另启9010；不依赖浏览器共享内存。安装器
固定约81MB CPU压缩资产，下载预算240秒、socket超时30秒、可执行文件上限
400MiB，Docker构建另以 `du -sx` 检查8GiB镜像rootfs。操作端prefix安装不扫描
整个本机文件系统。每次最多20模型turn及声明的墙钟时限，再清理。主动setsid
脱离及server被SIGKILL超出进程组保证；最终隔离边界是整个沙箱销毁。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

本机安装：`python goose/install_runtime.py --prefix <new-private-prefix>`；真实
CLI/协议/进程回归：`python -m pytest -q goose/test_commands.py`。合成HTTP fixture
只证明原生协议和工具选择，不证明真实模型或云端支持。HTTP控制器在
E2E_REQUIRE_LLM=1时要求真实源码修改、新报告、原测试不变及隔离held-out断言；
静态marker不能单独证明通过。E2E_REQUIRE_CLI=1要求真实可执行文件。

按[step指南](../docs/platform-steps.zh-CN.md)执行
`python scripts/prepare_steps.py goose --output /tmp/goose-steps`仅生成配置；
真实基础step验收为 `python scripts/run_steps_e2e.py goose --timeout 1200`。
构建方式回执、真实模型及独立自有资源清理分别记录。

## 贡献

[贡献指南](../CONTRIBUTING.md)、[规范](../docs/template-spec.md)及
[设计](../docs/design/goose.md)。两种语言、pin、argv与证据保持一致。

## 问题反馈

[Issue49](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/49)。
模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。
Server/客户端：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。
CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板采用[Apache-2.0](../LICENSE)。官方Goose为Apache-2.0；[原始许可证](upstream-LICENSE)
与未改动的官方二进制一并安装。上游依赖保留各自声明。不分发上游桌面、
Vulkan/CUDA资产、专有账户或模型权重。

### 当前版本新增平台 step 验收

[真实 step](evidence/express-2026-10-20T135350Z.json) 与 [外部 HTTP 尝试](evidence/verification-steps-2026-10-20T135350Z.json)：官方 READY、Python SDK 创建、CLI/SDK 冒烟，HTTP 9 通过、0 失败、1 跳过。本回执模型调用仍为 NOT_RUN；沙箱/模板及同账户私有资产缓存对象/bucket 都独立确认清理后才发布。既有镜像/模型回执保留其独立范围。
