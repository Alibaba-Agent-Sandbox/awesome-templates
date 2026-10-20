# dev-services

[English](README.md)。固定 PostgreSQL17.11 与 Redis8.0.2，非 root、无 Docker/systemd 的开发数据库。

## 做什么

初始化私有工作区数据库目录，启动两个真实服务，执行 SQL 和受限 Redis 操作，查看状态并停止本次进程。默认仅监听127.0.0.1:5432/16379，命令接口9000，必须提供密码。拒绝无所有权标记的已有目录。

## 技术栈

阿里云基础镜像 fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>，默认v0.0.49；Debian PostgreSQL服务端/客户端/libpq5 固定17.11-0+deb13u1，Redis服务端/工具固定5:8.0.2-3+deb13u3。传递系统安全库由当前 Debian 源解析。无注入 wheel 时服务端固定 e2cb27e24fde0a67112f82b8d44af463445a5d1a。generation2、USER user、/home/user/app，标准启动及健康命令，无 CMD/ENTRYPOINT。构建时关闭默认集群及自动启动。

## 解决的问题

在无特权、无 Docker Compose、不能 mount/systemd 的沙箱内提供真实单机数据库，明确鉴权、持久化数据及资源所有权。

## 快速开始（CLI）

按[原生 CLI 配置](../docs/platform-steps.zh-CN.md)准备环境。自测生成临时密码并清理全部数据；长期应用使用下面 SDK 示例，避免密码进入 shell 参数。

```bash
abx template deploy ./dev-services -y --generation 2 \
  --start-cmd 'agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py' \
  --ready-cmd 'agent-sandbox-server healthcheck --port 9000'
abx create --template <template-id> -y
abx run <sandbox-id> services_self_test
abx run <sandbox-id> services_status
abx run <sandbox-id> services_stop
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

客户端发行包 agent-sandbox-client，导入 agent_sandbox；安装[配对 SDK](../docs/python-client-installation.md)。停止后保存所需数据，再删除沙箱。

```python
import asyncio
import secrets
from agent_sandbox.api.sandbox import Sandbox

async def main():
    password = secrets.token_urlsafe(24)
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("services_start", password=password))
        print(await sb.run("services_sql", sql="SELECT 19+23"))
        await sb.run("services_redis", action="SET", key="example", value="42")
        print(await sb.run("services_redis", action="GET", key="example"))
        await sb.run("services_stop")
        # Save needed data after stop, before destroying the sandbox.
    finally:
        await sb.kill()

asyncio.run(main())
```

## 快速开始（HTTP POST）

将 ABX_SERVER_URL 设置为 SDK network.get_url(9000)。命令接口鉴权在进程启动前配置 ABX_SERVER_TOKEN。

```bash
curl --fail-with-body --request POST "$ABX_SERVER_URL/commands/services_self_test" \
  --header 'Content-Type: application/json' \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --data '{}'
```

成功响应 {"result":"POSTGRES_REDIS_OK"}。缺失参数400、未知命令404、执行错误500。客户端超时不保证服务端取消。

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
| ABX_SERVER_TOKEN | 空 | 启动前配置的命令接口鉴权 |
| ABX_SERVER_PORT | 9000 | 本地命令端口 |
| WORKSPACE | /home/user/app | 已存在工作区 |
| DEV_SERVICES_PASSWORD | 空 | 可选默认密码，也可每次启动显式传入 |
| DEV_SERVICES_POSTGRES_BIN | /usr/lib/postgresql/17/bin | 可信固定二进制 |
| DEV_SERVICES_REDIS_BIN | /usr/bin | 可信固定二进制 |
| DEV_SERVICES_LIBRARY_PATH | 空 | 解包安装本机测试用可信动态库路径 |

预热服务使用[显式进程配置](../docs/runtime-environment.md)。子进程环境仅有PATH、私有HOME、语言及所有权标记，不继承云端/模型密钥。expose=True才主动监听0.0.0.0并增加PostgreSQL SCRAM主机规则，鉴权仍强制。平台外部TCP端口转发尚未认证，不可自行拼接访问URL。

## 资源

2vCPU、2048MB、约10GiB根文件系统，端口9000/5432/16379。无Docker/KVM/root/显示器；依赖Linux pidfd/procfs。停止先TERM后有界KILL，强制退出后PostgreSQL可能恢复；Redis appendonly/everysec是开发持久化，不承诺零丢失。需要长期保存时在删除沙箱前备份数据。

## 已验证

尚无本模板云端通过回执。本机实际非root PostgreSQL17.11/Redis8.0.2鉴权、SQL/Redis读写、停止重启持久化、进程和监听清理、无关监听保留测试通过。镜像/极速版门禁待执行，外部TCP转发未验证。

## 二次开发

新增命令保持参数/输出/执行边界与鉴权。参考[PostgreSQL initdb](https://www.postgresql.org/docs/17/app-initdb.html)、[Redis安全](https://redis.io/docs/latest/operate/oss_and_stack/management/security/)及upstream-pins.json官方包来源。复制原始数据前停止两个引擎。调用方SQL和应用源码的隔离由沙箱提供，包装不构成额外安全边界。

## 贡献

阅读[贡献指南](../CONTRIBUTING.md)、[规范](../docs/template-spec.zh-CN.md)、[设计](../docs/design/dev-services.md)。完成本机/HTTP、真实镜像、极速版和独立清理验收后再标记对应提供方通过；保留失败记录。

## 问题反馈

[模板Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56)、[Python SDK/服务端](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI标题前缀为[templates]。

## 许可证

包装源码Apache-2.0，见[LICENSE](../LICENSE)。PostgreSQL为PostgreSQL License，Redis8可选择AGPLv3许可，不能描述成旧版Redis的BSD协议。保留安装的Debian版权及源码引用；分发或修改时遵循上游及传递依赖条款。
