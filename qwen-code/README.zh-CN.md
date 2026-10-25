# Qwen Code

[English](README.md)

## 做什么

通过类型化命名命令运行固定版本 Qwen Code 无头编码 CLI，并提供安装诊断和 Python 脚本执行命令。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a2`，由 Dockerfile 直接安装。

Alibaba FC generation 2 基础镜像、平台 Python、固定版本且校验 x86_64/aarch64 SHA256 的 Node.js 24.16.0、`@qwen-code/qwen-code@0.23.0`，以及 [Dockerfile](Dockerfile) 固定提交的沙箱服务器。CLI 不需要额外的 DashScope/OpenAI Python 库。

## 解决的问题

提供可复现的无头编码环境。显式选择 OpenAI 兼容认证，缺少密钥时在启动 CLI 前返回错误，避免等待浏览器 OAuth 登录。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装已发布 CLI 和 Python 客户端、配置极速版。在本仓库根目录执行，确保 Docker 和提供方镜像仓库可用。先在当前终端生成独立应用令牌：

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
abx template launch ./qwen-code --sandbox-timeout 900 --yes
```

该命令准备模板、创建沙箱并启动其应用。将返回的沙箱 ID 写入 `SANDBOX_ID`；三个客户端使用同一个应用令牌：

```bash
export SANDBOX_ID='<sandbox-id>'
abx sandbox command list "$SANDBOX_ID"
abx run "$SANDBOX_ID" qwen_version
abx run "$SANDBOX_ID" qwen_setup_check
```

