# Tau2 零售基准

[English](README.md).

## 做什么

运行原版 Tau2 v1.0.1 文本零售任务，由原生智能体与用户模拟器共同完成，返回原版评分及脱敏轨迹，再通过不携带模型密钥的原版评估器独立严格重放。支持范围为零售子集；其他领域、语音、知识任务及需要自然语言裁判的任务均拒绝。单个任务成绩不能代表完整基准。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

MIT 许可的[固定原版源码](https://github.com/sierra-research/tau2-bench/tree/fc0055dc4e0a316c3f83133267fbd6faaa770992)、Python3.13、隔离且按哈希锁定的依赖、LiteLLM1.81.11 与 Agent Sandbox server。
查看 [Dockerfile](Dockerfile)、[requirements.lock](requirements.lock)、[upstream.json](upstream.json) 和[设计](../docs/design/tau2-bench.md)。官方源码归档为92,081,935字节；固定 SHA256 记录在 `upstream.json`，来自控制端测量，并非上游发布的校验和。固定 `PYTHONPATH=/opt/tau2/src` 从源码运行，不声称 PyPI 已发布 Tau2 包。

[原始冻结导出](requirements.upstream.lock)完整保留平台标记；`python tau2-bench/select_lock.py` 选择 Linux CPython3.13 对应条目，不修改版本和哈希，镜像强制检查 Python 配置。

另由[兼容锁文件](requirements.compat.lock)明确新增 PSF-2.0 的 `audioop-lts==0.2.2`：Python3.13 已移除 `audioop`，但此版上游文本任务也会导入它；保留[许可证](AUDIOOP-LICENSE.txt)。

选取数据同时包含原版共享用户模拟器指引和零售领域数据，不使用替代指引。

## 解决的问题

为原版任务提供有界执行、原生评估、可单独下载的轨迹和独立严格重放。智能体与用户模拟器均使用明确配置的模型服务。

`tau2_run(domain)` 按需求返回 `score` 和 `log_path`，`artifact_path` 是同一份所属脱敏轨迹路径，同时提供字节数和 SHA256。

文本通信采用原生默认 `enforce_communication_protocol=False`，完成状态、源码、评分和严格重放验收要求均保留。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./tau2-bench --yes
abx run <sandbox-id> tau2_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('tau2_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/tau2_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"native_version": "1.0.1", "domain": "retail", "task_count": 114}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| 命令 | 参数 | 返回及副作用 |
| --- | --- | --- |
| `tau2_version` | 无 | 原版源码版本、提交、零售领域及原版任务数；不调用模型。 |
| `tau2_setup_check` | 无 | 配置是否存在的布尔值及 `native-retail-agent-and-user` 模式；不返回密钥、不调用模型。 |
| `tau2_run` | `domain: str="retail"`（仅零售）；`task_id: str="0"`（1–3位十进制数字且任务须存在）；`max_steps: int=30`（5–60，拒绝 bool）；`command_timeout: int=600` 秒（30–900，拒绝 bool） | 原生 `score`、`log_path`/`artifact_path` 同路径、终止原因、消息及工具次数、源码提交、轨迹字节数/SHA256；调用两个模型并写入独占私有结果目录。含非空自然语言断言的任务在模型调用前拒绝。 |
| `tau2_verify_artifact` | 必填 `path: str`（最多4096个 UTF-8 字节，工作区内已有常规轨迹文件，1–8MiB）；`task_id: str="0"` | 无模型密钥的原版严格重放、匹配评分和轨迹 SHA256；不修改文件；期限120秒。 |

版本命令期限60秒，输入走匿名 stdin，每条输出流限256KiB。原版进程使用串行化独占进程组、nonce 和 pidfd 清理。超时、非零退出、未完成轨迹、错误源码/任务、评分不一致或畸形输出均失败。

## 配置

| 变量 | 必填/默认 | 含义 |
| --- | --- | --- |
| `TAU2_MODEL_API_KEY` | 运行任务必填；空 | 模型密钥，最多8192字符，禁止 CR/LF/NUL。 |
| `TAU2_MODEL_BASE_URL` | 运行任务必填；空 | 显式 HTTPS 兼容接口，最多2048字符；仅本地字面地址允许 HTTP 合成测试；禁止 userinfo、query、fragment。 |
| `TAU2_MODEL` | 运行任务必填；空 | 明确模型标识，最多200个允许的标识字符。 |
| `WORKSPACE` | `/home/user/workspace` | 已有且可写的结果根目录。 |
| `ABX_SERVER_TOKEN` | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在服务导入时捕获。双方原生模型均设置相同 `openai/` 模型和显式 `api_base`，密钥只经匿名 stdin 进入私有工作进程环境，不写入 argv 或配置文件。排除操作端云凭据、GitHub 凭据和二进制覆盖变量。所有路径清理私有 HOME、临时原生日志和子进程；成功轨迹归调用者管理，失败的部分结果删除。轨迹的键和值递归移除实际密钥和接口字符串；重放不携带模型密钥。禁用遥测及模型价格网络刷新；未知价格返回零不代表免费或准确账单。

## 资源

2 vCPU、2048MiB RAM、9000端口、非 root `user`；无需 Docker daemon、KVM、GPU 或额外权限。根文件系统约10GiB，构建拒绝超过8GiB。92MB 源归档仅保留约38MB 源码/零售数据及依赖。智能体与模拟用户都产生模型费用；步骤5–60，每次模型请求60秒超时，命令期限30–900秒。成功轨迹不超过8MiB，保留于独占 `abx_tau2_result_<nonce>` 目录；读取后只删除本次目录，并销毁、独立确认自己的外层云资源不存在。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

运行 `python -m pytest -q tau2-bench/test_runtime.py`、
`python scripts/check_template.py tau2-bench` 和 `python scripts/check_docs.py`。
外部 `e2e_test.py` 检查发现、版本、配置及非法参数。设置 `E2E_REQUIRE_CLI=1` 强制原版运行；真实模型检查须在新建云服务设置
`E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1`：原版零售任务0须完成且评分1.0，具有实际智能体、用户和工具消息，独立下载核对字节及 SHA，再独立执行原版严格重放、返回后新鲜确认及结果清理。生成代码和运行时代码仅在云沙箱执行。不推断完整基准准确率；源码、数据、依赖、任务变化须重新验收。

## 贡献

遵循[贡献指南](../CONTRIBUTING.zh-CN.md)、[项目规范](../docs/project-standards.zh-CN.md)和[文档规范](../docs/documentation-standards.zh-CN.md)。保留上游冻结锁与两份许可证，同步翻译、设计、清单和目录，区分真实/合成测试并记录所属资源清理。

## 问题反馈

[模板需求59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59)。
模板问题：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)；
SDK/server：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)；
CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装为 [Apache-2.0](../LICENSE)，原版 Tau2 源码与选取的零售数据保留 [MIT 声明](UPSTREAM-LICENSE.md)。分发时保留上游声明。
Python3.13 兼容依赖保留 [audioop-lts PSF-2.0 许可证](AUDIOOP-LICENSE.txt)。
