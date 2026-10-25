# 模板开发、上架与验收

这是本仓库模板的规范。[docs/template-spec.md](./template-spec.md) 是同一份内容的英文版。两份不一致时，以英文版为准。

`docs/acceptance.md` 只保留指向这里的入口。`_skeleton/` 是符合本规范的目录示例，不是目录条目。

后续模板工作依赖的工具：

| 工具 | 作用 |
|---|---|
| `scripts/check_template.py` | 静态检查。目录符合本规范时退出码为 0。 |
| `scripts/public_launch_e2e.py` | 已安装 CLI 源码启动、宿主 CLI/Python/HTTP smoke，以及 Express/OpenSandbox 自有资源独立清理。 |
| `scripts/run_local_e2e.py` | 对每个带 `commands.py` 和 `e2e_test.py` 的目录做 L0，并运行检查器。 |
| `scripts/image_size_report.py` | 打印本地镜像每一层的大小（`docker history`）。 |

项目治理与完成条件见[项目规范](project-standards.zh-CN.md)，写作与翻译要求见
[文档规范](documentation-standards.zh-CN.md)。

## 目录布局

一个模板是仓库根目录下的一个目录。目录名、`template.yaml` 的 `name`、`awesome-templates.yaml` 里的 `path` 是同一个字符串。产品名符合 `^[a-z0-9][a-z0-9-]*$`。下划线目录只有 `_skeleton`，它不会被安装。

```
<name>/
├── template.yaml
├── Dockerfile
├── commands.py
├── e2e_test.py
├── README.md
├── README.zh-CN.md
└── evidence/                 # 按日期保存尝试，通过回执单独保留
    └── express-<YYYY-MM-DD>.json
docs/design/<name>.md         # 每个产品模板都要有
```

| 文件 | 内容 |
|---|---|
| `template.yaml` | 下面的 schema。 |
| `Dockerfile` | 阿里云基础镜像、钉死的安装、`WORKDIR /home/user/app`、`USER user`。不写 `CMD` 或 `ENTRYPOINT`。 |
| `commands.py` | `@command` 函数。`start()` 只出现在 `if __name__ == "__main__"` 里。 |
| `e2e_test.py` | 本地冒烟。读取 `E2E_BASE_URL`。 |
| `README.md` | 英文章节，见下表。 |
| `README.zh-CN.md` | 同样的章节，中文。 |
| `docs/design/<name>.md` | 事前分析。从 [docs/design/_TEMPLATE.md](./design/_TEMPLATE.md) 复制。 |
| `evidence/*.json` | 脱敏机器记录。提供方／日期资格文件必须运行及独立清理通过；失败尝试使用单独的 attempt 文件名保存，不作为提供方通过。 |

提供方内置运行时以托管目录引用表示，不复制成源码配方；保留其提供方身份与实际使用契约，见下文托管条目。

## template.yaml

```yaml
name: my-template
version: "1.0.0"
description: "一句话。"
author: "github-handle"
license: Apache-2.0
spec_version: 5

base: "fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>"
generation: 2
start_cmd: "agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py"
ready_cmd: "agent-sandbox-server healthcheck --port 9000"

resources:
  cpu: 2          # vCPU
  memory: 2048    # MB

ports:
  - 9000

tags: [example]
priority: P2      # P0、P1 或 P2
wave: other       # 1、2、3 或 other

provides:
  app:
    protocol: agent-sandbox-server
    version: 2
    port: 9000
    operations: [commands.list, commands.run]
env:
  SOME_API_KEY: ""

smoke:
  - command: hello
    args:
      name: Express
    expect: "Hello, Express!"
```

