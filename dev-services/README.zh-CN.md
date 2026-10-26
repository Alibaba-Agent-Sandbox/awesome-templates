# dev-services

[English](README.md)

## 做什么

初始化私有工作区数据库目录，启动两个真实服务，执行 SQL 和受限 Redis 操作，查看状态并停止本次进程。默认仅监听127.0.0.1:5432/16379，命令接口9000，必须提供密码。拒绝无所有权标记的已有目录。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

阿里云基础镜像 fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>，默认v0.0.49；Debian PostgreSQL服务端/客户端/libpq5 固定17.11-0+deb13u1，Redis服务端/工具固定5:8.0.2-3+deb13u3。传递系统安全库由当前 Debian 源解析。generation2、USER user、/home/user/app，标准启动及健康命令，无 CMD/ENTRYPOINT。构建时关闭默认集群及自动启动。

## 解决的问题

在无特权、无 Docker Compose、不能 mount/systemd 的沙箱内提供真实单机数据库，明确鉴权、持久化数据及资源所有权。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

将口令占位符换成16–128 个 URL-safe ASCII 字符的独立口令。该口令不替代 `ABX_SERVER_TOKEN`。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export DEV_SERVICES_PASSWORD='<choose-a-long-unique-password>'
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//dev-services --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" services_start --json-args '{}'
abx run "$SANDBOX_ID" services_sql --json-args '{"sql":"CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;"}'
```

返回 PostgreSQL 查询输出，合计 `5130` 分；会在此沙箱数据库中创建表。

数据库默认只监听沙箱回环地址；通过 `services_sql` / `services_redis` 操作，不需要在本机登录数据库。外部客户端必须显式 `expose=true`、配置正确端口转发并使用独立数据库口令；不要暴露无认证端口。数据库文件位于工作区 `service-data/`。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

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
            await client.commands.run('services_start')
            result = await client.commands.run('services_sql', sql='CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;')
            print(result)
        finally:
            try:
                await client.commands.run('services_stop')
            finally:
                await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

先按顺序调用：

- `POST /commands/services_start` with `{}`.

`POST /commands/services_sql`

```json
{
  "sql": "CREATE TABLE usage_demo (amount integer); INSERT INTO usage_demo VALUES (5130); SELECT sum(amount) AS total_cents FROM usage_demo;"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

使用完成后调用：

- `POST /commands/services_stop` with `{}`.

## 命令参考

| 命令 | 参数 | 返回 |
|---|---|---|
| services_setup_check | none / 无 | installed flag, declared pins and password-configured boolean; no credentials |
| services_versions | 无 | 实际 {postgres,redis} 版本 |
| services_start | password:16..128 URL-safe ASCII 字符，默认 DEV_SERVICES_PASSWORD；data_dir:单层目录名，默认 service-data；expose:布尔，默认false；timeout_s:1..120，默认60，分别用于初始化/就绪阶段 | {postgres:5432,redis:16379,running:true,exposed:布尔} |
| services_status | 无 | {running:false} 或 {running:布尔,postgres:5432,redis:16379} |
| services_sql | sql:必填，1..16384 UTF8字节 | psql 非对齐行文本 |
| services_redis | action:PING/SET/GET/DEL/INCR，默认PING；key:非PING必填，1..1024字节；value:SET文本，最多64KiB | Redis原始字符串，GET不存在返回空串 |
| services_stop | 无 | 确认本次进程/监听消失后的 {running:false} |
| services_self_test | 无；已有本次服务运行时拒绝 | 真实读写、停止重启及数据清理后的 POSTGRES_REDIS_OK |

psql使用 -X、ON_ERROR_STOP；redis-cli使用 -e 将协议错误作为失败。参数不经 shell，密码仅在客户端进程环境中。单次客户端30秒、每输出流256KiB限制。PostgreSQL使用SCRAM-SHA-256，Redis强制requirepass；临时配置0600、目录0700。Redis内存128MiB/noeviction，PostgreSQL64MiB共享缓冲/20连接。默认数据库用户sandbox、数据库postgres；重启原数据目录须提供相同PostgreSQL密码。停止保留数据，删除沙箱不会保留临时磁盘。

版本1.1.0为 services_start 新增 postgres_port:int=0、redis_port:int=0；0表示读取服务启动环境 DEV_SERVICES_POSTGRES_PORT/DEV_SERVICES_REDIS_PORT，本镜像默认5432/16379。不带这些设置单独加载源码时保留5432/6379。显式端口必须为1024..65535的不同整数，排除命令端口9000；启动和状态均返回实际端口。原1.0.0真实极速版尝试中，自有启动前6379已占用（独立探测EADDRINUSE98），不会停止无关监听。1.0.0数据标记代表未改变的存储格式，1.1.0仍可读取。认证和进程所有权要求保持原样。[端口诊断](evidence/port-conflict-2026-10-20.json)。

## 配置

| 名称 | 默认值 | 用途 |
|---|---|---|
| ABX_SERVER_TOKEN | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| ABX_SERVER_PORT | 9000 | 本地命令端口 |
| WORKSPACE | /home/user/app | 已存在工作区 |
| DEV_SERVICES_PASSWORD | 空 | 可选默认密码，也可每次启动显式传入 |
| DEV_SERVICES_POSTGRES_BIN | /usr/lib/postgresql/17/bin | 可信固定二进制 |
| DEV_SERVICES_REDIS_BIN | /usr/bin | 可信固定二进制 |
| DEV_SERVICES_LIBRARY_PATH | 空 | 解包安装本机测试用可信动态库路径 |

预热服务使用[显式进程配置](../docs/runtime-environment.md)。子进程环境仅有PATH、私有HOME、语言及所有权标记，不继承云端/模型密钥。expose=True才主动监听0.0.0.0并增加PostgreSQL SCRAM主机规则，鉴权仍强制。平台外部TCP端口转发尚未认证，不可自行拼接访问URL。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
abx run "$SANDBOX_ID" services_stop --json-args '{}'
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

2vCPU、2048MB、约10GiB根文件系统，端口9000/5432/16379。无Docker/KVM/root/显示器；依赖Linux pidfd/procfs。停止先TERM后有界KILL，强制退出后PostgreSQL可能恢复；Redis appendonly/everysec是开发持久化，不承诺零丢失。需要长期保存时在删除沙箱前备份数据。

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/dev-services.md)。

## 问题反馈

[模板Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56)、[Python SDK/服务端](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI标题前缀为[templates]。

## 许可证

包装源码Apache-2.0，见[LICENSE](../LICENSE)。PostgreSQL为PostgreSQL License，Redis8可选择AGPLv3许可，不能描述成旧版Redis的BSD协议。保留安装的Debian版权及源码引用；分发或修改时遵循上游及传递依赖条款。
