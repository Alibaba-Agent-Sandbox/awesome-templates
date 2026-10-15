# 模板开发、上架与验收

这是本仓库模板的规范。[docs/template-spec.md](./template-spec.md) 是同一份内容的英文版。两份不一致时，以英文版为准。

`docs/acceptance.md` 只保留指向这里的入口。`_skeleton/` 是符合本规范的目录示例，不是目录条目。

后续模板工作依赖的工具：

| 工具 | 作用 |
|---|---|
| `scripts/check_template.py` | 静态检查。目录符合本规范时退出码为 0。 |
| `scripts/express_e2e.py` | 在 `alicloud-express` 上做 L2。只有通过才写证据，然后删除沙箱和模板。用文件锁串行化 ACR 推送，并在推送没有进展时停掉它。 |
| `scripts/run_local_e2e.py` | 对每个带 `commands.py` 和 `e2e_test.py` 的目录做 L0，并运行检查器。 |
| `scripts/image_size_report.py` | 打印本地镜像每一层的大小（`docker history`）。 |

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
└── evidence/                 # 只在某个提供方通过之后出现
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
| `evidence/*.json` | 机器可读的通过记录。失败的运行不提交。 |

SDK 已经能解析的 OpenSandbox 镜像（`code-interpreter`、`code-interpreter-base`、`desktop`、`playwright`、`vscode`）不要再拷进本仓库。

## template.yaml

```yaml
name: my-template
version: "1.0.0"
description: "一句话。"
author: "github-handle"
license: Apache-2.0
spec_version: 2

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
tested_on: []     # 有通过证据的提供方 id，否则空列表

capabilities: [shell, files, code, ports]

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
| `spec_version` | 目录已经按本文实现时写 `2`。检查器把没有这个字段的目录当作旧模板：`--all` 会列出它们，但不会因此失败。 |
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
| `tested_on` | 已经有通过证据的提供方 id。没有则是空列表。与 README 的 Verified 表是同一组 id。 |
| `capabilities` | `shell`、`files`、`code`、`terminal`、`ports` 的子集。这是给客户端的元数据，本身不开关 HTTP 路由。 |
| `smoke` | `{command, args, expect}` 列表，由 `scripts/express_e2e.py` 执行。`args` 的键是命令参数。字符串 `expect` 在去掉首尾空白后比较。 |

`abx template deploy` 从本文件读取 `generation`、`start_cmd`、`ready_cmd`（命令行标志优先）。在 `alicloud-express` 上，目录里有 `commands.py` 但没写这三项时，默认是 generation 2，以及：

```
agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py
agent-sandbox-server healthcheck --port 9000
```

这三项仍然要写进文件。镜像里的 `commands.py` 如果不在 `/home/user/app/commands.py`，默认路径是错的。

命名命令不写在 `template.yaml` 里，在 `commands.py` 注册。

## 阿里云基础镜像

极速版沙箱以非 root 用户 `user` 运行：2 vCPU，没有 `/dev/kvm`，没有 Docker，没有额外 capabilities，rootfs 大约 10G，出网可用。平台基础镜像是：

```
fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>
```

`<region>` 默认 `cn-hangzhou`，可用 `ALIBABA_CLOUD_REGION_ID` 或 `ABX_BASE_IMAGE_REGION` 覆盖。`<tag>` 默认 `v0.0.49`，可用 `ABX_BASE_IMAGE_TAG` 覆盖。`abx template deploy` 在 `docker build` 之前替换 Dockerfile 里的占位符（`agent-sandbox` 的 `src/api/docker_builder.ts`）。镜像里已有 Python 3.13 和 Node.js 20。

镜像入口不能替换。Dockerfile 不写 `CMD`，也不写 `ENTRYPOINT`。平台执行 `start_cmd`，并用 `ready_cmd` 探测。这两条命令只在 generation 2 上生效。同名 generation 1 模板在带 `start_cmd` 更新时会失败。换一个名字部署，或先删掉 generation 1。`scripts/express_e2e.py` 使用唯一别名，不会删除不是它创建的模板。

`Dockerfile` 的形状：

```dockerfile
FROM fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>