| 字段 | 规则 |
|---|---|
| `name` | 与目录名相同。 |
| `description`、`version`、`author`、`license` | 非空字符串。 |
| `spec_version` | 仅支持整数 `5`，旧版及未知版本明确拒绝，不提供兼容模式。 |
| `base` | 字符串。占位符 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，或钉死的 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:vX.Y.Z`。不是 mapping。 |
| `generation` | 整数 `2`。 |
| `start_cmd` | `agent-sandbox-server serve`，并带上镜像里 `commands.py` 的路径。 |
| `ready_cmd` | `agent-sandbox-server healthcheck`，并带上端口。 |
| `resources.cpu` | 正整数，单位 vCPU。 |
| `resources.memory` | 正整数，单位 MB。 |
| `env` | mapping。以 `API_KEY`、`SECRET`、`TOKEN`、`PASSWORD`、`CREDENTIAL` 或 `PRIVATE_KEY` 结尾的键，值必须是空字符串。 |
| `ports` | 包含 `9000`。 |
| `tags` | 非空字符串列表。 |
| `priority` | `P0`、`P1` 或 `P2`。模板已经在 `docs/template-backlog.json` 里时，与那里的优先级一致。 |
| `wave` | `1`（整份产品能在极速版跑）、`2`（文中写明的切片）、`3`（工作负载要别的提供方）、或 `other`。 |
| `provides` | 模板提供的全部服务，包含协议、版本、端口与操作；启动后返回全部声明端点，无需选择工作流。 |
| `smoke` | `{command, args, expect}` 列表，由 `scripts/public_launch_e2e.py` 执行。`args` 的键是命令参数。可选的字符串 `expect` 在去掉首尾空白后比较；没有 expect 时，成功非空响应只证明调用链。 |

`template launch` 准备模板、创建沙箱、执行 `start_cmd`，执行 `ready_cmd` 并解析全部声明服务的端点。内置 server v2 协议额外检查健康及已声明的命令发现；其他协议提供端点，解析出 URL 不代表其协议已验证。
注册命令和工具在启动后可用；需要业务参数的任务按需调用，不会逐个自动执行。
从准备好的引用另建实例，不会继承原实例的运行进程。

命名命令不写在 `template.yaml` 里，在 `commands.py` 注册。

## 可选应用部署（规范版本 5）

所有输入使用封闭的 [spec/template-v5.schema.json](../spec/template-v5.schema.json)。
`application` 可省略；存在时保留原部署拓扑、hooks、持久状态和非空 smoke 期望语义。
模板启动与 application 应用部署是独立操作，两者不能互相替代。
未知字段、旧版本和非法拓扑组合检查失败，不提供旧版兼容。

`template.yaml` 是唯一用户配置入口，不增加 `agent-app.yaml`。
应用部署由显式 CLI 操作触发；安装模板、导入模块、构建 sandbox 镜像和
`ProviderSandbox.create()` 都不执行应用 hooks 或部署 FC 函数。Sandbox provider 与应用
部署 adapter 保持独立接口。

已做语法检查的[本地示例](examples/application-local/template.yaml)描述现有
`agents-cli` 本地 API profile，不代表新镜像验收或持久托管服务。
[外部示例](examples/application-external/template.yaml)演示内嵌 Serverless Devs 项目；
组件版本、角色、镜像、数据库和身份绑定必须在部署前解析并审查。
这些文件不是云端通过证据，也不是可安装的目录条目。

| Application 字段 | 契约 |
| --- | --- |
| `runtime` | `placement: external` 需要 `driver: python-remote-tools`，不能写本地 profile。`in-sandbox` 需要 `driver: sandbox-local-api`，profile 为 `server-core-agents`。Profile 不证明全部本地接口已开放。 |
| `gateway` | `placement: fc-web` 表示外部网关；`client-direct` 仅适用于 sandbox 内 runtime。 |
| `deployment` | 直连只能是 `{adapter: none}`。FC 需要 `adapter: serverless-devs-fc3`、`accessRef`、`toolchainLock`，以及 `inline`、`project` 二选一。Access 引用是名称，不是凭据。 |
| `deployment.inline` | Serverless Devs v3 mapping，包括 `edition: "3.0.0"`、`name`、`resources`。资源键限 `gateway`、`worker`、`dispatcher`；外部 runtime 三者都必需。每项包含精确 `component: fc3@X.Y.Z`、非空 `props`，可选 `actions`。Adapter 提取 mapping 生成冻结的 `s.yaml`，用户无需再维护一份 YAML。Schema 不验证 FC 属性、组件可用性、IAM 或实际代码。 |
| `deployment.project` | 高级替代方式：手写且已审查的 Serverless Devs 项目的相对路径。完整引用源码树都属于部署输入。 |
| `deployment.toolchainLock` | 部署工具版本及完整性锁的相对路径。JSON lock 的格式与验证执行属于 CLI adapter，不属于模板检查器。 |
| `sandbox` | Provider 名称、`lifetime: per-run`、`workspace: exclusive`、非空 `requiredFeatures`。两种模式都需要 `sandbox.lifecycle`；外部还需 `exec.run`、`files.rw`，sandbox 内还需 `ports.url`。能力声明不证明 provider 已支持，也不授予运行权限。 |
| `state` | 外部网关需要 `profile: durable`，`bindingRef` 必须指向 `bindings` 的键。客户端直连只能是 `{profile: ephemeral}`。 |
| `bindings` | 逻辑名称到凭据或服务引用名称的 mapping，不得写密钥、连接串或签名 URL。直连模式允许为空。 |
| `limits` | 正整数 `maxRunSeconds`、`maxToolSeconds`、`maxConcurrentRuns`、`maxQueuedRuns`、`maxRunsPerMinute`；`maxEventsPerRun >= 5`、`maxOutputBytes >= 1024`。工具预算不能超过任务预算。实际限制由 runtime 执行，检查器不实现准入控制。 |
| `hooks` | 可选 `beforeApply`、`afterReady` 列表，每阶段最多八项。直连本地模式没有部署 hooks，其他阶段名拒绝。 |

每个 hook 包含全局唯一 `id`、`executor: host-command`、argv 数组、相对 `cwd`、
`1..900` 的 `timeoutSeconds` 和环境变量名称 `envAllowlist`。
部署 adapter 在主机/CI 执行已审查的 argv 并限制输出；检查器只读取配置。
`beforeApply` 只验证冻结输入，不能重新构建或修改产物；`afterReady` 在发布前验证候选。
它们不是 sandbox 启动 hooks。Serverless Devs 原生 actions 与表达式也是可执行代码，
需要审查；构建步骤在部署计划冻结前完成。

路径必须是相对路径，不含反斜杠、控制字符或 `..` 段，解析后必须位于模板目录内。
引用的 project、lock 文件与 hook 工作目录必须存在；拒绝符号链接越界。
检查器不将 hook argv 当作 shell 字符串执行。

使用 `python -m pip install -r scripts/requirements-spec.txt` 安装固定检查依赖，
然后运行检查器与 `scripts/test_spec_tools.py`。下文 runtime、镜像、提供方与模型验收
仍独立适用；schema 有效不能认证启动或提升目录状态。

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
| 流式 | 命名命令是一次请求、一份 JSON。实时 stdout 属于进程 API（`sb.commands.stream`、`abx exec`），不属于 `@command`。返回完整文本，或写文件后让客户端用 `sb.files` 读取。 |
| 错误 | 缺参或类型不对时函数不会被调用：HTTP 400，正文 `{"error", "type": "ValueError"}`。上游失败时抛 `RuntimeError`（或 `ValueError`）。服务返回 HTTP 500，正文 `{"error": "<message>", "type": "<ExceptionName>"}`。上游非零退出是异常，不是一条成功的字符串。消息里不要带密钥。 |
| 隐藏 | `@command(hidden=True)` 仍可调用，但不出现在 `GET /commands`。 |
| `start()` | 只写在 `if __name__ == "__main__"` 下面。`agent-sandbox-server serve --commands` 会导入这个模块。导入时调用 `start()` 会破坏这条路径。 |
| 上游 | 产品命令的函数体执行该产品自己的非交互 argv。不要把提示词拼进 shell 字符串。argv 用列表传递。 |

`GET /commands` 返回 `{"commands": [{"name", "description", "args": [{"name", "type", "required", "default", "description"}]}]}`。

### 认证令牌

`/health` 不要求 server token；提供方网关仍可能认证该请求。health 成功不证明命名命令认证或模型配置正确。

进程启动时读取 `ABX_SERVER_TOKEN`。变量非空时，受保护的请求需要带 `Authorization: Bearer <token>` 或 `X-Access-Token: <token>`。在 `env` 里声明这个名字，值为空字符串。真正的值必须在服务进程启动前传入。创建时注入（`abx create --env` 或 `ProviderSandbox.create(envs=...)`）仅适用于提供方实际使用这些值启动服务的情况，不能重新配置预热进程。参考[运行环境配置](runtime-environment.zh-CN.md)，检查实际服务并选中已配置端口。

变量未设置时应用允许匿名调用；提供方网关认证仍单独处理。客户端保留提供方的网关访问头，把显式应用令牌放入 `Authorization: Bearer <token>`，并在同名头未被占用时补充已有应用 `X-Access-Token` 头。认证失败会直接返回，不会自动匿名重试。设置 `ABX_SERVER_TOKEN` 的模板必须说明：项目 Python API 使用 `await sb.application_client(port, token=...)`，CLI 命名命令使用 `ABX_SERVER_TOKEN`。

## 客户端如何调用

CLI，在 `abx --provider alicloud-express template launch <source> --yes` 已启动应用之后：

```bash
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` 的值是字符串。数字和布尔用 `--json-args`。`abx exec` 是 shell 或 argv，不是命名命令。

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
`sb.commands.run` 是进程 API。关闭连接不会删除沙箱；用完执行 `abx kill <sandbox-id>`
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

Verified 表里出现 `alicloud-express` 时，检查器要求存在上述形状的文件（文件名 `evidence/express-<date>.json` 或 `evidence/alicloud-express-<date>.json`），并且 `via` 同时有 `cli` 和 `sdk`，且 `ok` 都为 true。其他提供方使用 `evidence/<provider>-<date>.json`。

### Verified on

根 README 的目录表有 Verified on 列。单元格链接历史提供方运行；阅读回执中的准确源码、入口、检查和日期，不把它当作当前默认入口通过。空白表示没有匹配记录，不等于不支持。失败尝试不得写入该列或作为提供方资格；脱敏结果可用单独的 attempt 文件名保留，提供方／日期通过文件必须运行及独立清理成功。

模板 README 的 `## 已验证` 明确说明已有证据的准确范围。作者自填通过声明不能证明测试实际执行；静态检查器不接受手填提供方通过表。参见[启动验证](workflows.zh-CN.md)。

