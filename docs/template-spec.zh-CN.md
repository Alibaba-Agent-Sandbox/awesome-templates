# 模板 YAML v1 规范

[English](template-spec.md)

`template.yaml` 声明要准备和部署的资源。此格式需要匹配的开发版 CLI；已发布 CLI 0.5.10 未实现该规范。

## 目录布局

资源和值写在 `template.yaml`，镜像安装步骤写在 Dockerfile，业务行为写在源码。可选 `registry.yaml` 提供上架信息和初始化表单。本地运行不会重新读取 Registry 默认值。

## template.yaml

```yaml
specVersion: 1
name: python-hello
vars:
  location: cn-hangzhou
sandbox:
  agent:
    provider: alicloud-express
    template:
      region: ${vars.location}
      buildConfig:
        dockerfile: ./Dockerfile
      generation: 2
      cpu: 2
      memorySize: 2048
      startCommand: agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py
      readyCommand: agent-sandbox-server healthcheck --port 9000
```

| 字段 | 含义 |
| --- | --- |
| `specVersion` | 整数 `1`。 |
| `name` | 项目名称，1–63 个小写 ASCII 字母、数字和连字符。 |
| `vars` | 可选、完全由作者命名的复用值；没有保留镜像变量名，也可直接写字面值。 |
| `sandbox.<名称>` | 命名 Sandbox 资源，包含 Provider、模板、可选静态卷和资源动作。 |
| `sandbox.<名称>.template` | Provider 属性；Express 使用 `region`、`image`、`generation`、`cpu`、`memorySize`、`diskSize`、网络、日志、仓库和模板原生命令。 |
| `sandbox.<名称>.template.reference` | 借用已有原生模板。只可同时填写地域 `region`；不更新或删除借用资源。 |
| `sandbox.<名称>.volumes` | 命名静态卷。`props` 创建拥有卷，`reference` 借用已有卷，`retain: true` 在移除时保留拥有卷。卷共用 `template.region`。 |
| `serving.<名称>` | 原生组件标识、`props` 和可选资源动作。 |

Sandbox 与 Serving 逻辑名全局唯一。不接收 `access`、`application`、`deployment`、用户自定义 `outputs`、`instance`、`runtimeConfig`、`sandboxConfig` 或通用 `build`/`builds`。凭据复用现有配置。CPU/内存组合、地域和账号准入仍由 Provider 校验；未填写的 API 属性不会被猜测默认值填充。

完整类型见[嵌套字段表](template-fields.zh-CN.md)和[Schema](../spec/template-v1.schema.json)。

## 构建来源与镜像语义

`buildConfig` 只有两种互斥分支：`dockerfile` 配可选 `context`，或者 `steps`。不接受空对象或单独 `context`。路径相对 `template.yaml` 所在目录；省略 `context` 时使用 Dockerfile 所在目录。整段省略时不会扫描并自动构建本地 Dockerfile。

| 配置 | 结果 |
| --- | --- |
| 只有 `image` | 使用已有镜像准备模板。 |
| `image` 与 `buildConfig.dockerfile` | 构建并推送到该镜像地址，再准备模板。未填地址时必须由已有构建配置提供目的仓库。 |
| `image` 与 `buildConfig.steps` | 以该镜像为输入执行原生模板步骤，结果是模板 ID；不承诺把步骤后的 OCI 镜像导出并推回输入地址。 |
| `reference` | 复用已有模板，不构建或更新。 |

原生步骤为 `type: USER|WORKDIR|ENV|RUN` 和 `args: string[]`。ENV 按键值成对填写；USER 接受用户名及可选布尔字符串 sudo 标志；RUN 接受命令及可选执行用户。运行秘密不能放进镜像 ENV 或模板构建步骤。

Express 的 `registryConfig` 按需覆盖拉取认证、TLS 和仓库网络。不需要时整段省略。普通 Linux 和可识别的 ACR 镜像无需重复填写 `osType`、仓库类型或 ACR 实例。存储客户端由 Dockerfile 或基础镜像准备；安装不等于创建卷、挂载或授权。必要镜像复制和注入由 Provider 承接，不再暴露第二套高级构建配置。

## Serving 与动作

```yaml
serving:
  api:
    component: serverless-devs/fc3@0.1.26
    actions:
      pre-deploy:
        - component: serverless-devs/fc3@0.1.26 build --dockerfile ./server/Dockerfile --context ./server
    props:
      region: cn-hangzhou
      functionName: sandbox-api
      runtime: custom-container
      code: ./server
      customContainerConfig:
        image: registry.example/project/api:release-1
        port: 9000
      environmentVariables:
        SANDBOX_TEMPLATE_ID: ${resources.agent.output.templateId}
```

