# agents-api

业务客户端只配置一个 Gateway endpoint 和业务 Key。Agent 的模型调用、工具和工作区
运行在 Session 独占的 Sandbox 中。

[English](README.md) · [API 参考](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.zh-CN.md)

本分支模板使用 YAML v1，需要匹配的开发构建；已发布 CLI 0.5.10 不支持此格式。Sandbox 实例环境配置位于 `sandbox.instance.envs`，模型访问位于 `application.bindings.model`；用途和凭据来源见本页配置部分。详情见[配置规范](../docs/template-spec.zh-CN.md)。

## 做什么

通过同一个 Gateway 创建逻辑 Session、上传输入、运行 Codex 或 Qwen Code、查询持久化
Submission 和事件、下载产物。首次输入按需创建 Sandbox；后续轮次继续使用原生线程和
工作区。Close 释放计算并保留结果，Delete 删除公开数据，内部继续处理必要的资源清理。

这是参考 OpenAI Agents 的子集及明确的托管扩展。受支持字段见
`/v1/agent-sandbox/capabilities`，不承诺 OpenAI 托管 harness 或任意 OpenAI SDK 兼容。
忙碌时不能引导当前轮次的输入会被拒绝；需要排队时使用显式 Submission 队列。

## 技术栈

阿里云第二代 Sandbox 基础镜像、非 root 用户、Node.js 24.16.0、Codex 0.162.1、
Qwen Code 0.23.0、PostgreSQL，以及 FC Gateway/Worker/Dispatcher 函数。

[template.yaml](template.yaml) · [Sandbox Dockerfile](Dockerfile) ·
[Server Dockerfile](server/Dockerfile)

部署应用需要 Node.js 20 或更高版本和匹配的开发版 CLI。业务 HTTP 客户端只需要 Gateway endpoint 和业务 Key。

Guest 保留已发布 Server0.4.0a7；Server 使用固定 SDK 开发源码提交 `b988d2a76057b6202d836ec329cc0bd90a572b26`，详见 [Server Dockerfile](server/Dockerfile)。源码包元信息仍为 a7，不代表新的 PyPI 发行。

## 解决的问题

调用方只连接应用 endpoint，无需逐个发现 Sandbox 地址。部署凭据、数据库连接和
Sandbox 管理凭据留在 Server；Sandbox 只接收选定的模型配置和单独生成的应用令牌。

## 快速开始（CLI）

