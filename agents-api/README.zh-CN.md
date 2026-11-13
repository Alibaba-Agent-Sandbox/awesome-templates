# agents-api

业务客户端只配置一个 Gateway endpoint 和业务 Key。Agent 的模型调用、工具和工作区
运行在 Session 独占的 Sandbox 中。

[English](README.md) · [API 参考](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/main/docs/managed-agents-api.zh-CN.md)

本模板使用 YAML v1，需要匹配的开发版 CLI。资源和值在 `template.yaml` 中修改；`registry.yaml` 仅用于目录元信息和初始化表单。详见[配置规范](../docs/template-spec.zh-CN.md)。

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

使用匹配的源码 CLI，按[使用指南](../docs/using-templates.zh-CN.md)配置 Sandbox 和构建仓库凭据。部署主机需要 Python 3、Docker 及有 FC 管理权限的云凭据。部署和维护时保持项目虚拟环境激活。

```bash
abx template init ./agents-api --from agents-api
cd agents-api
python3 -m venv .abx/venv
. .abx/venv/bin/activate
python -m pip install -r scripts/requirements.txt
```

在私有 `.env` 或进程环境中填写“配置”中的变量，在 `template.yaml` 设置 `vars.adapter` 和 `vars.region`。每次 Server 构建给 `AGENTS_SERVER_IMAGE` 使用新的唯一 tag。需要修改应用名称时，在首次部署前同时修改 `name` 和 `vars.applicationName`。

```bash
abx deploy . --plan
abx deploy . --yes
python scripts/release.py status
```

计划不构建、不执行动作。部署准备 Sandbox 模板，构建 Server 镜像，分别创建 Worker、Dispatcher、Gateway 函数，并在切换稳定的 `prod` Gateway 别名前执行真实模型的两轮文件任务。部署不会创建一个常驻 Sandbox 实例。

首次部署生成不同的业务及内部令牌，更新时复用。本机私有 `.abx/agents-api/credentials.json` 包含 `businessKey` 和 `internalToken`，只向业务客户端提供业务 Key。endpoint 位于 `.abx/agents-api/release.json` 的 `endpoint` 字段。显式进程凭据不复制到凭据存储。`.env` 和 `.abx/` 应保密，并保留供更新、清理使用。

修改模板并选择新的 Server 镜像 tag 后，再执行同一个部署命令。已有 Session 继续使用原 Worker revision，新 Dispatcher 保留到旧 Worker 的路由。旧版本保留至应用删除。内部令牌不能直接轮换，跨版本共享应用时需另行协调迁移。需要日志投递时，在各角色原生 `props` 下配置 FC `logConfig`。

发布失败或中断可能留下候选版本，或者无法确定别名切换的结果。查看保存的阶段及 `python scripts/release.py status`，不要删除记录或重复提交发布。新 Dispatcher 在候选任务开始前接管新旧版本路由，候选任务失败后仍继续服务旧 Session。本模板不提供不确定发布的自动回滚和自动续跑；确认结果前保留旧资源。

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

三个原生 FC `props` 对象和 Sandbox 模板可分别调整。Session 和任务预算属于本模板的 `vars.policy`，由模板部署脚本校验。

## 配置

资源值在 [template.yaml](template.yaml) 修改。`${env('NAME')}` 读取项目私有 `.env` 或进程环境，进程值优先。`vars` 的键名由模板作者定义；下面是本模板选用的名称，不是规范保留字。

