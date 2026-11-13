# 使用模板

[English](using-templates.md)

选择模板、准备平台及必要的模型服务，部署可复用模板，再启动动态实例并调用业务命令。各模板 README 提供具体参数、凭据用途和 CLI、Python、HTTP 用例。

## 安装

本分支 YAML v1 需要匹配的开发版 CLI；已发布 CLI 0.5.10 不支持此格式。使用 Node 20+，将下面占位符替换为经过审查的匹配提交。Python 运行脚本使用已发布客户端 0.4.0a7。

```bash
git clone https://github.com/Alibaba-Agent-Sandbox/agent-sandbox.git
cd agent-sandbox
git checkout <reviewed-yaml-v1-cli-revision>
npm ci
npm run build
npm link
cd ..
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --index-url https://pypi.org/simple 'agent-sandbox-client==0.4.0a7'
abx --version
```

### 配置 Sandbox 平台

Express 源码构建需要 Docker、已有 ACR 命名空间及对应账号权限。Sandbox 平台 Key 用于创建实例，云 AK/SK 用于构建推送和资源管理，两者均不是模型 Key：

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SANDBOX_API_KEY="<sandbox-platform-api-key>"
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
export ALICLOUD_ACCESS_KEY_ID="<build-access-key-id>"
export ALICLOUD_ACCESS_KEY_SECRET="<build-access-key-secret>"
export ACR_NAMESPACE="<your-acr-namespace>"
```

平台 Key 与地域必须匹配。默认控制面 URL 和数据面域名由地域推导；仅平台要求时覆盖 `ABX_SANDBOX_BASE_URL` / `ABX_SANDBOX_DOMAIN`。凭据来源和配置方式见 [CLI 配置参考](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/reference/configuration.md)。

其他 Provider 使用自己的模板属性、镜像格式和部署能力；不能仅修改环境变量就将 Express 清单当成可移植配置。OpenSandbox 的准备步骤见其 [Provider 指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)。已有托管模板的用法见各自 README。

### 配置应用和模型

普通模板的 `run.py` 自动生成独立应用令牌并保存在私有 `.sandbox-session.json`，也可使用显式提供的 `ABX_SERVER_TOKEN`。平台 Key、应用令牌和模型 Key 用于不同系统。模型登录方式、API Key、端点和模型选择以该模板 README 为准；不应假设所有工具都使用 `ABX_LLM_*`。

镜像默认值在 Dockerfile。脚本仅转发 `RUNTIME_ENV_NAMES` 中声明的本机导出值；运行前准备模型凭据和覆盖值。启动后修改本机环境不会重新配置已运行的应用，详见[运行环境](runtime-environment.zh-CN.md)。

## CLI、SDK 与 HTTP

下载匹配版本的 `python-hello` 目录，并在该目录执行。此模板不需要模型服务。替换返回的 ID；以下读取私有令牌但不显示它：

```bash
export ABX_HTTP_TIMEOUT=660
abx deploy . --yes
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
export ABX_SANDBOX_ID="<returned-sandbox-id>"
abx sandbox command list "$ABX_SANDBOX_ID"
abx sandbox command run "$ABX_SANDBOX_ID" hello --arg name=Ada
```

预期结果为 `Hello, Ada!`。deploy 准备可复用模板，run.py 创建实例并启动应用。`sandbox command run` 调用命名业务命令，`sandbox exec` 执行进程；数字和布尔参数使用 `--json-args`。

`run.py --timeout` 是实例租期，`--ready-timeout` 是启动就绪等待；`ABX_HTTP_TIMEOUT` 是 CLI 请求等待。业务命令自身期限另行设置，客户端超时不证明远端任务停止。

### Python SDK

连接同一已启动实例，不重新创建实例：

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"])
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=660)
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

`client.commands.run` 调用应用，`sb.commands.run` 执行进程。关闭客户端连接不会删除实例。

### HTTP POST

通过 SDK 解析端口 URL 和 Provider 网关认证，保留原 URL 路径、查询和认证，再添加应用令牌。以下代码可直接保存运行：

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(os.environ["ABX_SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"])
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

预期响应为 `{"result":"Hello, Ada!"}`，参数直接作为 JSON body。Provider 若占用两个应用认证头，需要兼容路由；不能覆盖网关认证或匿名重试。

### 导出文件与清理

删除前使用 `abx sandbox download "$ABX_SANDBOX_ID" /remote/path ./local-file` 或 SDK 文件读取导出结果，再删除本次拥有的实例：

```bash
abx sandbox delete "$ABX_SANDBOX_ID" --yes
```

实例删除后再删除对应私有会话文件。可复用模板和镜像可能保留；不再需要时按所属平台清理本次拥有的资源，不删除共享模板或其他用户资源。

## 客户端入口

以上使用 `ProviderSandbox`。标准 `Sandbox` / `AsyncSandbox` 解释器入口是独立接口，见 [SDK 入口指南](https://github.com/Alibaba-Agent-Sandbox/python-sdk/blob/main/README.md)。运行脚本使用 SDK 创建和连接方法，不要求 Python 解析或构建 YAML。Registry 元数据用于上架/初始化，本地部署不依赖它。见[资源规范](template-spec.zh-CN.md)。
