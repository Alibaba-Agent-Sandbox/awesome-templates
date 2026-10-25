# dev-services

[English](README.md)。固定 PostgreSQL17.11 与 Redis8.0.2，非 root、无 Docker/systemd 的开发数据库。

## 做什么

初始化私有工作区数据库目录，启动两个真实服务，执行 SQL 和受限 Redis 操作，查看状态并停止本次进程。默认仅监听127.0.0.1:5432/16379，命令接口9000，必须提供密码。拒绝无所有权标记的已有目录。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

阿里云基础镜像 fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>，默认v0.0.49；Debian PostgreSQL服务端/客户端/libpq5 固定17.11-0+deb13u1，Redis服务端/工具固定5:8.0.2-3+deb13u3。传递系统安全库由当前 Debian 源解析。generation2、USER user、/home/user/app，标准启动及健康命令，无 CMD/ENTRYPOINT。构建时关闭默认集群及自动启动。

## 解决的问题

在无特权、无 Docker Compose、不能 mount/systemd 的沙箱内提供真实单机数据库，明确鉴权、持久化数据及资源所有权。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./dev-services --yes
abx run <sandbox-id> services_versions --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('services_versions'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/services_versions`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": {"postgres": "17.11", "redis": "8.0.2"}}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

## 资源

2vCPU、2048MB、约10GiB根文件系统，端口9000/5432/16379。无Docker/KVM/root/显示器；依赖Linux pidfd/procfs。停止先TERM后有界KILL，强制退出后PostgreSQL可能恢复；Redis appendonly/everysec是开发持久化，不承诺零丢失。需要长期保存时在删除沙箱前备份数据。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 二次开发

新增命令保持参数/输出/执行边界与鉴权。参考[PostgreSQL initdb](https://www.postgresql.org/docs/17/app-initdb.html)、[Redis安全](https://redis.io/docs/latest/operate/oss_and_stack/management/security/)及upstream-pins.json官方包来源。复制原始数据前停止两个引擎。调用方SQL和应用源码的隔离由沙箱提供，包装不构成额外安全边界。

## 贡献

阅读[贡献指南](../CONTRIBUTING.md)、[规范](../docs/template-spec.zh-CN.md)、[设计](../docs/design/dev-services.md)。完成本机/HTTP、真实镜像、极速版和独立清理验收后再标记对应提供方通过；保留失败记录。

## 问题反馈

[模板Issue56](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/56)、[Python SDK/服务端](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。SDK/CLI标题前缀为[templates]。

## 许可证

包装源码Apache-2.0，见[LICENSE](../LICENSE)。PostgreSQL为PostgreSQL License，Redis8可选择AGPLv3许可，不能描述成旧版Redis的BSD协议。保留安装的Debian版权及源码引用；分发或修改时遵循上游及传递依赖条款。

### 当前版本新增平台 step 验收

[真实原生 step](evidence/express-2026-10-20T130648Z.json)：官方 READY、Python SDK 创建、当前 CLI/SDK 冒烟，以及独立确认所拥有沙箱/模板已清理。[完整外部 HTTP](evidence/full-http-steps-2026-10-20T130648Z.json)：6 通过、0 失败、0 跳过。
