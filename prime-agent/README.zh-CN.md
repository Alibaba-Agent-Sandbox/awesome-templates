# prime-agent

## 做什么

运行未经修改的稳定版 Prime Agent0.10.0 Rust 原生 CLI，以及工具名为 `ipython` 的原版 CPython REPL。使用显式批准的兼容模型和固定内核解释器。本模板覆盖有界的无头编码流程；daemon、递归代理、订阅模型及研究基准仍未验证。[official release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0)；[pinned native source](https://github.com/PrimeIntellect-ai/prime-agent/tree/763094e1b6a7c17450ee8399b06cda1853847ca5)。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云 generation2 basev0.0.49/Python3.13/Linuxx64；发行归档和可执行文件均校验官方 manifest 发布的 SHA256。保留完整原版 sidecar、runtime源码0.1.0/protocol3及许可证。独立49包 Python 哈希锁；通过原生解释器覆盖跳过浮动 uv/bootstrap。已发布服务端包，非root user，9000端口。[Dockerfile](Dockerfile)、[来源](upstream.json)、[锁文件](requirements.lock)、[设计](../docs/design/prime-agent.md)。

## 解决的问题

通过 Agent Sandbox 调用真实原生编码能力，避免交互登录和共享开发配置。原生 provider 解析、CPython 协议、终态事件和所属资源清理分别验证；安装或版本输出不能证明编码成功。模型生成代码只在新建的自有云端沙箱执行。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./prime-agent --yes
abx run <sandbox-id> prime_agent_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('prime_agent_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/prime_agent_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"native_version": "0.10.0"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

## 命令参考

| Command | Parameters | Result / effects |
| --- | --- | --- |
| prime_agent_version | none | Actual checked binary/version: `{native_version:"0.10.0"}`; no model |
| prime_agent_kernel_check | none | Original CPython runtime protocol3,12 required imports: `{protocol_version:3,required_imports_checked:12}`; no model or bootstrap |
| prime_agent_setup_check | none | mode `original-native-prime-cpython-repl`; subscription_required:false; api_key_set/base_url_set/model_set booleans; read-only |
| prime_agent | prompt: required nonempty string1..32768UTF-8 bytes/no NUL; cwd: optional string default empty, max4096bytes, existing directory resolved inside WORKSPACE; command_timeout: integer1..600seconds default300 | `{stdout:string,stderr:string,exit_code:int,native_version:"0.10.0",native_completed:bool}`; real original native tools may modify files |

固定参数：--offline --mode json --provider abx-approved --model <configured-model> --thinking off --no-session --no-skills --no-prompt-templates --no-themes --no-context-files --cwd <private-git-root> --print。提示经匿名stdin传入，含选定项目绝对路径。原生cwd使用私有Git根，防止调用方项目配置覆盖显式provider。原生 ipython 工具执行原版CPython代码，工具具有外层一次性沙箱用户的OS权限；cwd检查不是额外OS隔离。

透明事件过滤器保留原版已完成NDJSON行，仅丢弃增量重复事件：原始stdout16MiB、单行1MiB、保留stdout256KiB、stderr256KiB；保留原生退出码和信号。native_completed要求exit0、原生turn_end/agent_end和最终assistant stopReason=stop；编码验收还要求原生ipython成功结果及独立原始/隐藏测试。调用串行，重叠请求返回busy。超时、超量和失败均清理本次进程组、nonce标记后代及私有HOME/配置/缓存/内核状态。

## 配置

| Name | Default / requirement | Meaning |
| --- | --- | --- |
| PRIME_MODEL_API_KEY | empty; required for coding | Approved compatible-model key |
| PRIME_MODEL_BASE_URL | empty; required for coding | Explicit HTTPS base; literal local HTTP for authored fixtures only; no userinfo/query/fragment; max2048characters |
| PRIME_MODEL | empty; required for coding | Actual model identifier; max200allowed identifier characters |
| WORKSPACE | `/home/user/workspace` | Existing caller project root |
| ABX_SERVER_TOKEN | 必填；清单为空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

配置在commands.py加载时读取。私有0700HOME/0600models.json使用 apiKey="ABX_PRIME_MODEL_KEY" 环境变量引用，不保存key值。不继承操作端云/GitHub/厂商凭据。固定内核入口在启动原版CPython前删除ABX_PRIME_MODEL_KEY；同一用户仍有OS访问权限，这只是环境收敛，不是凭据隔离。返回值脱敏原值及JSON转义的key/base。禁用遥测、trace、refinement、compaction、factory及发现，设置rlmMaxDepth0；原生print模式不传child host，使用NoRlmChildren，不启动委派代理或daemon。自定义模型价格未知，默认0不能理解为免费。

## 资源

仅Linuxx64，声明2vCPU/2048MB、9000端口，强制8GiB rootfs预算。无需嵌套Docker/KVM/GPU。编码需模型工具调用、显式API授权和网络出口；尚未测量任务峰值内存或容量。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

```bash
python -m pytest -q prime-agent/test_commands.py prime-agent/test_terminal.py
python scripts/check_template.py prime-agent --strict
python scripts/check_docs.py
python scripts/run_steps_e2e.py prime-agent
```

真实模型控制器仅允许显式拥有的远程目标：修改预置源文件、保持原测试字节不变、下载新报告和精确随机nonce、独立运行原始3项加4项隐藏用例，并执行返回后的新ACK。固定合成协议fixture及源码模式原生跳过不构成模型/云端通过。

## 贡献

遵循[贡献规范](../CONTRIBUTING.zh-CN.md)、项目/文档规范及不可变证据规则。保留原版许可证和完整sidecar；双语README、设计、manifest、目录和工程记录一起更新。

## 问题反馈

跟踪[Issue69](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69)。报告脱敏后的可复现问题、源码版本及测试层级；禁止附私钥、私有端点或原始提示/模型输出。

SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## 许可证

自编封装Apache-2.0；原版Prime Agent为MIT，PHOTON第三方声明为Apache-2.0。[发行与归属说明](UPSTREAM-NOTICE.md)；完整上游声明保留，不改变第三方许可证。
