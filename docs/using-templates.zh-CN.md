# 使用与验证模板

先阅读本页的安装和调用约定，再查目标模板 README 中的准确命令、参数、运行限制
与示例。[模板规范](template-spec.zh-CN.md)负责开发和验收规则；
[源码运行诊断](express-source-runtime.md)是另一类测试，不能证明镜像部署通过。

## 安装

安装已发布的 CLI 和 Python SDK 预览版；需要终端能力时建议 Node 22+：

```bash
npm install -g @agent-sandbox/cli@0.4.16
python3 -m pip install 'agent-sandbox-client==0.3.1a5'
abx --version
```

独立二进制见 [CLI 安装指南](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/zh/guide/binary-installation.md)。构建源码模板需要 Docker 和可写镜像仓库。按所选 provider 的指南配置账号，将凭据放在环境变量或配置文件中。

## CLI、SDK 与 HTTP

极速版需配置 Sandbox API key、base URL/domain、控制面凭据和 ACR namespace。安全设置 `ABX_SERVER_TOKEN` 后启动应用：

```bash
abx --provider alicloud-express template launch Alibaba-Agent-Sandbox/awesome-templates//python-hello --yes
abx sandbox command list <sandbox-id>
abx run <sandbox-id> hello --arg name=Ada
```

启动结果包含沙箱 ID 和已准备的模板引用。CLI 负责启动这个实例的应用服务。`abx run` 调用模板命名命令，`abx exec` 执行进程，数值或布尔参数使用 `--json-args`。

Python 连接这个已运行的实例。使用模板引用另建实例时，需要为新实例单独启动应用；原实例的运行进程不会继承过去。

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

直接 HTTP POST 时，用 SDK 解析提供方端点及网关头，并保留端点的路径与查询参数：

```python
import asyncio
import os
import httpx
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        endpoint, gateway_headers = await sb.network.resolve(9000)
        headers = dict(gateway_headers)
        if any(key.lower() == "authorization" for key in headers):
            raise ValueError("Keep the gateway Authorization header; do not replace it")
        token = os.environ["ABX_SERVER_TOKEN"]
        headers["Authorization"] = "Bearer " + token
        if not any(key.lower() == "x-access-token" for key in headers):
            headers["X-Access-Token"] = token
        url = httpx.URL(endpoint)
        url = url.copy_with(path=url.path.rstrip("/") + "/commands/hello")
        async with httpx.AsyncClient(timeout=180) as http:
            response = await http.post(url, headers=headers, json={"name": "Ada"})
            response.raise_for_status()
            print(response.json())  # {"result": "Hello, Ada!"}
    finally:
        await sb.close()

asyncio.run(main())
```

请求体直接是参数 JSON。已有的应用 `X-Access-Token` 头也可经过 OpenSandbox server proxy；该代理会移除 Bearer 认证头。CLI 和 Python application client 在同名头未被占用时自动补充它。provider 网关若要求自己的头，应保留原值，包括已有的网关 `X-Access-Token`。认证失败直接报错，不匿名重试。

用完执行 `abx kill <sandbox-id>` 删除实例。启动记录中列出保留供复用的模板和镜像；不再需要时，单独删除这些确切属于本次的资源。连接客户端不转移资源归属，也不自动销毁实例。

OpenSandbox 先安装配置 [provider](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)，每条 CLI 命令指定 `--provider opensandbox`，Python 连接指定 `provider="opensandbox"`。CLI 直接准备默认源码配方。对于已声明 portable profile 的模板，也可显式使用 `--build-profile portable` 构建。

## 验收与厂商

| 证据 | 能证明 | 不能证明 |
|---|---|---|
| 静态检查 | YAML、索引、文档符合规范 | 产品实际可运行 |
| L0 本地 HTTP | 启动服务后的命令断言 | 镜像依赖、云端部署、被跳过的模型调用 |
| L1 真实镜像构建 | 构建和声明的镜像无密钥检查 | 生产 CLI 部署封装或真实云验收 |
| 源码云端运行诊断 | 现有基础沙箱上的准确源码和依赖 | 变更后的 Dockerfile、模板部署 |
| L2 标准部署 | Docker/ACR 部署、READY、新沙箱、外部 CLI/SDK smoke、资源清理 | 未明确执行的全部 HTTP 命令或模型编码 |
| L3 产品/模型 | 记录中的任务和独立验证结果 | 其他源码/版本或上游所有能力 |
| L4 其他厂商 | 实际测试的厂商及工作负载 | 没有配置的其他厂商 |

[2026-10-22 矩阵](../.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json)记录了 46 个源码模板的 Express 镜像/HTTP 与 OpenSandbox 镜像/HTTP 测试通过；[steps 记录](../.agents/evidence/verify/2026-10-22-current-steps-after-backend-qualification.json)对应另一条 Express 构建路径。这些是真实历史测试，保留当时输入和入口。OpenSandbox 使用沙箱内或 bridge HTTP，不能证明后来新增的宿主 `template launch` 或未执行的模型任务。

没有匹配记录不等于平台不支持。查看测试日期、模板输入、provider、构建方式和实际检查内容；命名 API 通过不能推出终端或解释器也通过。历史收据保持原样。

## 文档与目录归属

- 模板 README：CLI/SDK/HTTP 示例、参数、配置、限制、验收和二次开发。
- `docs/design/<name>.md`：设计理由与可行性。
- `template-spec.md`：开发和验收的规范来源。
- `python-client-installation.md`：唯一的配套源码安装步骤。
- `.agents/`：工程决策与日期化验证，不是用户 API 文档。
- `awesome-templates.yaml`：CLI 和[registry 仓库](https://github.com/Alibaba-Agent-Sandbox/registry)
  消费的模板源目录。

旧的 `registry/index.html`、`registry/catalog.json` 不被 CLI、SDK、正式 registry
聚合或 CI 使用，且包含过时的厂商描述，本次退役。网站 UI 归
[website 仓库](https://github.com/Alibaba-Agent-Sandbox/website)，registry 从源仓库
生成公开目录；不要把这些前端或生成目录再复制回来。

[English](using-templates.md)

本地验收清理会保留 Python 验收源码（包括 `e2e_sdk.py`），仅移除生成产物和缓存。源码应留在工作树中供后续 SDK 验收使用。


## 客户端入口兼容性

自定义命令、provider、会话和 `sb.server` 示例显式导入
`from agent_sandbox.api.sandbox import Sandbox`。这个原生异步入口可用于当前
主分支及标准客户端候选版本，避免根入口切换为同步 `Sandbox` 后误用 await。
标准 `Sandbox` / `AsyncSandbox` 与解释器导入属于另一个契约，见
[SDK47](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/47)。

当前极速版使用位置模板参数；本页及模板 README 的示例与上述 CLI 源码提交一致。旧版原生 CLI 的参数不同，应使用对应版本的帮助。

| 操作 | 当前极速版入口 |
| --- | --- |
| 脚本创建 | `abx create <template-id> --detach` |
| Shell | `abx exec --cwd /tmp <sandbox-id> sh -c 'echo hello'` |
| 清理本任务沙箱 | `abx kill <sandbox-id>` |

`template deploy`、命名命令 `abx run`、上传/下载仍为项目扩展。标准 create 不带 `--detach` 会打开 PTY。模板源代码和厂商验收等级不因示例更新而改变。
