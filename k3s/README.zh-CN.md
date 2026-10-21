# k3s

[English](README.md)。

## 做什么

使用原版K3s v1.37.1+k3s1 API服务器和kubectl，在全新私有非root、无agent控制面中校验Kubernetes manifest。每次证明API就绪、工作节点为0、严格服务端dry-run、操作后健康及清理。不执行Pod／容器／工作节点，也不提供持久用户集群。

## 技术栈

Alibaba generation2 Linuxx86_64／Python3.13、[固定serverSDK](server-sdk.commit)、81543330字节[官方原始ELF](https://github.com/k3s-io/k3s/releases/download/v1.37.1%2Bk3s1/k3s)，官方SHA256为92b94582eb7b34a8cf532e6006842b9ed215a6783cf56a3dd6271fd35243b2c0。[元数据](upstream.json)、固定源码[356c0254](https://github.com/k3s-io/k3s/tree/356c025475bbefaa09cf0d7e48e8e2adbbde57db)、原始[Apache许可证](UPSTREAM-LICENSE.md)。构建只验证字节、不执行原版；运行时校验root持有的原二进制。[官方无agent模式](https://docs.k3s.io/advanced#running-agentless-servers-experimental)属于控制面切片，不代表工作负载执行。

## 解决的问题

部署到用户集群前，用真正Kubernetes服务器校验schema／admission行为。API不接受用户kubeconfig、集群地址或外部账号。仅语法解析不能证明服务端校验，版本查询也不能证明集群能力；有效／无效结果都需要真实私有原版API及操作后检查。

## 快速开始（CLI）

`abx run`在此使用已核实的native0.4.1入口。先配置Express并发布准确源码；以公开40位提交替换<published-commit>、唯一运行名替换<run>，ID仅使用本次自有资源。重命名生成manifest以免覆盖现有模板。

```bash
python scripts/prepare_steps.py k3s --output /tmp/k3s-steps-<run> \
  --source-commit <published-commit> --asset-transport parallel
python - <<'CONFIG'
from pathlib import Path
import yaml
p = Path("/tmp/k3s-steps-<run>/template.yaml")
v = yaml.safe_load(p.read_text())
v["name"] = "k3s-<run>"
p.write_text(yaml.safe_dump(v, sort_keys=False))
CONFIG
abx --native template deploy /tmp/k3s-steps-<run> --build steps -y
abx --native create --template <owned-template-id> -y
abx --native run <owned-sandbox-id> k3s_version
abx --native run <owned-sandbox-id> k3s_native_check
abx --native run <owned-sandbox-id> validate_manifest --json-args '{"manifest_yaml":"apiVersion: v1\nkind: Namespace\nmetadata:\n  name: abx-example\n","command_timeout":180}'
abx --native kill <owned-sandbox-id> -y
abx --native template delete <owned-template-id> -y
```

返回原版Namespace的dry-run对象，不持久化用户提交资源；模板READY不代表有Kubernetes工作节点。示例经源码／语法审查，真实提供商通过必须有当前匹配回执。正式原版验收命令：

```bash
ABX='abx --native' python scripts/run_steps_e2e.py k3s \
  --sandbox-create sdk --http --asset-transport oss
```

[固定可选缓存依赖](../scripts/requirements-steps-cache.txt)启用同账号临时私有OSS传输，校验原字节哈希／ACL并独立删除。通用300MiB原包／15000线传字节限制不变。原生steps无需本地Docker，真实Docker镜像另行验收。

## 快速开始（Python SDK）

安装[配套agent-sandbox-client](../docs/python-client-installation.md)，只需已有Express配置，不需要模型或用户集群账号。Express标准9000命令服务默认没有Bearer；沙箱访问凭证不是命令服务Bearer。只有明确配置过对应token的进程才发送它。下例做语法检查，云端结果见下方回执。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    sb = await Sandbox.create(template="<owned-template-id>", timeout=900)
    sid = sb.id
    server = sb.server_at(9000, timeout=330)
    try:
        print(await sb.run("k3s_version"))
        result = await server.commands.run("validate_manifest",
            manifest_yaml="apiVersion: v1\nkind: Namespace\nmetadata:\n  name: abx-example\n",
            command_timeout=180, timeout=300)
        assert result["valid"] and result["worker_nodes"] == 0
        assert result["post_api_ready"] and result["probe_not_persisted"]
        assert result["api_server_stopped"] and result["private_state_removed"]
        assert result["node_state_restored"]
        print(result["object"]["kind"])
    finally:
        try:
            await server.aclose()
        finally:
            try:
                await sb.kill()
            finally:
                await sb.close()
    try:
        await Sandbox.get_info_by_id(sid)
    except SandboxNotFoundError:
        pass
    else:
        raise RuntimeError("owned sandbox cleanup is not verified")

asyncio.run(main())
```

仅删除本次沙箱／模板。不确定创建响应须按唯一metadata／私有意图核对，不能把响应丢失当作取消。create-time环境不追溯配置预热服务，见[运行时环境](../docs/runtime-environment.md)。可选独立认证服务使用SDK start_server9010／PTY9011，其配置和认证与内部私有Kubernetes API不同。

## 快速开始（HTTP POST）

使用自有沙箱命令服务转发URL；只有该服务启动时配置独立token才加Authorization: Bearer $COMMAND_SERVER_TOKEN。

```bash
curl --fail-with-body -X POST "$K3S_COMMAND_SERVER_URL/commands/validate_manifest" \
  -H 'Content-Type: application/json' \
  --data '{"manifest_yaml":"apiVersion: v1\nkind: Service\nmetadata:\n  name: abx-invalid\nspec:\n  ports: invalid-type\n","command_timeout":180}'
```

真实schema拒绝只在原API健康／未持久化／清理都通过后返回HTTP200：`{"result":{"valid":false,"object":null,"validation_error":"...",...}}`。基础设施／启动／未知原生错误／期限／清理失败为500，不能伪装valid:false成功。未知／类型错误参数400，语义范围400／500，认证401，未知命令404。/health、/commands、shell／文件共享命令服务认证；HTTP断开不取消云操作，仍由自身期限控制。

## 命令参考

| 命令 | 参数／默认值 | 结果／副作用 |
| --- | --- | --- |
| k3s_version | 无 | 原二进制身份与实际版本，无集群 |
| k3s_native_check | 无 | 原版server帮助；original_native/agentless_flag_in_help/private_data/private_kubeconfig/explicit_port布尔字段 |
| k3s_setup_check | 无 | mode/installed/pinned_version/runtime_uid/worker_nodes_supported:false/pods_supported:false/persistent_cluster:false/node_state_empty |
| validate_manifest | manifest_yaml必填字符串；command_timeout整数180 | 全新原版无agent服务器、严格dry-run及清理 |

manifest_yaml非空、1..32768UTF8字节、无NUL，由原版kubectl接受YAML或JSON；command_timeout整数30..300秒，布尔拒绝。不接受任意标志、外部集群URL、kubeconfig、特权模式、文件路径或shell代码。

固定原版server --config <私有空配置> --disable-agent --data-dir <私有目录> --write-kubeconfig <私有文件> --https-listen-port <自有端口> --bind-address 0.0.0.0 --advertise-address <客体IPv4>，关闭coredns／traefik／servicelb／metrics-server／local-storage。原版kubectl apply --dry-run=server --validate=strict -f <私有输入> -o json执行校验。

返回valid布尔、object原版JSON对象或null、validation_error字符串、runtime_uid整数、worker_nodes:0，以及api_ready/post_api_ready/probe_not_persisted/api_server_stopped/private_state_removed/node_state_restored:true、native_version/native_sha256/mode。独立新Namespace探针先做原版dry-run，再在校验前后get确认NotFound；用户提交资源不持久化，私有控制面初始化状态在结束后删除。错误分类保守，网络故障不能伪装为manifest拒绝。

## 配置

固定原版的--disable-agent在--help中隐藏，已对照不可变上游源码核实，因此native_check实际返回agentless_flag_in_help:false；模式由真实validate_manifest执行证明，不靠帮助输出推断。

仅可选命令服务ABX_SERVER_TOKEN；没有模型密钥／用户kubeconfig设置。子进程只收到私有HOME/config/cache/TMP和唯一归属标记，不继承操作端cloud／model／K3S／KUBECONFIG凭证。显式空配置避免加载全局K3s配置及drop-in。证书／kubeconfig／SQLite数据／原始日志仅在私有状态中并清理，失败只返回安全诊断标记。

root构建阶段准备空的用户持有0700目录/etc/rancher/node。运行时通过目录inode锁跨服务串行，任何预存状态均保留并拒绝；结束只删除匹配本次新建、当前UID持有、普通文件、33字节格式的原生password并确认目录为空，外来文件／符号链接／变化身份保留并报错。不使用SDK user=root运行时选择器，见[SDKIssue83](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/83)。

原版服务器与内层kubectl RPC使用不同归属标记，外层期限仍覆盖两者。每个RPC的stdout／stderr各256KiB，原生服务器日志每路2MiB，失败只返回安全布尔标记；同一沙箱同时最多一个控制面。command_timeout含启动与校验，清理最多另加90秒，客户端期限至少command_timeout+120秒。调用方文件、无关进程和预存节点状态不删除。

## 资源

仅Linuxx86_64／非root用户，2vCPU／4096MB，对外命令端口9000，构建根盘预算8GiB。临时TLS API使用客体随机端口及私有生成凭证，不是可复用公开集群端点。不宣称工作节点／kubelet／containerd／Pod／Docker／KVM／GPU／持久集群能力。峰值RSS／并发吞吐／其他架构和提供商未认证，每次校验都有控制面启动开销。

## 已验证

尚未记录任何通过的提供方测试。

当前1.0.0已实现源码及本地固定工作进程测试，原版模板Express SDK／完整HTTP／镜像／清理／最终CI／review／合并待验收。操作端没有执行原版K3s程序，单元固定进程不能认证Kubernetes。[实际记录](../.agents/evidence/verify/2026-10-21-k3s-agentless-validation.md)。

## 二次开发

```bash
python -m pytest -q k3s/test_runtime.py k3s/test_controller.py k3s/test_install.py
python scripts/check_template.py k3s --strict
python scripts/check_docs.py
```

先发布COPY／helper源码再准备不可变steps，保留准确哈希／回执及root构建、非root运行边界。真实验收必须通过SDK／HTTP校验原版有效Namespace和无效Service、原API操作后健康／0工作节点／NotFound及独立清理。TCP接受连接不等于内核监听归属或API就绪；清理验证/proc监听不存在及身份固定进程退出，不从健康无agent API推断Pod／工作节点执行。

## 贡献

遵守[贡献说明](../CONTRIBUTING.md)、[项目规范](../docs/project-standards.zh-CN.md)、[文档规范](../docs/documentation-standards.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)。独立源码、双语14章／设计／目录及索引证据一致，保留失败和已合并历史；最终head检查／review和普通固定SHA合并必需。

## 问题反馈

[Issue42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42)、[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)、[K3s上游](https://github.com/k3s-io/k3s/issues)。不公开私有集群凭证／地址／原始日志。

## 许可证

本包装层和K3s原源码Apache-2.0，[原许可证](UPSTREAM-LICENSE.md)保留并安装在原始ELF旁；附带组件保留上游声明／授权。不提交原二进制，不宣称提供商或厂商背书。
