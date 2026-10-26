# Aider

## 做什么

真实调用官方 `aider-chat==0.86.2` CLI。默认 **ask 只读模式**；只有显式
`allow_write=true` 才允许回写指定文件。工作目录必须属于已有 git 仓库。
每轮只把白名单文件复制进临时 git 工作区，完成后检查原文件未被并行修改，
再回写选中的结果，不自动提交。它不是交互式 Aider 的全部功能替代品。

## 技术栈

默认配方使用 Alibaba FC generation-2 基础镜像，以非 root `user` 运行，服务端固定安装已发布的 `agent-sandbox-server==0.4.0a6`。

官方 `aider-chat==0.86.2` 使用 `/opt/aider` 下独立的 Python `3.12.12` 环境，服务端仍使用平台 Python。

[Dockerfile](Dockerfile) · [template.yaml](template.yaml)

## 解决的问题

在隔离沙箱中使用已经安装的工具，通过 CLI、Python 或 HTTP 提交工作，再导出文件；模型账号与云沙箱账号分别配置。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，配置选择的平台（沙箱 API Key、连接地址及构建镜像仓库），再配置下面独立的模型/应用凭据。无需 clone 仓库即可启动公共模板。

此无交互路径使用下方三个显式模型配置，不启动浏览器/OAuth 登录。endpoint 必须支持兼容 OpenAI 的 Chat Completions，并接受本适配器的 `enable_thinking=false` 设置。此路径使用整文件文本编辑，不要求模型原生工具调用。从对应服务商取得 Key 和准确模型 ID，云沙箱 API Key 是另一种凭据。下方以百炼公共兼容接入点为例，必须使用同地域有权限的 Key 和模型；换服务时三个值一起替换。

使用下方的百炼接入点时，在[百炼 API Key 页面](https://help.aliyun.com/zh/model-studio/get-api-key)选择北京地域创建 Key，并填写该账号可用模型 ID；其他地域或 Coding Plan 使用其对应的 Key/endpoint，不能混用。

所有 `<...>` 都是需要你替换的占位值，模型名必须使用服务商实际提供的 ID。密钥在你自己的终端或 secret manager 中设置，不要放入镜像、YAML 或公开日志。以下变量要在 launch **之前**设置；之后改变 host 环境不会更新运行中的应用。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AIDER_API_KEY='<your-model-or-vendor-key>'
export AIDER_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
export AIDER_MODEL='<model-id-from-your-provider>'
abx template launch Alibaba-Agent-Sandbox/awesome-templates//aider --sandbox-timeout 1800 --yes
export SANDBOX_ID='<sandbox-id-returned-by-launch>'
abx sandbox command list "$SANDBOX_ID"
```

`--sandbox-timeout 1800` 是沙箱生存时间（秒），`command_timeout`/`timeout_s` 是单次任务执行期限，`ABX_HTTP_TIMEOUT`/SDK `timeout` 是客户端等待时间，三者分别设置。

launch 已启动该实例的应用，不需要再建第二个沙箱或启动第二个服务。使用 OpenSandbox 时，先按[指南](../docs/using-templates.zh-CN.md#clisdk-与-http)配置它，将 `ABX_PROVIDER=opensandbox`，下方 Python 也读取同一个选择。

```bash
abx exec "$SANDBOX_ID" -- git -C /home/user/app init -q
```

```bash
ABX_HTTP_TIMEOUT=420 abx run "$SANDBOX_ID" aider --json-args '{"prompt":"Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.","files":"[\"generated_hello.py\",\"GENERATED_REPORT.md\"]","allow_write":true,"cwd":"/home/user/app","command_timeout":300}'
```

任务要求在 `/home/user/app` 写出 `generated_hello.py` 和 `GENERATED_REPORT.md`。示例显式开放所需的编辑/工具权限，只在自己拥有的可丢弃沙箱中使用。下面的 SDK 和 HTTP 是同一任务的替代调用方式，选择一种即可。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

```python
import asyncio
import os
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        await sb.commands.run("git -C /home/user/app init -q")
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=420
        )
        try:
            print(await client.commands.run('aider', prompt='Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.', files='["generated_hello.py","GENERATED_REPORT.md"]', allow_write=True, cwd='/home/user/app', command_timeout=300))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

所有调用入口都需要 Git 工作树；发送下面请求前，先运行上面的 `abx exec ... git ... init -q` 准备步骤。