这些命令需要当前源码 CLI，已发布的 0.5.10 不支持。先按[使用指南](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/using-templates.md#installation)
配置 Sandbox 及镜像构建仓库。`deployment.access` 可选已有 Devs 别名、复用 abx 云凭据的 `abx`，或读取进程云凭据的 `env`，缺省仍为 `default`。FC 地域、Sandbox 地域、数据库网络和镜像仓库访问需要相互匹配。
CLI 只复制这个模板，得到可编辑项目，不会在获取源码时部署。部署主机仍需 Python 3
和 `httpx==0.28.1`：部署后会执行 `scripts/smoke.py`，通过 Gateway 完成两轮 Agent
文件任务。部署及更新时保持该虚拟环境激活。创建虚拟环境会同时创建 `.abx/`，无需单独建目录。

```bash
abx template init ./agents-api --from agents-api
cd agents-api
python3 -m venv .abx/venv
. .abx/venv/bin/activate
python -m pip install httpx==0.28.1
```

部署前提供“配置”表中的环境变量，在私有 binding 文件中选择 adapter，
通过 `OPENAI_MODEL` 提供与其匹配且实际可用的模型 ID，并修改清单中的地域、access 和资源限制。私有文件、构建收据和计划存放在 `.abx/` 下，该目录不进入镜像构建上下文。

```bash
abx deploy . --name agents-api --plan
abx deploy . --name agents-api --yes
abx status agents-api
```

`--plan` 只预览资源，不构建或部署；`--yes` 确认执行构建、云端部署和模板自带的真实模型业务检查。

`abx status agents-api` 显示 endpoint 和本机私有凭据文件路径。首次部署自动生成独立的业务及内部 Key，后续更新复用。业务客户端只需要 endpoint 和该文件中的 `businessKey`，不要分享 `internalToken`。显式提供的自定义凭据不会复制保存。

```bash
abx logs agents-api
abx recover agents-api
```

`abx logs` 需要配置 FC `logConfig`；本模板默认不配置。未配置时，请在 FC 控制台查看可用的函数诊断信息。

部署中断后先执行 `recover` 查看已知资源和恢复提示，不重复提交创建请求。修改模板或配置后，使用相同名称再次执行 `abx deploy . --name agents-api --yes` 更新。已有 Session 保留原 revision；先关闭其 Session，再清理未使用的旧版本：

```bash
abx status agents-api --revisions
abx delete agents-api --revision <旧版本> --yes
```

作者需要分开构建和部署时，可选用 `abx template build . --out .abx/build.json --yes`，再通过 `abx deploy . --build .abx/build.json --name agents-api --yes` 复用构建。发布源码使用 `abx template publish`，不会自动上架 Registry。

## 快速开始（Python HTTP 客户端）

Gateway 使用标准 HTTP，目前没有专用的 Gateway 客户端 SDK；本例使用 `httpx`，无需
Sandbox SDK 或单个 Sandbox 地址。设置
`AGENTS_API_BASE_URL` 为返回的 endpoint，`AGENTS_CREDENTIALS_FILE` 为返回的本机私有
凭据文件路径。下面创建带初始任务的 Session，并查询其持久化 Submission。

```python
import json, os, time
from pathlib import Path
import httpx

key = json.loads(Path(os.environ["AGENTS_CREDENTIALS_FILE"]).read_text())["businessKey"]
with httpx.Client(base_url=os.environ["AGENTS_API_BASE_URL"],
                  headers={"Authorization": "Bearer " + key}, timeout=30) as api:
    models = api.get("/v1/models").raise_for_status().json()["data"]
    response = api.post("/v1/agents/sessions",
        headers={"Idempotency-Key": "my-first-session"},
        json={"agent": {"model": models[0]["id"]},
              "input": "Write and run /workspace/outputs/hello.py printing hello."})
    response.raise_for_status()
    session = response.json()["id"]
    submission = response.headers["X-Agent-Sandbox-Submission-Id"]
    try:
        deadline = time.monotonic() + 660
        while time.monotonic() < deadline:
            value = api.get(f"/v1/agent-sandbox/sessions/{session}/submissions/{submission}").raise_for_status().json()
            if value["status"] in {"completed", "failed", "cancelled", "uncertain"}:
                break
            time.sleep(1)
        else:
            raise TimeoutError("客户端超时不取消执行，请继续查询 Submission")
        print(value["status"], value.get("turn_id"))
        # 使用 /v1/agents/sessions/{session}/artifacts 下载已捕获产物。
    finally:
        closed = api.post(f"/v1/agent-sandbox/sessions/{session}/close", json={})
        closed.raise_for_status()
        print("清理操作：", closed.json()["id"])
```

继续查询 `/v1/agent-sandbox/operations/{id}`，直到 Close 成功，才可以认为计算已释放。
失败或不确定的操作需要协调处理，请保存其 ID。关闭后已保存的结果仍可读取，直到保留期
结束。完整的上传、两轮真实 Agent 处理和产物下载示例见 `scripts/smoke.py`；为其提供同一
私有凭据中的 `AGENTS_API_KEY` 和 `AGENTS_API_BASE_URL`。

镜像在 `/workspace/agents-api-demo` 提供一个有意保留聚合缺陷的 CSV 练习和原始测试。
附件目标位于 `/workspace/input/`，CSV 练习使用 `/workspace/input/sales.csv`。
完整示例先让 Agent 修复现有 `aggregate.py`，运行原始测试，生成汇总、说明和修改后的源码；
第二轮继续给同一个程序增加占比列。示例从 Gateway 下载每一轮的独立产物版本，并核对
金额和占比，不在宿主机执行 Agent 生成的代码。这个练习目录不覆盖你自己的文件。

## 快速开始（HTTP POST）

从私有文件读取业务 Key 到 `AGENTS_API_KEY`，不要打印值。`model-id` 使用
`/v1/models` 返回的实际模型 ID。

```bash
curl --fail-with-body -X POST "$AGENTS_API_BASE_URL/v1/agents/sessions" \
  -H "Authorization: Bearer $AGENTS_API_KEY" \
  -H 'Content-Type: application/json' -H 'Idempotency-Key: example-session-1' \
  -d '{"agent":{"model":"model-id"},"input":"Create /workspace/outputs/hello.txt containing hello."}'
```

创建 Session 返回 201。后续 `POST .../{session}/events` 返回 202、空响应体及
Submission 收据头。查询收据和对应 Turn 判断执行结果；HTTP 成功或流断开都不表示
Agent 已完成任务。

## 命令参考

[API 参考](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.zh-CN.md)列出公开操作。

| 入口 | 参数 | 结果 |
| --- | --- | --- |
| `POST /v1/agents/sessions` | `agent`、可选 `input`、metadata 和输入文件扩展 | 逻辑 Session；带初始输入时还返回收据头。 |
| `POST /v1/agents/sessions/{id}/events` | 受支持的输入或取消事件 | 202；收据位于响应头。 |
| `POST /v1/agent-sandbox/sessions/{id}/submissions` | 输入及必需的 `Idempotency-Key` | 显式排队的 Submission。 |
| `POST /v1/agent-sandbox/sessions/{id}/close` | 空对象 | 清理 Operation；保留已提交结果。 |
| `DELETE /v1/agents/sessions/{id}` | 已关闭或空闲 Session ID | 删除公开资源；正在执行或采集时返回 409。 |

私有 bridge 不是业务 API。`commands.py` 中的本机 `agents_version()` 无参数，只检查
安装的 CLI 并返回固定版本；私有 bridge 不开放该命名命令。

清单省略了 `fc-managed-agents` profile 的固定字段。按需修改显式声明的提供方、binding 引用、地域和预算；默认值与允许的覆盖见 [profile 参考](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agent-applications.zh-CN.md)。

## 配置

只编辑 [template.yaml](template.yaml)；`${env('NAME')}` 由原生 Serverless Devs parser 读取本地环境值。可以在当前项目未提交的 `.env` 中设置下列变量，不再需要 bindings JSON。模板中的 `registry.yaml` 仅用于上架和初始化提问。

| 变量 / 字段 | 用途与来源 |
| --- | --- |
| ABX_MANAGED_DATABASE_URL | 已有 PostgreSQL URL，来自数据库提供商；三个 FC 角色都要可达。不自动创建或删除数据库。 |
| SANDBOX_API_KEY | 已有 Sandbox 平台 Key，用于实例生命周期；来自对应平台的账号配置。 |
| SANDBOX_BASE_URL / SANDBOX_DOMAIN / SANDBOX_REGION | 同一 Sandbox 平台的 API、实例访问域名和地域。与 Key 匹配。 |
| OPENAI_API_KEY / OPENAI_BASE_URL / OPENAI_MODEL | 模型提供商的 Key、兼容 API 地址和已获授权的准确模型 ID。qwen-code 需要支持工具的 Chat Completions，codex 需要支持工具的 Responses。 |
| AGENTS_FC_ROLE_ARN | 已有 FC 执行角色的 RAM ARN，须能调用私有 Worker/Dispatcher；来自 RAM/FC 配置。 |
| application.bindings.model.adapter | 在 template.yaml 选择 qwen-code 或 codex，与上面模型兼容性对应。 |
| deployment.access / deployment.vars.region | 保留原生缺省 `default` 或选择已有 Devs 别名；也可用 `abx` 复用已配置的 abx 云凭据，或用 `env` 读取进程云凭据。FC 地域在 `deployment.vars.region`。部署凭据与模型、Sandbox Key 分开。 |
| application.bindings.clientAuth / internalAuth | 缺省由 CLI 自动生成不同的业务和内部密钥并在本机安全复用。业务客户端只使用业务密钥。 |

例如使用已有私网数据库时，在 `application.state` 中配置现有网络（真实 ID 由网络管理员提供）：

```yaml
application:
  state:
    databaseUrl: ${env('ABX_MANAGED_DATABASE_URL')}
    databaseCa: ${env('AGENTS_DATABASE_CA_PEM')}
    vpcConfig:
      vpcId: ${env('AGENTS_VPC_ID')}
      vSwitchIds: ["${env('AGENTS_VSWITCH_ID')}"]
      securityGroupId: ${env('AGENTS_SECURITY_GROUP_ID')}
```

只在数据库使用私有 CA 时添加 databaseCa；值为证书 PEM，来自数据库提供商，不是私钥。数据库 URL 保留 sslmode=verify-full，并使用证书覆盖的主机名。本版本不提供另一套 `{env: ...}` 或 `{file: ...}` 配置语法。

FC 三角色借用这些网络资源；不会创建 VPC、交换机、安全组、路由或 NAT。按实际路由验证数据库、镜像仓库、Sandbox 和模型端点可达性。生产入口使用已有 HTTPS 域名，要求独占的 `/*` 路由指向同一个 Gateway；该托管路径只更新 revision qualifier，不创建域名、DNS 或 VPC。托管部署仅支持三个角色资源，额外原生资源在部署前拒绝。具体支持范围见[资源规范](../docs/template-spec.zh-CN.md)。

`ABX_SERVER_TOKEN` 是运行时为每个 Sandbox 生成的独立应用认证令牌，无需去云控制台申请，也无需手动填写。

## 资源

Sandbox 请求 2 vCPU、4096 MB。默认 Session 空闲/最大寿命为 900/3600 秒，一个 Session
同时只执行一轮。Turn/工具预算为 600/60 秒。单文件和单产物上限各 10 MiB，owner 保留
总量为 100 MiB；完整的接收限制见清单。

FC、镜像存储、Sandbox、数据库和模型可能产生费用。FC 内置函数 URL 是测试入口，
受平台限制，不代表生产 SLA。同 UID 的 Agent 工具可以读取注入的模型 Key 并修改工作区；
捕获的 Agent 输出不是独立执行证明。重启或投递不确定会冻结任务并等待协调，不会静默
重放工具操作。

完成后关闭 Session，下载结果并删除不再需要的公开 Session/文件。删除部署：

```bash
abx delete agents-api --yes
```

检查删除结果；操作中断或结果不确定时，使用 `abx recover agents-api` 核查。
删除操作清理部署记录中的自有资源。通过 `--build` 提供的可复用构建产物、用户提供的
`application.server.image`，以及已有数据库、网络、模型服务和自定义域名仍由你管理。

独立构建不再被任何部署使用后，可用 `abx template build --clean .abx/build.json --yes`
清理归属已确认的 Server 镜像。Sandbox 构建镜像可能仍列在 `retained_build_artifacts`
中；按镜像仓库清理说明只删除属于你的未使用 tag。删除部署不会擦除另外保留的数据库历史。

## 贡献

遵循 [CONTRIBUTING.md](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/CONTRIBUTING.md) 和[模板规范](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/template-spec.zh-CN.md)，
同步维护中英文文档。

## 问题反馈

模板或规范问题提交到 [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)，
Gateway/bridge/runtime 问题到 [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，
部署命令问题到 [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。
请移除 Key、数据库 URL 和私有日志。

## 许可证

Apache-2.0，见 [LICENSE](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/LICENSE)。上游 CLI 保留各自许可证。
