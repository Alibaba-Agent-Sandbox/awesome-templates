# 使用模板

[English](using-templates.md)

选模板，配置沙箱平台及它需要的模型服务，启动一次，再调用命名命令。每个模板 README 提供准确参数、模型与认证配置，以及 CLI、Python、HTTP 的实际任务示例。

## 安装

安装公开 CLI 0.5.8 和 Python client 0.4.0a6。Python 建议使用独立虚拟环境；此包仍为预览版，所以明确固定版本。npm 安装需要 Node 20+，终端能力建议 Node 22+。

```bash
npm install -g @agent-sandbox/cli@0.5.8 --registry=https://registry.npmjs.org
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --index-url https://pypi.org/simple 'agent-sandbox-client==0.4.0a6'
abx --version
```

独立二进制参见 [CLI 安装指南](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/binary-installation.md)。安装后找不到 `abx` 时，执行安装器提示的 PATH 配置。

### 配置沙箱平台

使用极速版**源码**模板前，准备 Docker、ACR namespace 和构建账号权限，再配置：

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SANDBOX_API_KEY="<sandbox-platform-api-key>"
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
export ALICLOUD_ACCESS_KEY_ID="<build-access-key-id>"
export ALICLOUD_ACCESS_KEY_SECRET="<build-access-key-secret>"
export ACR_NAMESPACE="<your-acr-namespace>"
```

默认控制面 URL 与数据面 domain 根据地域生成。只有平台要求其他端点或网关时才覆盖 `ABX_SANDBOX_BASE_URL`、`ABX_SANDBOX_DOMAIN`。Sandbox API Key 应属于所选平台与地域。准确账号及 ACR 配置见 [CLI 配置参考](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/reference/configuration.md)。这些是平台凭据，不是模型凭据。

OpenSandbox 先按其 [provider 指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)完成服务和镜像仓库配置，再统一使用 `ABX_PROVIDER=opensandbox`。4 个托管条目分别按各自 README 与所属平台使用；启动已有平台模板不需要重新构建源码配方。

### 配置应用和模型

正常启动模板时，CLI 自动生成私有应用令牌、保存在本机并供后续命令复用。自定义令牌或从外部 SDK／HTTP 客户端调用服务时，按[应用认证说明](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/guided-configuration.md)配置。模板实际读取的模型 API Key、endpoint、模型选择及必要账号登录另行准备，沙箱、应用和模型凭据各有用途。

各工具采用不同的上游配置方式。不能假定所有工具都读取 `ABX_LLM_*`、支持任意 OpenAI 兼容端点，或继承本机登录态。非模型工具不需要模型 Key；商业账号登录、API Key 模式和可选 Web 服务密码由对应 README 分别说明。

CLI 0.5.8 中，模板清单声明为**空值**的环境变量可由主机环境填充；非空清单值优先于同名主机 export。切模型优先使用命令提供的 `model` 等参数。对于清单空值声明的启动配置，export 新模型、Key 或 endpoint 后，从公开模板创建新实例，并使用新返回的沙箱 ID；只有修改非空清单默认值或实现时才需要本地模板副本。此路径只传递已声明的运行配置。启动后修改本机 export，不会重配已经运行的应用。

## CLI、SDK 与 HTTP

以下示例还会从外部 Python／HTTP 客户端调用应用，因此显式设置自定义 `ABX_SERVER_TOKEN` 并在启动与调用时复用。只使用 CLI 时无需手动设置令牌。

下面的 `python-hello` 不需要模型服务。请先替换凭据与 ID 占位符，并按上文对全部操作使用同一个 `ABX_PROVIDER`。

```bash
export ABX_SERVER_TOKEN="<independent-application-token>"
export ABX_HTTP_TIMEOUT=660
abx template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --sandbox-timeout 1800 --yes
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command list "$ABX_SANDBOX_ID"
abx run "$ABX_SANDBOX_ID" hello --arg name=Ada
```

预期返回 `Hello, Ada!`。启动过程准备模板并启动它声明的应用，返回沙箱 ID 和保留的准备资源引用。`abx run` 调用命名命令，`abx exec` 执行进程；数值和布尔参数使用 `--json-args`。

三类超时分别控制不同阶段：`--timeout` 是构建期限，`--sandbox-timeout` 是实例寿命，`ABX_HTTP_TIMEOUT` 是 CLI 等待 HTTP 的时间；模型命令还有自己的执行期限。对于 600 秒编码任务，示例采用 1800 秒实例与 660 秒客户端等待，避免默认 300 秒实例或 SDK 的默认 30 秒等待先到期。

### Python SDK

在已配置的 Python 环境中保存并运行以下完整示例，连接已经启动的实例；不要另建实例却期望原实例的应用也在那里运行。

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660
        )
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

`client.commands.run` 调用模板应用，`sb.commands.run` 执行进程。`client.aclose()` 与 `sb.close()` 都只释放客户端资源，不删除沙箱。其他模板采用它自己声明的命令、参数、端口与等待时间。

### HTTP POST

以下完整示例直接调用 `POST /commands/hello`，通过 SDK 解析提供方端点与网关头，不假定所有平台都暴露裸 host/port：

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        occupied = {key.lower() for key in headers}
        token = os.environ["ABX_SERVER_TOKEN"]
        if "authorization" not in occupied:
            headers["Authorization"] = "Bearer " + token
        if "x-access-token" not in occupied:
            headers["X-Access-Token"] = token
        if {"authorization", "x-access-token"}.issubset(occupied):
            raise ValueError("Gateway occupies both application authentication headers")
        url = httpx.URL(endpoint)
        url = url.copy_with(path=url.path.rstrip("/") + "/commands/hello")
        async with httpx.AsyncClient(timeout=660) as http:
            response = await http.post(url, headers=headers, json={"name": "Ada"})
            response.raise_for_status()
            print(response.json())
    finally:
        await sb.close()

asyncio.run(main())
```

