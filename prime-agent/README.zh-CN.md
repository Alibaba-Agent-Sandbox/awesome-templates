# prime-agent

## 做什么

运行未经修改的稳定版 Prime Agent0.10.0 Rust 原生 CLI，以及工具名为 `ipython` 的原版 CPython REPL。使用显式批准的兼容模型和固定内核解释器。本模板覆盖有界的无头编码流程；daemon、递归代理、订阅模型及研究基准仍未验证。[official release](https://github.com/PrimeIntellect-ai/prime-agent/releases/tag/v0.10.0)；[pinned native source](https://github.com/PrimeIntellect-ai/prime-agent/tree/763094e1b6a7c17450ee8399b06cda1853847ca5)。

## 技术栈

阿里云 generation2 basev0.0.49/Python3.13/Linuxx64；发行归档和可执行文件均校验官方 manifest 发布的 SHA256。保留完整原版 sidecar、runtime源码0.1.0/protocol3及许可证。独立49包 Python 哈希锁；通过原生解释器覆盖跳过浮动 uv/bootstrap。server源码 e2cb27e24fde0a67112f82b8d44af463445a5d1a，非root user，9000端口。[Dockerfile](Dockerfile)、[来源](upstream.json)、[锁文件](requirements.lock)、[设计](../docs/design/prime-agent.md)。

## 解决的问题

通过 Agent Sandbox 调用真实原生编码能力，避免交互登录和共享开发配置。原生 provider 解析、CPython 协议、终态事件和所属资源清理分别验证；安装或版本输出不能证明编码成功。模型生成代码只在新建的自有云端沙箱执行。

## 快速开始（CLI）

安装[已验证的原生 CLI](../docs/platform-steps.zh-CN.md)，配置已授权的 Express 访问，将尖括号占位符替换为本次唯一的自有值。steps 使用不可变公共 COPY 输入前先发布准确提交；等待官方 READY 后再创建沙箱。CLI0.4.1 使用 `abx --native run`，命名命令入口为 `abx run`。

```bash
python scripts/prepare_steps.py prime-agent --output /tmp/prime-steps-<unique-run> \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/prime-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> prime_agent_version
abx --native run <owned-sandbox-id> prime_agent_kernel_check
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```
版本预期 `{"native_version":"0.10.0"}`。配置命令服务后可调用 `abx --native run <owned-sandbox-id> prime_agent --json-args '{"prompt":"Inspect the existing project and fix failing tests","cwd":"project","command_timeout":300}'`。项目须已存在且位于 WORKSPACE。编码成功还需原生终态及独立文件/测试验证。

## 快速开始（Python SDK）

按[配套源码安装说明](../docs/python-client-installation.md)安装发行包 `agent-sandbox-client`，导入 `agent_sandbox`。以下示例不调用模型，并清理自身沙箱；示例做语法检查，真实云端结论以“已验证”为准。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=300)
    try:
        print(await sb.run("prime_agent_version", timeout=60))
        print(await sb.run("prime_agent_kernel_check", timeout=90))
    finally:
        await sb.kill()

asyncio.run(main())
```
命令服务启动前配置 PRIME_MODEL_API_KEY/PRIME_MODEL_BASE_URL/PRIME_MODEL。[预热进程配置](../docs/runtime-environment.zh-CN.md)说明后续 create 环境不会重配已有9000服务。先通过 `prime_agent_setup_check` 检查存在性，再调用 `await sb.run("prime_agent", prompt="Fix existing source and preserve its tests", cwd="project", command_timeout=300, timeout=330)`。直接返回结构化缓冲结果，不流式返回事件。

## 快速开始（HTTP POST）

ABX_SERVER_URL 来自 `sb.network.get_url(9000)`；命令服务 token 独立于模型和云端凭据。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/prime_agent_version" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header "Content-Type: application/json" --data '{}'
```
HTTP200返回 `{"result":{"native_version":"0.10.0"}}`。`POST /commands/prime_agent` 直接接收 `{prompt,cwd,command_timeout}`。类型/未知/缺失参数400，鉴权401，未知命令404，语义校验或执行异常500及 `{error,type}`。原生进程结束后返回真实 exit_code，包括非零值。客户端断连不取消有界执行，最终清理仍会运行。

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
| ABX_SERVER_TOKEN | optional; empty | Independent command-server Bearer token |

配置在commands.py加载时读取。私有0700HOME/0600models.json使用 apiKey="ABX_PRIME_MODEL_KEY" 环境变量引用，不保存key值。不继承操作端云/GitHub/厂商凭据。固定内核入口在启动原版CPython前删除ABX_PRIME_MODEL_KEY；同一用户仍有OS访问权限，这只是环境收敛，不是凭据隔离。返回值脱敏原值及JSON转义的key/base。禁用遥测、trace、refinement、compaction、factory及发现，设置rlmMaxDepth0；原生print模式不传child host，使用NoRlmChildren，不启动委派代理或daemon。自定义模型价格未知，默认0不能理解为免费。

## 资源

仅Linuxx64，声明2vCPU/2048MB、9000端口，强制8GiB rootfs预算。无需嵌套Docker/KVM/GPU。编码需模型工具调用、显式API授权和网络出口；尚未测量任务峰值内存或容量。

## 已验证

尚未记录任何通过的提供方测试。

原生version/help及本地自编测试仅是部分证据。当前镜像、Express、原生内核、真实模型和独立清理门禁待完成。[带日期研究](../.agents/evidence/verify/2026-10-20-prime-agent-native-research.md)。

## 二次开发

```bash
python -m pytest -q prime-agent/test_commands.py prime-agent/test_terminal.py
python scripts/check_template.py prime-agent --strict
python scripts/check_docs.py
ABX='abx --native' python scripts/run_steps_e2e.py prime-agent --sandbox-create sdk --http
```

真实模型控制器仅允许显式拥有的远程目标：修改预置源文件、保持原测试字节不变、下载新报告和精确随机nonce、独立运行原始3项加4项隐藏用例，并执行返回后的新ACK。固定合成协议fixture及源码模式原生跳过不构成模型/云端通过。

## 贡献

遵循[贡献规范](../CONTRIBUTING.zh-CN.md)、项目/文档规范及不可变证据规则。保留原版许可证和完整sidecar；双语README、设计、manifest、目录和工程记录一起更新。

## 问题反馈

跟踪[Issue69](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/69)。报告脱敏后的可复现问题、源码版本及测试层级；禁止附私钥、私有端点或原始提示/模型输出。

SDK/server: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## 许可证

自编封装Apache-2.0；原版Prime Agent为MIT，PHOTON第三方声明为Apache-2.0。[发行与归属说明](UPSTREAM-NOTICE.md)；完整上游声明保留，不改变第三方许可证。