示例镜像地址是占位符，须改成自己有推送权限的仓库。`serverless-devs/` 前缀选择组件执行适配器，原生 `fc3@0.1.26` 决定 `props`。FC 的 build 与 deploy 推送行为不同；引用已构建远端镜像应走组件支持的跳过推送路径，不能仅删除构建动作就认为不会推送。

动作在部署发起端执行。`run` 执行 Shell，`component` 在当前资源上下文调用原生组件命令，可选 `path` 指定工作目录。`pre-deploy` 在资源部署前，`success-deploy` 在资源就绪后，`fail-deploy` 在失败时，`complete-deploy` 在两种结果后执行。Sandbox 成功需查询模板就绪，不能仅收到构建请求受理就成功。输出引用确定依赖顺序，未知资源和循环引用在部署前失败。

## 模板与动态实例

部署准备可复用模板和静态卷。业务代码、SDK 或 `abx sandbox create --template <template-id>` 创建实例并选择运行环境变量、租期和挂载。`startCommand` 与 `readyCommand` 保留模板准备/快照阶段原生语义，不是每个动态实例的钩子。恢复的预热进程不会自动重新读取创建时环境变量。应用启动与模型凭据见[运行环境指南](runtime-environment.zh-CN.md)。

镜像默认值是普通 Dockerfile ENV；空凭据名称不含秘密。运行时私有值需在创建实例时或通过业务运行时显式注入。端口声明、进程监听、网络访问和业务协议分别配置，声明端口不等于公开或认证业务 API。

## 配置与上架

使用单个 JSON 兼容 YAML 1.2 Core 文档，键为字符串，不允许重复键、别名或自定义标签，UTF-8 最大 1 MiB。静态目录工具不求值 `${env('NAME')}`、`${vars.key}` 或资源输出表达式。

可选 `registry.yaml` 包含 `specVersion`、`name`、`version`、双语 `description`、`author`、`license`、`tags`、双语 `readme` 和 `parameters`。每个参数用 JSON Pointer `target` 指向实际配置值，并提供双语 `title`。敏感参数另设 `environmentVariable`，目标必须对应 `${env('NAME')}`。初始化修改实际本地值或私有来源；之后运行只依赖 `template.yaml` 和它显式引用的来源。

## 阿里云基础镜像

默认官方配方保留非 root 用户 `user`，资源在清单中声明。平台限制和应用需求分别说明。基础镜像是：

```
fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
```

已安装的 CLI 暂存官方源码配方，按所选 provider 配置或 CLI 默认值解析受支持的
`<region>`、`<tag>`。配方直接安装固定的已发布服务包，不要求生成 wheel、
SDK 源码归档或宿主 Python checkout。源码 checkout 不变；不会自动解析其他镜像占位符，
portable profile 由调用方显式选择。实际构建输入进入回执。

默认 Express 配方不能用 `CMD` 或 `ENTRYPOINT` 替换平台入口，保留 generation2 的启动与就绪配置。
显式 portable profile 是单独审查的配方，不是自动回退。

`Dockerfile` 的形状：

```dockerfile
FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive

# 重的工具放在前面的一层（一条 RUN，钉死版本，pip --no-cache-dir，清掉 npm cache）。
# commands.py 是最后一次 COPY，改命令不会重建那一层。
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"

# 其他安装同样钉死：pip name==X.Y.Z，npm package@X.Y.Z。
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
```

### 已发布的 `agent-sandbox-server` 依赖

`RUN` 必须直接安装一个准确且实际已发布的版本，例如：

```dockerfile
RUN pip install --no-cache-dir --index-url https://pypi.org/simple "agent-sandbox-server==0.4.0a6"
```

不使用 Git 归档回退、注入 wheel 或独立的 `server-sdk.commit`。直接 Docker 构建和
provider 准备都消费同一声明依赖。检查器验证固定版本声明，镜像和实际运行验收独立
读回已安装版本；声明本身不证明安装或启动通过。

每次 `pip install` 都加 `--no-cache-dir`。npm 安装在同一层里清掉缓存（`npm cache clean --force`）。

### 镜像层