ENV DEBIAN_FRONTEND=noninteractive

# 重的工具放在前面的一层（一条 RUN，钉死版本，pip --no-cache-dir，清掉 npm cache）。
# commands.py 是最后一次 COPY，改命令不会重建那一层。
COPY *.whl /tmp/
RUN if ls /tmp/*.whl 1>/dev/null 2>&1; then \
        pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl; \
    else \
        pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40位hex-sha>.tar.gz#subdirectory=server-sdk"; \
    fi

# 其他安装同样钉死：pip name==X.Y.Z，npm package@X.Y.Z。
WORKDIR /home/user/app
COPY --chown=user:user commands.py .
USER user
EXPOSE 9000
```

### 允许的 `agent-sandbox-server` 钉法

`RUN` 行必须使用下面两种形式之一。检查器两种都接受。只在注释里提到钉不算。

| 形式 | 行 |
|---|---|
| PyPI | `pip install --no-cache-dir "agent-sandbox-server==X.Y.Z"` |
| python-sdk git 归档 | `pip install --no-cache-dir "agent-sandbox-server @ https://github.com/Alibaba-Agent-Sandbox/python-sdk/archive/<40位hex-sha>.tar.gz#subdirectory=server-sdk"` |

`<40位hex-sha>` 是 `Alibaba-Agent-Sandbox/python-sdk` 的完整提交（40 个十六进制字符），不是短 sha。2026-10-15 时 `agent-sandbox-server==0.3.0` 不在 PyPI（`https://pypi.org/pypi/agent-sandbox-server/0.3.0/json` 返回 404）。在该版本发布之前使用归档钉。归档钉更精确：它选中某一次提交，包括 `61c43e0` 及之后的极速版服务端修复。

`ABX_SERVER_SDK_SOURCE` 指向 `server-sdk` 源码树时，`abx template deploy` 会把 `agent-sandbox-server` 的 wheel 注入构建上下文。`if` 分支安装这个 wheel。`else` 分支仍然带上两种钉之一。用 BuildKit 构建，这样没有注入 wheel 时 `COPY *.whl` 也能通过（`DOCKER_BUILDKIT=1`）。

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

进程启动时读取 `ABX_SERVER_TOKEN`。变量非空时，每个请求都要带 `Authorization: Bearer <token>` 或 `X-Access-Token: <token>`。在 `env` 里声明这个名字，值为空字符串。真正的值在 `abx create --env` 或 `Sandbox.create(envs=...)` 时注入。

变量未设置时允许匿名调用。极速版网关仍可能带上沙箱访问令牌。当前 `abx`（`agent-sandbox` main，`#16` 的部署与运行修复）在 401 后会不带该头重试一次。当前 `agent_sandbox.Sandbox.server` 不会把沙箱令牌发给端口 9000。模板若设置了 `ABX_SERVER_TOKEN`，要写明客户端如何把 `token=` 传给 `server_at`。

## 客户端如何调用

CLI，在 `abx create --template <id>` 之后：

```bash
abx run <sandbox-id> hello --arg name=Ada
abx run <sandbox-id> add --json-args '{"x": 1, "y": 2}'
abx sandbox command list <sandbox-id>
abx exec <sandbox-id> -- python3 -c 'print(1)'
```

`--arg` 的值是字符串。数字和布尔用 `--json-args`。`abx exec` 是 shell 或 argv，不是命名命令。

Python SDK。PyPI 上的客户端发行名是 `agent-sandbox-client`。导入名仍是 `agent_sandbox`。`pip install agent-sandbox` 会装上一个无关项目。

```bash
python3 -m pip install agent-sandbox-client
```

```python
import asyncio
from agent_sandbox import Sandbox

async def main() -> None:
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("hello", name="Ada"))  # "Hello, Ada!"
        print((await sb.commands.run("python3 -c 'print(1)'")).stdout)
        print(sb.network.get_url(9000))
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 把关键字参数作为 `POST /commands/hello` 的 JSON 正文，并返回 `result`。`sb.commands.run` 是 shell API。连接已有沙箱用 `await Sandbox.connect(sandbox_id)`。

python-sdk 0.3.0 上，`Sandbox.create_sync`、`Sandbox.connect_sync`、`Sandbox.list_sync`、`Sandbox.kill_by_id_sync` 会抛 `TypeError`（类参数被丢掉）。`await Sandbox.connect` 得到实例之后，`sb.run_sync` 这类实例方法可用。在 [python-sdk#22](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/22) 修复前使用上面的异步构造。

本地 L0 不创建云沙箱。`scripts/run_local_e2e.py` 启动 `python3 commands.py`，设置 `E2E_BASE_URL`，再运行 `e2e_test.py`。该测试可以对 `E2E_BASE_URL` 发 HTTP。所有云上路径使用上面的 SDK。

## 测试级别

只记录通过的级别。README 的 Verified 表和 `tested_on` 只列出通过的提供方。

| 级别 | 通过的含义 |
|---|---|
| L0 | `python3 scripts/run_local_e2e.py` 能启动该模板，且 `e2e_test.py` 退出码为 0。某个用例因缺少模型密钥可以打印 SKIP。这个 SKIP 不是该 Agent 已验收。本地脚本会设置 `E2E_RUN_LLM=0`。 |
| L1 | `docker build` 成功，日志里能看到钉死的上游版本。 |
| L2 | `abx template deploy` 到达 READY，`Sandbox.create(template=<id>)`（或 `connect`）成功，并且每条 smoke 命令都从沙箱外经 SDK 调用并断言。记录提供方 `alicloud-express`、UTC 日期、模板版本、SDK 版本。不记录模板 id。 |
| L3 | 用本环境已有的密钥做一次真实模型或产品调用。提示词要求标记 `ABX_E2E_OK`，输出里包含它。`E2E_REQUIRE_LLM=1` 时空密钥是失败，不是跳过。 |
| L4 | `e2b`、`opensandbox`、`alicloud-container` 或 `cubesandbox`，只有在该提供方上真实跑过之后。 |

`scripts/express_e2e.py <dir>` 是 L2 运行器。只有每条 smoke 命令都经 CLI 和 SDK 通过时，才写 `evidence/express-<YYYY-MM-DD>.json`：

```json
{
  "provider": "alicloud-express",
  "date": "2026-10-15",
  "template": "my-template",
  "template_version": "1.0.0",
  "sdk_version": "0.3.0",
  "cli": "abx",
  "passed": true,
  "commands": [
    {"name": "hello", "via": "cli", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.4},
    {"name": "hello", "via": "sdk", "args": {"name": "Express"}, "ok": true, "result": "Hello, Express!", "duration_s": 0.3}
  ]
}
```

Verified 表里出现 `alicloud-express` 时，检查器要求存在上述形状的文件（文件名 `evidence/express-<date>.json` 或 `evidence/alicloud-express-<date>.json`），并且 `via` 同时有 `cli` 和 `sdk`，且 `ok` 都为 true。其他提供方使用 `evidence/<provider>-<date>.json`。

### Verified on

根 README 的目录表有 Verified on 列。单元格里的提供方，必须在该模板的 evidence 目录里有通过文件。空单元格表示没有通过记录。失败的运行不写入这一列，也不作为证据提交。

模板 README 的 `## Verified` 要么是句子 `No provider has a passing run recorded for this template.`，要么是第一列为提供方 id 的表。中文文件用 `尚未记录任何通过的提供方测试。`，或同一组提供方 id。`tested_on` 列出同一组 id。

## 安全

- 密钥的值不进入镜像、`template.yaml`、Docker 历史或证据 JSON。
- `env` 只声明名字和空字符串。创建沙箱时注入值。
- 日志和异常文本不包含令牌。`scripts/express_e2e.py` 在打印前会涂掉名字里含 `KEY`、`SECRET`、`TOKEN` 或 `PASSWORD` 的环境变量值。
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
| Command reference | 命令参考 |
| Configuration | 配置 |
| Resources | 资源 |
| Verified | 已验证 |
| Secondary development | 二次开发 |
| Contributing | 贡献 |
| Issues | 问题反馈 |
| License | 许可证 |

CLI 一节要有 `abx run` 示例。SDK 一节要导入 `Sandbox` 并调用 `.run` 或 `.run_sync`。命令参考是带参数的表。非阿里云基础镜像再加 `## Base image` / `## 基础镜像`。

## 上架与验收

`scripts/check_template.py <dir>` 退出码为 0、L0 通过、并且 `docs/design/<name>.md` 已填好时，目录可以以 `experimental` 合并。`awesome-templates.yaml` 增加一条：`name`、`description`、`repo`、`path`、`tags`、`author`、`capabilities`、`status`。

`status: official` 还要同时满足：

1. CI 里 L0 为绿（`python3 scripts/run_local_e2e.py`）。
2. PR 上记录了 L1（镜像构建，能看到钉死的版本）。
3. 不需要缺失密钥的 smoke 命令有 `alicloud-express` 的 L2 证据。
4. README 声称上游 Agent 本身可用之前，要有 L3 证据。SKIP 不是这句声明。

在这些通过记录出现之前，状态是 `experimental`。`community` 给仓库外维护、但仍然满足同一套文件规则的模板。索引条目上的 `providers` 映射不是验收记录。Verified 列才是。

`abx template install` 在 `alicloud-express` 上构建。其他提供方只在有 L4 运行之后才写入文档。

## 贡献

1. 模板已经分析过时，先读 `docs/template-backlog.json` 和 `docs/template-market-survey-2026-10.md` 里对应的一节。
2. 按 `docs/design/_TEMPLATE.md` 写 `docs/design/<name>.md`。
3. 把 `_skeleton/` 复制为 `<name>/`。保留阿里云基础镜像、钉死的服务安装和 README 标题。
4. 注册真正调用上游程序的命令。钉住版本。
5. 上面的验收清单还没满足时，索引入口的 `status` 写 `experimental`。
6. 运行 `python3 scripts/check_template.py <name>` 和 `python3 scripts/run_local_e2e.py`。
7. 有极速版凭证时运行 `python3 scripts/express_e2e.py <name>`。只有进程退出码为 0 才提交证据文件。
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
python3 scripts/check_template.py --all --strict   # 旧模板的违规也导致失败
```

`--all` 打印符合性列表。每个 `spec_version: 2` 的目录都通过时退出码为 0。旧目录会带上违规代码列出来，但不让进程失败。CI 运行 `--all`。`scripts/run_local_e2e.py` 也会运行它，spec_version 2 失败时整个脚本失败。

违规代码包括 `required-file`、`readme-section`、`base-image`、`dockerfile-cmd`、`dockerfile-user`、`yaml-field`、`commands-start`、`verified-evidence`、`pinned-version`、`readme-client`、`secrets`。`RUN` 上两种服务端钉都没有时，`pinned-version` 失败。spec_version 2 的 SDK 章节没有写 `agent-sandbox-client`，或 README 让读者 `pip install agent-sandbox` 时，`readme-client` 失败。

## 极速版 harness

```bash
export HOME=/home/ubuntu
unset ABX_PROVIDER
export ABX='node /path/to/agent-sandbox/dist/bin/abx.js'
export ACR_NAMESPACE=...
export ALICLOUD_ACCESS_KEY_ID=...
export ALICLOUD_ACCESS_KEY_SECRET=...
export ABX_SANDBOX_API_KEY=...
export ABX_SANDBOX_BASE_URL=...
export ABX_SANDBOX_DOMAIN=...
export ALIBABA_CLOUD_REGION_ID=cn-hangzhou
# 可选：用一份检出构建镜像里的 server
export ABX_SERVER_SDK_SOURCE=/path/to/python-sdk/server-sdk

python3 scripts/express_e2e.py python-hello \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000' \
  --command hello --arg name=E2E --expect 'Hello, E2E!'
```

main 上的 `python-hello` 还没有 `smoke`、`start_cmd` 和阿里云基础镜像，所以上面的标志补上这些值。`spec_version: 2` 的目录不需要标志：harness 读 `template.yaml`。

远端名字是唯一的 `e2e-<name>-<hex>` 别名，不是目录里的名字，因此已有的 generation 1 模板会被留下。`finally` 对本进程创建的 id 执行 `abx kill <id> -y` 和 `abx template delete <id> -y`。它还会杀掉部署进程组，以及命令行里包含该别名的 `docker push`。以前只按墙钟杀掉 `abx` 时，推送不在同一个进程组里，会继续占着仓库连接。

harness 用现有标志调用 `abx template deploy`（`--json`、`-y`、`--generation`、`--start-cmd`、`--ready-cmd`、`--alias`、`--acr-repo`、`--tag`、`--timeout`、`--verbose`）。它自己不推镜像。`--timeout` 是 `abx` 内部等待 READY 的预算，不是上传的上限。`--verbose` 让 `--json` 下也能看到每一层的输出；没有这些行时 CLI 只打印阶段名，慢推送看起来像停住了。harness 会从子进程环境里去掉 `CI` 以及 `abx` 用来识别 CI 的其他变量（`GITHUB_ACTIONS`、`GITLAB_CI` 等），因为 CI 模式会吞掉这些行。

并发的 harness 在整个 deploy 期间对 `/tmp/abx-acr-push.lock` 加独占 `flock`（`ABX_ACR_PUSH_LOCK` 可改路径）。CLI 没有单独的推送步骤，所以这把锁盖住构建、推送和 READY 轮询，比只锁 `docker push` 更粗。推送锁和无进展超时应该做在 `abx` 里（[agent-sandbox#29](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues/29)）。在那之前，由 harness 上锁。

`--idle-timeout`（默认 180）在 stdout 和 stderr 没有新字节时杀掉这次 deploy。仍在打印层状态的推送算作有进展，不会被杀掉。`--wall-timeout`（默认 `max(21600, --timeout)`）只是安全上限，给一直有输出的 deploy 用。六小时够一条仍在前进的大约 1 GB 上传，按争用链路上测到的约 35 KB/s 估算；真正停掉已经不动的推送的是空闲计时器。`--push-retries`（默认 2）会重试卡住的推送或推送错误。已知的 CLI/SDK 阻断和 Docker 构建失败不重试。每次重试前先停掉这个别名留下的 `docker push`，避免新上传叠在孤儿进程上。

`--plan` 打印解析后的命令、锁路径和超时，不调用 `abx`。

退出码 2 表示输出命中了已知的 CLI 或 SDK 失败（字符串 `base` 被拒绝、generation 1 更新、`AuthError` / HTTP 401，或 envd 的 `promised N bytes in enveloped message`）。这些曾记在 agent-sandbox `#12` `#13` `#14` 和 python-sdk `#15` `#17`。部署与运行的 CLI 修复已在 `agent-sandbox` main（`#16`）。envd 帧和端口 9000 认证的修复已在 `python-sdk` main。harness 仍然识别旧的报错，这样旧二进制也会给出明确结果。

退出码 1 是其他失败。退出码 0 会写入证据文件。