使用[直接 HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析 endpoint，保留网关 headers、URL path/query 和独立应用 token。请求 `POST /commands/aider`，`Content-Type: application/json`，body 是下面的直接参数对象，不加 `args` 包装：

```json
{
  "prompt": "Create generated_hello.py that prints exactly Hello from the sandbox, and GENERATED_REPORT.md explaining the program. Preserve unrelated existing files.",
  "files": "[\"generated_hello.py\",\"GENERATED_REPORT.md\"]",
  "allow_write": true,
  "cwd": "/home/user/app",
  "command_timeout": 300
}
```

响应为 `{"result": ...}`：内容格式见下方命令参考；模型生成的文字每次不同。HTTP 等待时间至少设为 420 秒，命令执行期限是另一个设置；断开客户端不会保证终止远端任务。认证失败为 401，参数类型错误为 400，执行失败为错误响应；返回对象包含 `exit_code` 时还应检查它是否为 0。

### 导出产物与清理

```bash
abx exec "$SANDBOX_ID" -- python3 /home/user/app/generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/generated_hello.py ./generated_hello.py
abx download "$SANDBOX_ID" /home/user/app/GENERATED_REPORT.md ./GENERATED_REPORT.md
abx kill "$SANDBOX_ID"
```

程序预期输出 `Hello from the sandbox`。先读取产物并检查再使用；模型回答成功不代表文件一定存在。文件不会自动回写模板或你的本机，释放沙箱前必须导出。

`close()`/`aclose()` 仅关闭客户端连接，不释放沙箱。launch 日志中的已构建模板和镜像可能保留用于复用，不再需要时仅删除自己创建的那些资源。

## 命令参考

| 命令 | 参数 | 返回与真实调用 |
| --- | --- | --- |
| `aider_version` | 无 | 字符串 `aider 0.86.2`；真实执行 `aider --version` |
| `aider_setup_check` | 无 | 安装/配置/home 阻断布尔值、固定版本和工作目录；不返回 key 或 endpoint |
| `aider` | 必填 `prompt: string`，1–100000 字符；`cwd: string=""`；`files: string="[]"`，内容是最多 32 个相对路径组成的 JSON 数组；`allow_write: boolean=false`；`command_timeout: integer=600`，范围 1–1800 | 脱敏 stdout/stderr、exit_code 与 changed_files 字典 |

命令响应为缓冲结果，不是流式事件。`cwd` 必须指向已存在且符合本模板路径约束的目录；允许编辑/工具执行时，模型可按沙箱用户权限修改文件或运行程序。超时只限制相应调用，客户端断连不能作为取消机制。

## 配置

| 名称 | 默认与含义 |
| --- | --- |
| `AIDER_API_KEY` | 空；必需兼容 API 凭据 |
| `AIDER_BASE_URL` | 空；必需 HTTP(S) endpoint，不允许内嵌凭据、query、fragment |
| `AIDER_MODEL` | 空；必需 model ID，自动加 LiteLLM `openai/` 前缀 |
| `WORKSPACE` | `/home/user/app`；默认工作目录 |
| `ABX_SERVER_TOKEN` | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |

在 `template launch` 前导出 `AIDER_API_KEY`、`AIDER_BASE_URL`、`AIDER_MODEL` 和独立应用令牌。当前 launch 路径启动该实例的命名服务，无需另启 9010 服务。修改宿主机环境不会重新配置已运行的应用；更改配置后启动新实例。

兼容配置使用 `extra_body.enable_thinking=false`，模型服务必须接受这个请求参数。key 不写入 stage 文件；选中源码仍会发往模型服务。

**原生 home 限制：** 固定上游源码总是先搜索 home 默认文件，再追加
`--config` / `--env-file`，这两个参数不能承诺完全隔离。已有 home
`.aider.conf.yml`、`.env`、model settings/metadata、OAuth key 文件时启动前拒绝。
包装层不替换 `HOME`、不修改共享 profile、不导入项目配置；
`PYTHON_DOTENV_DISABLED=1` 禁用 dotenv 加载。上游自己的 cache/install 与
analytics-disabled 状态可能保留在该专用沙箱原生 `.aider`，随实例整体销毁。
不要在共享宿主 home 中执行真实调用。

## 资源

2 vCPU，2048 MB 内存，应用端口 9000，非 root `user`。工作目录 `/home/user/app`；磁盘容量和最长生存时间由所选平台配置。模型任务需要访问配置的模型服务，模型调用费用由对应服务商计费。

## 贡献

开发模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)和[设计说明](../docs/design/aider.md)。

## 问题反馈

[模板 Issue 50](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/50)。
SDK/server 问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，
CLI/deploy 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 glue 为 Apache-2.0。[Aider](https://github.com/Aider-AI/aider) 也采用 Apache-2.0；
安装依赖与 [python-build-standalone](https://github.com/astral-sh/python-build-standalone)
保留各自 notices。参见[官方安装](https://aider.chat/docs/install.html)与
[兼容 API 指南](https://aider.chat/docs/llms/openai-compat.html)。