把软件包安装放在靠前的层，`COPY commands.py` 放在最后。2026-10-15 这台机器同时向 `registry.cn-hangzhou.aliyuncs.com` 推送了多份模板镜像。`ss` 显示到仓库的连接 `rwnd_limited` 大约 98.8%（受接收窗口限制，不是往返时延：`minrtt` 不到 1 ms）。一条上传大约 35 KB/s，另一条在 8 秒内 `bytes_sent` 没有增加。镜像大约 0.9–1.2 GB。它们在本地与基础镜像 `v0.0.49` 的两层（大约 632 MB，主要是一层 606 MB 的 rootfs）共享摘要，但每次 harness 推送都使用新的 ACR 仓库，跨仓库挂载基础层并没有保证，基础层可能被再传一次。

`docker history` 的大小是未压缩的层差异。仓库存的是压缩后的 blob，每个 blob 是一次请求。把一个 CLI 拆成几十个小 `COPY` 层会让每个 blob 都多一次往返。`python3 scripts/image_size_report.py <image>` 按层打印。加上 `--base` 可以看到还有多少 rootfs 摘要仍属于基础镜像。

```bash
python3 scripts/image_size_report.py <本地镜像> \
  --base fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime/base:v0.0.49
```

只有硬依赖使平台镜像不可用时，才允许其他基础镜像。这时 README 要有 `## Base image`，用一段话说明原因。检查器接受这个例外。「原来就有一份 Dockerfile」不是原因。

上游 CLI 和库钉到精确版本。`latest` 或未钉版本的 `npm install -g` 是不符合规范。

## commands.py

导入服务端 SDK 并注册命名命令：

```python
from __future__ import annotations

import os

from agent_sandbox.server import command, start


@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
```

| 规则 | 说明 |
|---|---|
| 导入 | `from agent_sandbox.server import command`。本地进程要提供 HTTP 时再导入 `start`。可以用标准库。不要再引入第二套 HTTP 服务。 |
| 名字 | `@command("name")`，或省略第一个参数时用函数名。包装产品时用上游 CLI 的动词，`snake_case`（`claude`、`codex_exec`）。 |
| 参数 | 来自函数签名。`int`、`float`、`bool` 保持类型，其余是字符串。没有默认值的参数是必填。 |
| 返回值 | 一个可 JSON 序列化的值：`str`、`int`、`float`、`bool`、`None`、`list` 或 `dict`。HTTP 正文是 `{"result": <value>}`。不要返回生成器。 |
| 流式 | 命名命令是一次请求、一份 JSON。实时 stdout 属于进程 API（`sb.commands.stream`、`abx sandbox exec`），不属于 `@command`。返回完整文本，或写文件后让客户端用 `sb.files` 读取。 |
| 错误 | 缺参或类型不对时函数不会被调用：HTTP 400，正文 `{"error", "type": "ValueError"}`。上游失败时抛 `RuntimeError`（或 `ValueError`）。服务返回 HTTP 500，正文 `{"error": "<message>", "type": "<ExceptionName>"}`。上游非零退出是异常，不是一条成功的字符串。消息里不要带密钥。 |
| 隐藏 | `@command(hidden=True)` 仍可调用，但不出现在 `GET /commands`。 |
| `start()` | 只写在 `if __name__ == "__main__"` 下面。`agent-sandbox-server serve --commands` 会导入这个模块。导入时调用 `start()` 会破坏这条路径。 |
| 上游 | 产品命令的函数体执行该产品自己的非交互 argv。不要把提示词拼进 shell 字符串。argv 用列表传递。 |

`GET /commands` 返回 `{"commands": [{"name", "description", "args": [{"name", "type", "required", "default", "description"}]}]}`。

### 认证令牌

`/health` 不要求 server token；提供方网关仍可能认证该请求。health 成功不证明命名命令认证或模型配置正确。

应用在进程启动时读取 `ABX_SERVER_TOKEN`，受保护请求使用 `Authorization: Bearer <token>` 或 `X-Access-Token: <token>`。普通模板通过 `run.py` 生成或接收令牌，创建实例并显式启动应用，再验证带认证的命令发现。凭据不写入模板准备命令或镜像层。见[运行环境配置](runtime-environment.zh-CN.md)。

变量未设置时应用允许匿名调用；提供方网关认证仍单独处理。客户端保留提供方的网关访问头，把显式应用令牌放入 `Authorization: Bearer <token>`，并在同名头未被占用时补充已有应用 `X-Access-Token` 头。认证失败会直接返回，不会自动匿名重试。设置 `ABX_SERVER_TOKEN` 的模板必须说明：项目 Python API 使用 `await sb.application_client(port, token=...)`，CLI 命名命令使用 `ABX_SERVER_TOKEN`。