预期响应：`{"result":"Hello, Ada!"}`。请求体直接是参数对象。保留网关头及 URL 路径／查询参数；应用 `X-Access-Token` 也可通过会移除 Bearer 头的 OpenSandbox 代理。如果网关已使用 Authorization，示例保留它，并通过空闲的应用令牌头认证。两个应用认证头都已被网关占用时，需要兼容的路由，不能覆盖网关凭据或匿名重试。

调用其他模板时，把命令路径和 JSON 参数换成它提供的任务，并设置足够的等待时间。客户端超时不代表远端任务已经停止。

### 导出文件与清理

释放前用 `abx download "$ABX_SANDBOX_ID" /remote/path ./local-file` 或 `await sb.files.read_bytes("/remote/path")` 导出产物。只删除自己这次任务创建的实例：

```bash
abx kill "$ABX_SANDBOX_ID"
```

准备的模板／镜像可能保留供复用。不再需要时，按启动返回的准确资源引用，通过所选平台管理工具清理；不要删除共享基础模板或其他用户的资源。

## 验收与厂商

维护者的测试方法与日期记录放在[公开启动测试指南](public-launch-testing.md)和[工程索引](../.agents/README.md)，不混入模板使用 README。历史运行只说明当时输入，不承诺所有模型、终端或解释器能力。

## 文档与目录归属

- 模板 README：任务、安装、配置、参数、限制、产物与清理。
- `docs/design/<name>.md` 与[贡献指南](../CONTRIBUTING.zh-CN.md)：实现设计及模板编写。
- `template-spec.md`：开发规范。
- `.agents/` 与模板 evidence：工程决定与日期化验证。
- `awesome-templates.yaml`：CLI 与 [Registry](https://github.com/Alibaba-Agent-Sandbox/registry)消费的源目录。

## 客户端入口兼容性

本页 provider／应用示例使用 `ProviderSandbox`。标准 `Sandbox`／`AsyncSandbox` 解释器接口是另一条合同，见相应模板说明及 [SDK 入口指南](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/README.md)。`abx create <平台模板ID>` 使用平台已有模板，源码模板使用 `abx template launch <源码引用>`。
