# Tau2 零售基准

[English](README.md).

## 做什么

运行原版 Tau2 v1.0.1 文本零售任务，由原生智能体与用户模拟器共同完成，返回原版评分及脱敏轨迹，再通过不携带模型密钥的原版评估器独立严格重放。支持范围为零售子集；其他领域、语音、知识任务及需要自然语言裁判的任务均拒绝。单个任务成绩不能代表完整基准。

## 技术栈

MIT 许可的[固定原版源码](https://github.com/sierra-research/tau2-bench/tree/fc0055dc4e0a316c3f83133267fbd6faaa770992)、Python3.13、隔离且按哈希锁定的依赖、LiteLLM1.81.11 与 Agent Sandbox server。
查看 [Dockerfile](Dockerfile)、[requirements.lock](requirements.lock)、[upstream.json](upstream.json) 和[设计](../docs/design/tau2-bench.md)。官方源码归档为92,081,935字节；固定 SHA256 记录在 `upstream.json`，来自控制端测量，并非上游发布的校验和。固定 `PYTHONPATH=/opt/tau2/src` 从源码运行，不声称 PyPI 已发布 Tau2 包。

[原始冻结导出](requirements.upstream.lock)完整保留平台标记；`python tau2-bench/select_lock.py` 选择 Linux CPython3.13 对应条目，不修改版本和哈希，镜像强制检查 Python 配置。

另由[兼容锁文件](requirements.compat.lock)明确新增 PSF-2.0 的 `audioop-lts==0.2.2`：Python3.13 已移除 `audioop`，但此版上游文本任务也会导入它；保留[许可证](AUDIOOP-LICENSE.txt)。

选取数据同时包含原版共享用户模拟器指引和零售领域数据，不使用替代指引。

## 解决的问题

为原版任务提供有界执行、原生评估、可单独下载的轨迹和独立严格重放。智能体与用户模拟器均使用明确配置的模型服务。

`tau2_run(domain)` 按需求返回 `score` 和 `log_path`，`artifact_path` 是同一份所属脱敏轨迹路径，同时提供字节数和 SHA256。

文本通信采用原生默认 `enforce_communication_protocol=False`，完成状态、源码、评分和严格重放验收要求均保留。

## 快速开始（CLI）

依照[步骤构建指南](../docs/platform-steps.zh-CN.md)安装已验证原生 CLI，并配置自己的极速版提供商。以下占位符须替换为本次唯一输出目录和自己创建的资源 ID。先发布源码提交，再准备不可变 COPY 步骤；步骤构建不能证明 Docker 镜像构建通过。

```bash
python scripts/prepare_steps.py tau2-bench --asset-transport oss --output /tmp/tau2-steps-<unique-run> --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
abx --native template deploy /tmp/tau2-steps-<unique-run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> tau2_version
# Requires the explicitly configured model server; select its port as documented below.
abx --native run <owned-sandbox-id> tau2_run --server-port 9010
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

命名命令使用 `abx run`；`--native` 选择已验证的原生 CLI 后端。版本结果应包含原版 `1.0.1`、领域 `retail`、`task_count: 114`。标准非模型部署、SDK 创建、HTTP 检查及清理命令：

```bash
ABX='abx --native' python scripts/run_steps_e2e.py tau2-bench --sandbox-create sdk --http --asset-transport oss
```

要求官方状态 READY，使用后独立确认本次沙箱、模板和私有资产对象均不存在。清理不确定时保留私有恢复日志。模型配置仅通过下述进程环境传递，密钥不得放入 CLI 参数。

## 快速开始（Python SDK）

按[固定客户端安装说明](../docs/python-client-installation.md)安装配套 `agent-sandbox-client`。模板占位符必须属于自己。示例已通过语法检查，同样的 SDK/原生操作已在记录中的所属云验收执行；代码显式启动带模型配置的9010服务。

```python
import asyncio
import os
import secrets

import httpx
from agent_sandbox.api.sandbox import Sandbox

async def example():
    settings = {name: os.environ[name] for name in ('TAU2_MODEL_API_KEY', 'TAU2_MODEL_BASE_URL', 'TAU2_MODEL')}
    token = secrets.token_urlsafe(32)
    settings.update(HOME="/home/user", WORKSPACE='/home/user/workspace',
                    ABX_SERVER_BASE_DIR='/home/user/workspace', ABX_SERVER_TOKEN=token,
                    PATH="/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/bin:/sbin")
    sb = await Sandbox.create(template="<owned-template-id>", timeout=1200)
    stream = drain = server = None
    try:
        stream = await sb.commands.start(
            "agent-sandbox-server serve --port 9010 --commands /home/user/app/commands.py",
            env=settings, timeout=1100)
        started = asyncio.Event()
        async def consume():
            async for chunk in stream:
                if chunk.pid:
                    started.set()
        drain = asyncio.create_task(consume())
        await asyncio.wait_for(started.wait(), 90)
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(60):
                try:
                    response = await client.get(sb.network.get_url(9010) + "/health",
                                                headers=sb.network.get_access_headers())
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("configured server not healthy")
        server = sb.server_at(9010, token=token)
        print(await server.commands.run('tau2_version', timeout=90))
        setup = await server.commands.run('tau2_setup_check', timeout=60)
        if not all(setup.get(k) is True for k in ("api_key_set", "base_url_set", "model_set")):
            raise RuntimeError("model configuration not present in this server")
        result = await server.commands.run("tau2_run", domain="retail", task_id="0",
                                           max_steps=40, command_timeout=900, timeout=1000)
        trajectory = await sb.files.read_bytes(result["log_path"], max_bytes=8 * 1024 * 1024)
        print(result["score"], len(trajectory))
        print(await server.commands.run("tau2_verify_artifact", path=result["log_path"],
                                        task_id="0", timeout=150))
    finally:
        try:
            if server is not None:
                await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                if drain is not None:
                    drain.cancel()
                    await asyncio.gather(drain, return_exceptions=True)
                if stream is not None:
                    await stream.cancel()

asyncio.run(example())
```

创建时设置环境变量不会重配预热服务，遵循[运行环境说明](../docs/runtime-environment.zh-CN.md)，模型运行前检查 `tau2_setup_check`。

## 快速开始（HTTP POST）

将自己服务的 URL 和 Bearer token 安全注入环境，勿公开。参数直接作为 JSON 对象发送，不包裹 `args`。

```bash
curl --fail-with-body -X POST "$SERVER_URL/commands/tau2_version" -H "Authorization: Bearer $ABX_SERVER_TOKEN" -H 'Content-Type: application/json' -d '{}'
```

返回 JSON 为 `{"result":{"native_version":"1.0.1","domain":"retail","task_count":114}}`。调用 `tau2_run` 使用
`{"domain":"retail","task_id":"0","max_steps":30,"command_timeout":600}`；重放使用
`{"path":"<returned-artifact-path>","task_id":"0"}`。参数结构、类型、缺失或未知参数错误为 HTTP400，认证失败401，未知命令404，语义或原版执行失败500。结果缓冲返回；客户端超时应长于执行期限，断开连接不会取消服务端任务。

## 命令参考

| 命令 | 参数 | 返回及副作用 |
| --- | --- | --- |
| `tau2_version` | 无 | 原版源码版本、提交、零售领域及原版任务数；不调用模型。 |
| `tau2_setup_check` | 无 | 配置是否存在的布尔值及 `native-retail-agent-and-user` 模式；不返回密钥、不调用模型。 |
| `tau2_run` | `domain: str="retail"`（仅零售）；`task_id: str="0"`（1–3位十进制数字且任务须存在）；`max_steps: int=30`（5–60，拒绝 bool）；`command_timeout: int=600` 秒（30–900，拒绝 bool） | 原生 `score`、`log_path`/`artifact_path` 同路径、终止原因、消息及工具次数、源码提交、轨迹字节数/SHA256；调用两个模型并写入独占私有结果目录。含非空自然语言断言的任务在模型调用前拒绝。 |
| `tau2_verify_artifact` | 必填 `path: str`（最多4096个 UTF-8 字节，工作区内已有常规轨迹文件，1–8MiB）；`task_id: str="0"` | 无模型密钥的原版严格重放、匹配评分和轨迹 SHA256；不修改文件；期限120秒。 |

版本命令期限60秒，输入走匿名 stdin，每条输出流限256KiB。原版进程使用串行化独占进程组、nonce 和 pidfd 清理。超时、非零退出、未完成轨迹、错误源码/任务、评分不一致或畸形输出均失败。

## 配置

| 变量 | 必填/默认 | 含义 |
| --- | --- | --- |
| `TAU2_MODEL_API_KEY` | 运行任务必填；空 | 模型密钥，最多8192字符，禁止 CR/LF/NUL。 |
| `TAU2_MODEL_BASE_URL` | 运行任务必填；空 | 显式 HTTPS 兼容接口，最多2048字符；仅本地字面地址允许 HTTP 合成测试；禁止 userinfo、query、fragment。 |
| `TAU2_MODEL` | 运行任务必填；空 | 明确模型标识，最多200个允许的标识字符。 |
| `WORKSPACE` | `/home/user/workspace` | 已有且可写的结果根目录。 |
| `ABX_SERVER_TOKEN` | 空 | 对外服务应配置认证 token。 |

配置在服务导入时捕获。双方原生模型均设置相同 `openai/` 模型和显式 `api_base`，密钥只经匿名 stdin 进入私有工作进程环境，不写入 argv 或配置文件。排除操作端云凭据、GitHub 凭据和二进制覆盖变量。所有路径清理私有 HOME、临时原生日志和子进程；成功轨迹归调用者管理，失败的部分结果删除。轨迹的键和值递归移除实际密钥和接口字符串；重放不携带模型密钥。禁用遥测及模型价格网络刷新；未知价格返回零不代表免费或准确账单。

## 资源

2 vCPU、2048MiB RAM、9000端口、非 root `user`；无需 Docker daemon、KVM、GPU 或额外权限。根文件系统约10GiB，构建拒绝超过8GiB。92MB 源归档仅保留约38MB 源码/零售数据及依赖。智能体与模拟用户都产生模型费用；步骤5–60，每次模型请求60秒超时，命令期限30–900秒。成功轨迹不超过8MiB，保留于独占 `abx_tau2_result_<nonce>` 目录；读取后只删除本次目录，并销毁、独立确认自己的外层云资源不存在。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

运行 `python -m pytest -q tau2-bench/test_runtime.py`、
`python scripts/check_template.py tau2-bench` 和 `python scripts/check_docs.py`。
外部 `e2e_test.py` 检查发现、版本、配置及非法参数。设置 `E2E_REQUIRE_CLI=1` 强制原版运行；真实模型检查须在新建云服务设置
`E2E_RUN_LLM=1 E2E_REQUIRE_LLM=1 E2E_REMOTE_SANDBOX=1`：原版零售任务0须完成且评分1.0，具有实际智能体、用户和工具消息，独立下载核对字节及 SHA，再独立执行原版严格重放、返回后新鲜确认及结果清理。生成代码和运行时代码仅在云沙箱执行。不推断完整基准准确率；源码、数据、依赖、任务变化须重新验收。

## 贡献

遵循[贡献指南](../CONTRIBUTING.zh-CN.md)、[项目规范](../docs/project-standards.zh-CN.md)和[文档规范](../docs/documentation-standards.zh-CN.md)。保留上游冻结锁与两份许可证，同步翻译、设计、清单和目录，区分真实/合成测试并记录所属资源清理。

## 问题反馈

[模板需求59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59)。
模板问题：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)；
SDK/server：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)；
CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

封装为 [Apache-2.0](../LICENSE)，原版 Tau2 源码与选取的零售数据保留 [MIT 声明](UPSTREAM-LICENSE.md)。分发时保留上游声明。
Python3.13 兼容依赖保留 [audioop-lts PSF-2.0 许可证](AUDIOOP-LICENSE.txt)。