## 客户端如何调用

CLI，在 `abx --provider alicloud-express deploy <source> --yes` 已启动应用之后：

```bash
abx sandbox command run <sandbox-id> hello --arg name=Ada
abx sandbox command run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx sandbox exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` 的值是字符串。数字和布尔用 `--json-args`。`abx sandbox exec` 是 shell 或 argv，不是命名命令。

Python SDK。PyPI 上的客户端发行名是 `agent-sandbox-client`。导入名仍是 `agent_sandbox`。`pip install agent-sandbox` 会装上一个无关项目。

按 [Python 客户端安装](./python-client-installation.md) 安装兼容的已发布版本。
连接前面已启动的实例，并使用相同的应用令牌：

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main() -> None:
    sb = await ProviderSandbox.connect("<sandbox-id>", provider="alicloud-express")
    try:
        client = await sb.application_client(9000, token=os.environ["ABX_SERVER_TOKEN"])
        try:
            print(await client.commands.run("hello", name="Ada"))
        finally:
            await client.aclose()
        print((await sb.commands.run("python3 -c 'print(1)'")).stdout)
    finally:
        await sb.close()

asyncio.run(main())
```

`client.commands.run` 把关键字参数作为 `POST /commands/hello` 的 JSON 正文并返回 `result`；
`sb.commands.run` 是进程 API。关闭连接不会删除沙箱；用完执行 `abx sandbox delete <sandbox-id> --yes`
删除自己创建的实例，并另行核对准备的模板和镜像。验收记录源码提交及实际安装版本。

本地 L0 不创建云沙箱。`scripts/run_local_e2e.py` 启动 `python3 commands.py`，设置 `E2E_BASE_URL`，再运行 `e2e_test.py`。该测试可以对 `E2E_BASE_URL` 发 HTTP。云验收必须调用实际选定的 CLI/SDK/HTTP 入口。

### HTTP POST 契约

每个 README 在 Python SDK 章节后包含独立的“快速开始（HTTP POST）”章节。
使用与 CLI/SDK 相同的任务，给出沙箱端口 URL、`POST /commands/<name>`、
`Content-Type: application/json`、直接参数 JSON（不嵌套 args）及 `{"result": ...}`。
说明必填值、默认值、类型、范围，以及参数错误 400、认证失败 401、命令不存在
404、执行错误 500。分别说明 ABX_SERVER_TOKEN 与提供方网关认证；示例只使用
环境变量或占位符，不得出现真实凭据。

命名命令在执行完成后整体返回。`sb.application_client(..., timeout=...)` 设置客户端 HTTP
超时，因此命令执行截止时间应采用 command_timeout 或 timeout_s 等独立参数名。
客户端超时不保证取消服务端执行。后台运行、重连与取消使用进程 API。
编程 Agent 的 L3 必须修改已有源码、创建新产物，并在沙箱内独立运行测试；
远端服务的产物验证必须走远端 files/process API，不能读取宿主文件冒充通过。
仅回复 marker 不构成 L3。

## 测试级别

这些保留的证据标签描述测试范围，不是晋升顺序或平台支持等级。仅记录实际执行的检查及准确启动命令、端点和源码输入；旧证据保留历史范围。

| 级别 | 通过的含义 |
|---|---|
| L0 | `python3 scripts/run_local_e2e.py` 能启动该模板，且 `e2e_test.py` 退出码为 0。某个用例因缺少模型密钥可以打印 SKIP。这个 SKIP 不是该 Agent 已验收。本地脚本会设置 `E2E_RUN_LLM=0`。 |
| L1 | `docker build` 成功，日志里能看到钉死的上游版本。 |
| L2 | 记录的 Express 源码准备／启动就绪，声明的 smoke 经过所记录宿主入口调用并断言，自有清理独立确认。记录准确源码、CLI/SDK 版本、启动路径与检查；保留历史 deploy 回执，不声称它测试了后来的 launch 代码。 |
| L3 | 用兼容凭据运行真实模型/产品。编程 Agent 必须修改已有源码、创建新产物，并在沙箱内独立运行测试；远端文件/进程 API 验证产物，回复 marker 不足以通过。`E2E_REQUIRE_LLM=1` 时空密钥是失败。 |
| L4 | `e2b`、`opensandbox`、`alicloud-container` 或 `cubesandbox`，只有在该提供方上真实跑过之后。 |

当前默认验收入口是[公开源码启动](public-launch-testing.md#中文)：先调用已安装 CLI，
再从宿主 CLI/Python/HTTP 验证应用，并独立核对沙箱、准备的模板及镜像清理。
失败尝试分开保留，`PARTIAL` 不算通过。旧固定版本云流程仅保留为[历史说明](canonical-express-review.zh-CN.md)。

以下是目录检查器仍读取的旧版日期回执格式。它保留原源码、调用路径和清理范围，
不是新的 public-launch 报告格式，也不证明后来的默认入口：

```json
{
  "provider": "alicloud-express",
  "date": "2026-10-15",
  "template": "my-template",
  "template_version": "1.0.0",
  "sdk_version": "0.3.0",
  "cli": "abx",
  "passed": true,
  "cleanup_verified": true,
  "commands": [
    {"name": "hello", "via": "cli", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.4},
    {"name": "hello", "via": "sdk", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.3}
  ]
}
```

Express 历史回执使用 `evidence/express-<date>.json` 或 `evidence/alicloud-express-<date>.json`；其他提供方使用 `evidence/<provider>-<date>.json`。静态检查器不会根据本地提交的回执认证提供方，即使其中字段声明成功。

### Verified on

根 README 的目录表有 Verified on 列。单元格链接历史提供方运行；阅读回执中的准确源码、入口、检查和日期，不把它当作当前默认入口通过。空白表示没有匹配记录，不等于不支持。失败尝试不得写入该列或作为提供方资格；脱敏结果可用单独的 attempt 文件名保留，提供方／日期通过文件必须运行及独立清理成功。

模板 README 面向使用者；验证报告、历史验收、开发说明和测试分层叙述放在工程记录、设计或贡献指南中，不是 README 必需章节。原始证据及上述验收门禁保持不变。作者自填通过声明不能证明测试实际执行；静态检查器仍拒绝手填提供方通过表。参见[启动验证](workflows.zh-CN.md)。

## 安全

- 密钥的值不进入镜像、`template.yaml`、Docker 历史或证据 JSON。
- 创建实例时的 `envs` 只声明名字和空字符串。真正的值在使用它的进程启动前明确传入；创建请求不能更新已有进程。
- 日志和报告不包含秘密或原生资源标识。公开运行器私下保留原始子进程诊断，只导出受控检查标签、稳定错误码和数值 HTTP 状态。
- 不要提交 `.env`、云凭证或 `Dockerfile.abx-build`。

## README 章节

`README.md` 和 `README.zh-CN.md` 按这个顺序使用这些标题。检查器按标题原文匹配。

| 英文 | 中文 |
|---|---|
| What it does | 做什么 |
| Stack | 技术栈 |
| Problem solved | 解决的问题 |
| Quick start (CLI) | 快速开始（CLI） |
| Quick start (Python SDK) | 快速开始（Python SDK） |
| Quick start (HTTP POST) | 快速开始（HTTP POST） |
| Command reference | 命令参考 |
| Configuration | 配置 |
| Resources | 资源 |
| Contributing | 贡献 |
| Issues | 问题反馈 |
| License | 许可证 |

托管 Managed Agents API 应用将 Python SDK 标题替换为 `Quick start (Python HTTP client)` / `快速开始（Python HTTP 客户端）`，如实展示使用 `httpx` 调用 Gateway；当前不提供专用 Gateway 客户端 SDK。

启动前区分所需平台凭据、应用令牌和模型凭据，并写清模板实际读取的模型、endpoint、API Key 或产品登录配置；不臆造通用于所有上游工具的变量映射。

Managed Agents API 使用显式 `abx deploy` 部署及 Python `httpx` 访问统一 Gateway，列出公开 API 和托管 close/delete 清理。以下客户端要求适用于 ordinary Sandbox templates。CLI 一节要有 `abx sandbox command run` 示例。SDK 一节导入 `ProviderSandbox`，通过 `application_client` 获取应用客户端，并调用 `client.commands.run`。命令参考是带参数的表。非阿里云基础镜像再加 `## Base image` / `## 基础镜像`。