`qwen_version` 返回 `0.23.0`。setup 结果只报告安装和配置是否存在，不返回凭据。两个命令都不需要模型密钥，也不执行编码任务。使用 OpenSandbox 时，按[调用指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置，在启动前设置 `ABX_PROVIDER=opensandbox`，下面 Python 改用 `provider="opensandbox"`。

### 运行编码任务

启动**新实例之前**，在启动终端安全配置 `OPENAI_API_KEY`（或备选 `DASHSCOPE_API_KEY`）。`template.yaml` 中值为空的密钥声明会在 launch 时继承这些值。默认端点和模型为 DashScope 与 `qwen3-coder-plus`；需要其他端点或工作区时，在启动前修改 `template.yaml` 中非空的 `env` 默认值。事后 export 不会重新配置运行中的应用。单次调用可通过 `model` 参数覆盖模型。

选择带模型密钥的实例 ID 和令牌，上传已有计算器和测试文件，再让 Qwen 修复：

```bash
abx upload "$SANDBOX_ID" ./calculator.py /home/user/app/calculator.py
abx upload "$SANDBOX_ID" ./test_calculator.py /home/user/app/test_calculator.py
```

使用下面 Python SDK 示例中的编码调用完成任务后，再运行独立测试并下载报告。长编码任务可在 CLI 0.4.17 使用 `ABX_HTTP_TIMEOUT=330 abx run ...`；Python/HTTP 客户端使用显式 `timeout=330`。`command_timeout` 单独控制服务端任务期限。CLI 0.4.16 的命名调用仍最多等待 30 秒，需升级后再使用 CLI 超时配置。客户端超时不会取消远端任务。

```bash
abx exec "$SANDBOX_ID" -- python3 -m unittest discover -s /home/user/app -p test_calculator.py
abx download "$SANDBOX_ID" /home/user/app/REPORT.md ./REPORT.md
```

上传前将本地文件名换成你自己的项目文件。`yolo=true` 批准所有代理工具操作，仅用于允许代理修改的项目；默认 `false`。结果是缓冲的 Qwen JSON 文本。查看报告及独立测试结果，版本或配置检查不能证明模型兼容或代码修复成功。

完成 CLI、Python 和 HTTP 示例后，用 `abx kill "$SANDBOX_ID"` 删除自有实例。launch 日志标明为复用保留的模板/镜像；不再需要时单独删除这些确属本次创建的资源。

## 快速开始（Python SDK）

按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 `agent-sandbox-client`。连接上面已经启动的实例；另建实例不会继承其运行中的应用。

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["SANDBOX_ID"], provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=330)
        try:
            print(await client.commands.run("qwen_version"))
            print(await client.commands.run("qwen_setup_check"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

实例已配置模型密钥且文件上传后，可在同一 `try` 块中调用 `await client.commands.run("qwen", prompt="修复 calculator.py 并写 REPORT.md；保留和运行测试", max_turns=20, yolo=True, command_timeout=300)`。`timeout=330` 控制 HTTP 等待，`command_timeout=300` 限制代理进程组执行。客户端超时本身不取消任务。关闭借用的连接不会删除沙箱。

## 快速开始（HTTP POST）

从同一实例解析端点及网关头，保留网关认证、URL 路径前缀和查询参数，独立配置应用令牌：

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["SANDBOX_ID"], provider="alicloud-express")
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        if any(key.lower() == "authorization" for key in headers):
            raise ValueError("Keep gateway Authorization; do not replace it with an application token")
        token = os.environ["ABX_SERVER_TOKEN"]
        headers["Authorization"] = "Bearer " + token
        if not any(key.lower() == "x-access-token" for key in headers):
            headers["X-Access-Token"] = token
        base = httpx.URL(endpoint)
        async with httpx.AsyncClient(timeout=330) as http:
            for name in ("qwen_version", "qwen_setup_check"):
                url = base.copy_with(path=base.path.rstrip("/") + "/commands/" + name)
                response = await http.post(url, headers=headers, json={})
                response.raise_for_status()
                print(response.json())
    finally:
        await sb.close()

asyncio.run(main())
```

`POST /commands/qwen_version` 发送 `{}`，使用 `Content-Type: application/json`，返回 `{"result":"0.23.0"}`。setup 返回 `result` 内的对象。编码任务配置完成后，使用 `POST /commands/qwen` 和下面的直接参数对象，不加 `args` 包装；返回 `{"result":"<缓冲的 Qwen JSON 输出文本>"}`。缺参/类型错误为 400，认证失败为 401，未知命令为 404，参数范围错误、缺密钥/CLI、上游失败或执行超时为 500。错误响应含 `{"error":"...","type":"RuntimeError"}` 或 `ValueError`，已知秘密值会脱敏。

```json
{"prompt":"Fix calculator.py, preserve test_calculator.py, write REPORT.md and run tests","max_turns":20,"yolo":true,"command_timeout":300}
```

## 命令参考

| 命令 | 参数 | 结果及上游调用 |
| --- | --- | --- |
| `qwen` | `prompt: str` 必填非空；`max_turns: int=100`（1–1000）；`model: str=""` 使用 `OPENAI_MODEL`；`cwd: str=""` 使用工作区；`command_timeout: int=600`（1–1800 秒）；`yolo: bool=false` | 字符串；`qwen -p PROMPT --auth-type openai --output-format json --max-session-turns N --max-wall-time SECONDS --no-chat-recording`，按需加 `--model MODEL`、`--yolo` |
| `qwen_version` | 无 | 真实 `qwen --version` 输出，不需密钥 |
| `qwen_setup_check` | 无 | 安装/版本/pin、密钥/模型/base URL 是否配置、设置文件存在与 JSON 有效性；不返回设置内容，不写文件 |
| `run` | `script: str="main.py"` | 兼容命令，返回 Python stdout，执行期限 120 秒 |

`cwd` 为绝对路径或相对 `WORKSPACE` 的路径，必须已经存在。包装器使用 argv 数组，不拼接 shell。上游编码代理可以修改文件并执行 shell 工具。

此生命周期实现适用于 Linux：并行读取两路输出，在清理自建进程组前保留未回收的会话 leader。成功、非零退出和执行截止都会先清理该组再返回。

## 配置

| 变量 | 含义 |
| --- | --- |
| `OPENAI_API_KEY` | 编码任务所需的主要模型密钥；版本和配置检查不需要 |
| `DASHSCOPE_API_KEY` | 主要密钥为空时的备选值，仅在子进程映射 |
| `OPENAI_BASE_URL` | 默认 `https://dashscope.aliyuncs.com/compatible-mode/v1`，其他兼容端点需在启动前修改清单默认值 |
| `OPENAI_MODEL` | 默认 `qwen3-coder-plus`，命令参数 `model` 优先 |
| `WORKSPACE` | 默认 `/home/user/app` |
| `ABX_SERVER_TOKEN` | 启动 application 工作流前必填；独立于模型和网关凭据 |

诊断只读 `~/.qwen/settings.json` 和 `<workspace>/.qwen/settings.json`，保留内容与权限；正常编码可能产生上游运行缓存。兼容约定见[上游模型提供方配置](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/configuration/model-providers.md)和[无头模式](https://github.com/QwenLM/qwen-code/blob/v0.23.0/docs/users/features/headless.md)。每个端点/模型仍需真实验收，不把 API 日志中的秘密写入公开产物。

## 资源

2 vCPU、4096 MB 内存、端口 9000，需要访问所选模型服务的出网能力。generation 2 使用非 root `user`，Qwen 不依赖 Docker-in-Docker 或额外权限。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 历史验收

| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。该历史 smoke 不证明真实模型任务或当前 launch 路径。

## 二次开发

在 `commands.py` 添加类型化 `@command`，`start()` 保持在主入口保护内。保留 `qwen`、`run` 名称，双语更新参数文档，固定 CLI/server 版本。修改前阅读[设计](../docs/design/qwen-code.md)。

当前源码启动检查见[公开 launch 测试指南](../docs/public-launch-testing.md)。下面的历史 steps 保留各自输入和调用路径范围。

## 贡献

遵守[贡献规则](../CONTRIBUTING.md)和[模板规范](../docs/template-spec.md)。运行 `python3 scripts/check_template.py qwen-code`、`python3 -m pytest -q qwen-code/test_commands.py`、`python3 scripts/run_local_e2e.py`。本地 CLI 缺失时可跳过实版本测试，`E2E_REQUIRE_CLI=1` 时必须失败，跳过不代表运行时通过。真实编码验收先用兼容密钥/base URL/model 启动服务器，再运行 `E2E_REQUIRE_CLI=1 E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 python3 qwen-code/e2e_test.py`。测试修改现有源文件，经文件 API 读取新报告和精确产物，再经目标 shell API 独立运行原测试及保留计算；只清理本次唯一项目目录。保留工程记录，不提交密钥或失败的提供方通过证据。

## 问题反馈

模板任务跟踪于 [issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26)。SDK/server 问题提交 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，附脱敏命令、版本及实际未通过门禁。

## 许可证

模板使用 Apache-2.0。Qwen Code 保留[上游许可](https://github.com/QwenLM/qwen-code/blob/v0.23.0/LICENSE)。

### 2026-10-20完整 step 检查点：模板2.1.1

[真实对应版本 step](evidence/express-2026-10-20T155502Z.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T155502Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，9 PASS/0 FAIL/1 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