| 变量 / 字段 | 用途与来源 |
| --- | --- |
| `AGENTS_SERVER_IMAGE` | 你可写的 OCI 仓库地址及唯一 Server 镜像 tag，供原生 FC 构建和三个 Server 角色使用。 |
| `ABX_MANAGED_DATABASE_URL` | 已有 PostgreSQL URL，来自数据库提供商，三个角色均须可达。数据库创建、删除另行管理。 |
| `SANDBOX_API_KEY` | Sandbox 平台账号提供的 Key，供 Worker/Dispatcher 管理实例生命周期。 |
| `SANDBOX_BASE_URL` / `SANDBOX_DOMAIN` / `SANDBOX_REGION` | 同一平台的 API、实例域名和地域，与 Key 匹配。 |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | 模型提供商的 Key、HTTPS API 地址和已授权模型 ID，仅 Worker 接收模型 Key。qwen-code 需要支持工具的 Chat Completions；codex 需要支持工具的 Responses。 |
| `AGENTS_FC_ROLE_ARN` | 已有 FC 执行角色 RAM ARN，包含调用私有 Worker 的权限。 |
| `AGENTS_DATABASE_CA_PEM` | 可选数据库 CA 证书 PEM，来自数据库提供商，不是私钥。数据库 URL 保留 `sslmode=verify-full` 和匹配的主机名。 |
| `vars.adapter` / `vars.region` | 选择 qwen-code 或 codex，以及资源地域。地域仍属于各 `sandbox.<name>.template` 或 FC 原生 `props`，表达式仅复用值。 |
| `vars.policy` | Session、任务和存储的正整数预算；其中 `instance.timeout` 须与 Session 最大寿命一致。 |
| `AGENTS_BUSINESS_KEY` / `AGENTS_INTERNAL_TOKEN` | 可选的自定义业务及内部令牌，各不少于 32 字符且不同，缺省自动生成。这些不是云 API Key。 |

私网数据库已有网络的 ID 分别放在 `serving.worker.props.vpcConfig`、`serving.dispatcher.props.vpcConfig` 和 `serving.gateway.props.vpcConfig`：

```yaml
vpcConfig:
  vpcId: "${env('AGENTS_VPC_ID')}"
  vSwitchIds: ["${env('AGENTS_VSWITCH_ID')}"]
  securityGroupId: "${env('AGENTS_SECURITY_GROUP_ID')}"
```

验证这些网络中的数据库、仓库、Sandbox API 和模型端点可达。本模板不创建 VPC、路由、NAT、数据库或自定义域名。稳定入口使用 FC 测试 URL；已有自定义域名需要另行配置到 Gateway 的 `prod` 别名。

Guest Dockerfile 设置 `ABX_MANAGED_WORKSPACE=/workspace` 和 `ABX_MANAGED_STATE_DIR=/home/user/.agent-sandbox/managed-bridge`，分别控制 Session 工作区和 Sandbox 内 bridge 状态。修改时编辑镜像，并保持托管工作区合同一致。Worker 创建动态实例时注入独立令牌和模型环境，然后显式启动 managed bridge；模板快照准备阶段不提前启动这个需要认证的进程。实例期限也由 Worker 负责。`ABX_SERVER_TOKEN` 是运行时为每个 Sandbox 生成的独立应用令牌，无需手动申请云控制台 Key。

## 资源

Sandbox 请求 2 vCPU、4096 MB。默认 Session 空闲/最大寿命为 900/3600 秒，一个 Session
同时只执行一轮。Turn/工具预算为 600/60 秒。单文件和单产物上限各 10 MiB，owner 保留
总量为 100 MiB；完整的接收限制见清单。

FC、镜像存储、Sandbox、数据库和模型可能产生费用。FC 内置函数 URL 是测试入口，
受平台限制，不代表生产 SLA。同 UID 的 Agent 工具可以读取注入的模型 Key 并修改工作区；
捕获的 Agent 输出不是独立执行证明。重启或投递不确定会冻结任务并等待协调，不会静默
重放工具操作。

完成后关闭 Session，下载结果并删除不需要的公开数据。通过带排空检查的脚本删除应用：

```bash
python scripts/release.py destroy
```

脚本停止新请求接入并请求清理 Session。若仍有活跃 Session、待完成清理或不确定资源，会保留 FC 资源并报告排空未完成；处理剩余任务后再次执行。每次删除都重新核对 Dispatcher 和数据库身份；若上次部分删除已移除 Dispatcher，需要先独立确认业务清理再继续资源删除。确认排空后调用 `abx delete agents-api --yes`，删除记录中的自有资源，包括保留的函数版本。存在活跃 Session 时，不要绕过排空直接删除资源。

已有数据库、网络、执行角色、自定义域名和用户提供的镜像 tag 仍由你管理。不再使用的 tag 通过镜像仓库清理。应用删除不会擦除另外保留的数据库历史；确认资源已删除前保留私有部署记录。

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