## 安全

- 密钥的值不进入镜像、`template.yaml`、Docker 历史或证据 JSON。
- `env` 只声明名字和空字符串。真正的值在使用它的进程启动前明确传入；创建请求不能更新已有进程。
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
| Verified | 已验证 |
| Secondary development | 二次开发 |
| Contributing | 贡献 |
| Issues | 问题反馈 |
| License | 许可证 |

CLI 一节要有 `abx run` 示例。SDK 一节导入 `ProviderSandbox`，通过 `application_client` 获取应用客户端，并调用 `client.commands.run`。命令参考是带参数的表。非阿里云基础镜像再加 `## Base image` / `## 基础镜像`。

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

`abx --provider <provider> template launch <source>` 通过所选提供方已实现的操作准备配方并启动应用。
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

`--all` 检查根目录下所有包含 `template.yaml` 的目录，包括 skeleton。每份清单必须显式填写受支持的 `spec_version`，缺失、格式错误及未知版本均失败。目录索引必须声明 `schema_version: 2`。CI 和 `scripts/run_local_e2e.py` 使用同一项完整检查，任一违规都会导致失败。

违规代码包括 `required-file`、`readme-section`、`base-image`、`dockerfile-cmd`、`dockerfile-user`、`yaml-field`、`commands-start`、`verified-evidence`、`pinned-version`、`readme-client`、`secrets`。`RUN` 上两种服务端钉都没有时，`pinned-version` 失败。spec_version 4 的 SDK 章节没有写 `agent-sandbox-client`，或 README 让读者 `pip install agent-sandbox` 时，`readme-client` 失败。