## 上架与验收

目录必须通过 `scripts/check_template.py <dir>` 和 L0，并完成 `docs/design/<name>.md`。
`awesome-templates.yaml` 添加一条：`name`、`description`、`repo`、`path`、`tags`、`author`、`status`。

现有目录标签描述维护归属：`official` 表示本项目维护，`community` 表示外部维护，
`experimental` 标记开发中。测试不会自动晋升标签。标签不证明某个平台、启动方法、终端、
解释器或模型任务可用。

实际组件验收要求保留：

1. CI 中 L0 通过（`python3 scripts/run_local_e2e.py`）。
2. 镜像配方有 L1 记录，包含构建及固定版本。
3. 已实现的 Express smoke 路径有 L2 证据，包含自有资源清理。
4. 声称上游 Agent／模型任务可用前须有 L3 证据；SKIP 不算通过。

按[完成标准](project-standards.zh-CN.md#完成标准)对变更组件运行适用测试和必需 CI；
文档变更不重跑无关云测试。部署／模型验收条件未完成时，Issue 继续开放，不受目录标签影响。
记录准确源码、提供方、调用入口、测试及清理结果。索引只使用当前目录 schema 接受的字段；已退休的能力／验证字段会被拒绝。

`abx --provider <provider> deploy <source>` 通过所选提供方已实现的操作准备配方并启动应用。
文档应说明各提供方的实际使用契约；只有匹配的真实运行记录才能证明该路径已测试。
没有证据本身不等于不支持。

## 贡献

1. 模板已经分析过时，先读 `docs/template-backlog.json` 和 `docs/template-market-survey-2026-10.md` 里对应的一节。
2. 按 `docs/design/_TEMPLATE.md` 写 `docs/design/<name>.md`。
3. 把 `_skeleton/` 复制为 `<name>/`。保留阿里云基础镜像、钉死的服务安装和 README 标题。
4. 注册真正调用上游程序的命令。钉住版本。
5. 按上面的维护归属／开发阶段填写索引标签，测试结果单独记录。
6. 运行 `python3 scripts/check_template.py <name>` 和 `python3 scripts/run_local_e2e.py`。
7. 对要求的平台／入口运行公开源码启动验收，保存每次尝试、断言结果并独立确认自有清理；缺少凭据时该条件仍未完成。
8. 开 PR。正文写明哪些级别通过了。

## 到哪里提 issue

| 主题 | 仓库 |
|---|---|
| 模板行为、目录、本规范、检查器、极速版 harness | [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) |
| `agent_sandbox` 或 `agent_sandbox.server`：API 摩擦、缺陷、缺失的行为 | [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。标题前缀 `[templates]`。写明做了什么、期望、实际、最小复现、提供方、模板 generation、SDK commit。 |
| `abx` CLI | [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。同样的标题前缀和同样结构的正文。 |

先搜索未关闭的 issue。是同一个缺陷就在原 issue 下评论。

## 事前分析

`docs/design/<name>.md` 使用 [docs/design/_TEMPLATE.md](./design/_TEMPLATE.md) 的标题：

- Purpose
- Capabilities
- Exposed API
- How to build
- Express feasibility，其中有一行 `Limiting factor:`
- Risks
- Test plan

Express feasibility 写 `yes`、`slice` 或 `no`，并写出唯一的限制因素（整份产品都能跑时写 `none`）。

## 检查器

```bash
python3 scripts/check_template.py _skeleton
python3 scripts/check_template.py --all
```

`--all` 检查根目录下所有包含 `template.yaml` 的目录，包括 skeleton。每份清单必须显式填写受支持的 `specVersion: 1`，缺失、格式错误及未知版本均失败。目录索引必须声明 `schema_version: 3`。CI 和 `scripts/run_local_e2e.py` 使用同一项完整检查，任一违规都会导致失败。

违规代码包括 `required-file`、`readme-section`、`base-image`、`dockerfile-cmd`、`dockerfile-user`、`yaml-field`、`commands-start`、`verified-evidence`、`pinned-version`、`readme-client`、`secrets`。`RUN` 上两种服务端钉都没有时，`pinned-version` 失败。普通 Sandbox 模板的 SDK 章节没有写 `agent-sandbox-client`，或 README 让读者 `pip install agent-sandbox` 时，`readme-client` 失败。

## 原生部署维护

源码默认通过 Dockerfile 构建。原生 Provider 的 steps API 仍是独立能力；`scripts/prepare_steps.py` 生成工程用 `prepared-steps.yaml`，不是可部署的公开 template.yaml。工程验收先通过原生 API 注册，再用 v1 reference 启动。smoke/priority/wave 在 scripts/template-checks.json，仅用于工程检查，不是用户资源字段。

## 提供方托管条目

目录保留原生 Provider、template.reference、文档及历史证据；引用不代表当前已验证，也不自动获得源码安装和重建能力。
