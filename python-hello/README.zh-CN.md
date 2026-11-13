# python-hello

[English](README.md)

本分支模板使用 YAML v1，需要匹配的开发构建；已发布 CLI 0.5.10 不支持此格式。模板属性在 `sandbox.agent.template`；运行默认值在 Dockerfile，私有运行值在创建实例时显式传入。用途和凭据来源见本页配置部分。详情见[配置规范](../docs/template-spec.zh-CN.md)。

## 做什么

提供最小 Python 开发沙箱：问候、执行内联 Python、运行上传的脚本和 pytest 测试，同时演示隐藏命令和自定义 GET 路由。`agent-sandbox-server` 在 9000 端口提供命名命令。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>` 自带 Python 3.13、Node.js 20。部署时默认解析为 `cn-hangzhou` 和 `v0.0.49`。
- 镜像安装 `pytest==8.4.2`，供 `test` 命令使用。
- 非 root 用户 `user`，工作目录 `/home/user/app`，generation 2。`abx deploy` 准备镜像和模板；`run.py` 在创建实例后带运行凭据启动应用。

## 解决的问题

用于学习命名命令协议，或通过同一沙箱上传、运行、测试 Python 程序。内联代码、脚本路径、pytest 路径统一使用一个工作目录，避免上传文件与执行目录不一致。

## 快速开始（CLI）

`abx deploy` 只准备模板。下载本目录源码后，从该目录执行下面的部署，再将 `<prepared-template-id>` 改成返回的模板 ID，运行 `run.py` 创建实例并显式启动业务服务。脚本只传入本页列出的运行配置，自动生成并将应用令牌保存在本地 `.sandbox-session.json`（仅当前用户可读）；不会打印令牌。已有会话文件不会被覆盖，可用 `--session` 选择新文件。


CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
# run.py 自动生成私有应用令牌；需要自行指定时可取消下一行注释。
# export ABX_SERVER_TOKEN='<YOUR_APPLICATION_TOKEN>'
export ABX_HTTP_TIMEOUT=450
abx deploy . --yes
python3 -m pip install "agent-sandbox-client==0.4.0a7"
python3 run.py --template <prepared-template-id> --timeout 1800
export ABX_SERVER_TOKEN="$(python3 -c 'import json; print(json.load(open(".sandbox-session.json"))["application_token"])')"
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx sandbox command run "$SANDBOX_ID" run_script --json-args '{"code":"from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath(\"summary.txt\").write_text(f\"total={total:.2f}\\n\")\nprint(f\"total={total:.2f}\")"}'
```

返回 stdout `total=51.30`，并生成可下载的 `summary.txt`。

`run.py --timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a7`。

在完成上述 CLI 启动、设置 `SANDBOX_ID` 后，将以下保存为 `use_template.py`，执行 `python3 use_template.py`。它连接同一实例，不另建沙箱。对于需要输入的示例，先在本机准备上面的文件。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('run_script', code='from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath("summary.txt").write_text(f"total={total:.2f}\\n")\nprint(f"total={total:.2f}")')
            print(result)
            Path('summary.txt').write_bytes(await sb.files.read_bytes('/home/user/app/summary.txt'))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/run_script`

```json
{
  "code": "from pathlib import Path\nrows = [12.50, 18.80, 20.00]\ntotal = sum(rows)\nPath(\"summary.txt\").write_text(f\"total={total:.2f}\\n\")\nprint(f\"total={total:.2f}\")"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

下列参数均为字符串，模板没有额外长度限制。路径可相对于工作目录，也可为绝对路径，需运行用户 `user` 可访问；代码以该用户权限执行。这些命令用于执行调用者提供的 Python，应只向可信调用者开放。

| 命令 | 参数 | 必填/默认值 | 返回值 | 执行期限 |
|---|---|---|---|---|
| `hello` | `name: str` | 可选，`World` | `Hello, <name>!` | 不启动子进程 |
| `run_script` | `code: str` | 必填 | Python stdout | 30 秒 |
| `run` | `file: str` | 可选，`main.py` | 脚本 stdout | 60 秒 |
| `test` | `path: str` | 可选，`.` | pytest stdout | 120 秒 |
| `_debug_info` | 无 | 发现列表隐藏，但可调用 | 含 `python`、`system` 的对象 | 不启动子进程 |

`run_script` 使用服务器自身的 Python 加 `-c`；`run` 将文件作为 argv 参数；`test` 执行 `python -m pytest -p no:cacheprovider <path>`。不进行 shell 插值。非零退出（包括 pytest 没有找到测试）、进程启动失败和执行超时返回 HTTP 500，使用固定诊断，退出码存在时会附上。失败消息不包含 argv、源码或捕获的输出；成功 stdout 按设计返回，可能包含程序打印的数据。镜像不自带示例测试，需自行上传。空字符串可通过字符串类型检查，后续可能导致子进程错误。

## 配置

资源配置改 `template.yaml` 的 `sandbox.agent.template`；镜像默认值改 Dockerfile。运行时值从当前进程环境传给 `run.py`，允许的名称直接列在脚本 `RUNTIME_ENV_NAMES` 中。空值不会作为秘密写入镜像。业务启动命令在 `run.py`；不在模板快照阶段启动带动态认证的服务。外部 SDK/HTTP 客户端可从私有 `.sandbox-session.json` 读取 `application_token`，或复用显式设置的 `ABX_SERVER_TOKEN`。

| 变量 | 必填 | 默认值 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 自动生成 | run.py 自动生成，或显式提供；外部客户端从私有会话文件读取。 |
| `WORKSPACE` | 否 | `commands.py` 所在目录 | 所有 Python 子进程使用的已有目录，调整时同步修改上传路径。 |
| `ABX_SERVER_BASE_DIR` | 否 | `/home/user` | 文件 API 路径边界；自定义工作目录需位于该边界内。此设置不限制任意 Python 代码。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地 `python3 commands.py` 监听端口；云端 `start_cmd` 固定指定 9000。 |
| `LANG` | 否 | `C.UTF-8` | Unicode 输出。 |

在 `run.py` 前安全导出本页说明的运行配置；脚本仅传递声明的变量。不要将秘密写入镜像、YAML 或日志。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx sandbox download "$SANDBOX_ID" /home/user/app/summary.txt ./summary.txt
abx sandbox delete "$SANDBOX_ID" --yes
```

`abx delete` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

### 选择备用镜像配方

保留了 `Dockerfile.portable`。需要时在资源副本中修改 `template.buildConfig.dockerfile`，并选择目标 Provider 及其支持的模板属性。准备完成后，通过 `run.py --provider <provider> --template <reference>` 创建实例并启动应用。配方存在不等于该后端已经验证。

## 资源

2 vCPU、2048 MB 内存、9000 端口，使用 provider 根文件系统（Express 约 10G）。无需 GPU、Docker、KVM 或模型 API key。大任务可能超出内存或执行期限，应选择合适的进程 API/provider。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/python-hello.md)。

## 问题反馈

模板跟踪：[awesome-templates#21](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/21)。模板问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，Python 客户端/服务端问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI 标题使用 `[templates]`，提供无秘密的复现、provider、generation 和源码版本。

## 许可证

Apache-2.0，见 [LICENSE](../LICENSE)。