## 原生部署维护

原生云准备使用[平台步骤](platform-steps.zh-CN.md)：准备空闲 provider 模板，再保留
原清单并复用当前完整公开启动消费者。`express_e2e.py` 仅保留外部控制器使用的有界
进程监控，不再提供第二套部署／创建／恢复 CLI。历史回执保留其原源码范围；清理
成功不能把原应用失败改成通过。

## 提供方托管条目

`managed_templates` 是与可安装源码 `templates` 分开的目录命名空间。每条记录只包含 `name`、`provider`、`template_id`、`kind: provider-managed`、`documentation`、`historical_evidence`、`spec_version: 5` 和 `provides`。平台标识绑定其 Provider；没有应用服务时 `provides` 为 `{}`。无需声明工作流，创建后使用该平台实际支持的接口。

Exec 启动必须有明确的 `start_cmd`。托管记录不包含该字段，因此拒绝
`startup: exec`。请选择 `none` 或提供方确实支持的原生 `entrypoint` 路径；
元数据本身不授予提供方启动能力。

托管 ID 没有此仓库拥有的 Dockerfile、镜像版本、commands.py 或构建上下文，因此不参与源码模板的镜像选择、steps 生成和部署检查。原生模板引用本身不证明运行时身份不可变。实测必须绑定实际输入、消费入口和网络路径，核对准确的操作语义，并独立确认自有资源清理。Shell 执行不能认证原生或统一解释器。参见 [base](managed/base/README.zh-CN.md) 和 [code-interpreter-v1](managed/code-interpreter-v1/README.zh-CN.md)。

同一天验证新版本时，使用独立的 express-YYYY-MM-DDTHHMMSSZ.json 回执，保留旧日期文件。提供方资格必须匹配当前清单版本，且 passed 和 cleanup_verified 都为 true，并含真实 CLI/SDK 成功调用；旧版本不能认证变更后的模板。

含 `application` 的 spec4 清单必须为 smoke 显式填写非 null 的 `expect`，支持字符串、数值、布尔、对象和数组，并使用结构化比较。旧 schema 输入直接拒绝。


托管目录通过 `python scripts/check_managed_catalog.py` 检查准确字段、与源码目录不重名、服务声明、双语 14 个有序 README 章节，以及本地历史证据身份。`historical_evidence` 只链接原始回执，其内容不授予当前启动认证。只有完整、输入匹配且来源受独立信任的回执才能认证路径，参见[启动验证](workflows.zh-CN.md)。托管 ID 仍排除在源码镜像选择／steps 之外。[Desktop](managed/desktop/README.zh-CN.md)和[OpenSandbox 解释器](managed/opensandbox-code-interpreter/README.zh-CN.md)说明各条目的条件、实际证据范围和剩余产品门槛。

Dockerfile 固定已发布的 `agent-sandbox-server` 版本；CI 直接安装该依赖并检查实际版本，不再通过 Git 归档或注入 wheel 回退。
