# opensandbox-code-interpreter

[English](README.md).

## 做什么

原版OpenSandbox Code Interpreter镜像目录条目，通过OpenSandbox提供商／服务创建，不归本仓库构建，也不注册成Express模板。

## 技术栈

[固定上游30348cbd示例](https://github.com/opensandbox-group/OpenSandbox/blob/30348cbdfe4b9cfd49e0963617aed357a8f1ac4c/docs/examples/code-interpreter.md)使用v1.1.0镜像，也发布在sandbox-registry.cn-zhangjiakou.cr.aliyuncs.com/opensandbox/code-interpreter:v1.1.0。标签不是不可变镜像摘要或部署回执；提供商插件0.3.0使用原版生命周期／execd协议。

## 解决的问题

发现外部解释器镜像，同时与[Express code-interpreter-v1](../code-interpreter-v1/README.zh-CN.md)区分。当前Agent Sandbox OpenSandbox提供商支持shell／文件，原生code.interpret不支持、返回E8004；shell Python不能冒充原生内核／会话成功。

## 快速开始（CLI）

使用支持Node的[提供商宿主](../../using-templates.md#client-entry-compatibility)，不是仅原生steps构建入口。先安装准确公开提交并配置独立账号／服务。下面是源码／语法审查，真实后端NOT_RUN。替换本次创建的自有ID，只删除沙箱，不删托管模板定义。

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//opensandbox@9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d --yes
abx provider info opensandbox
abx provider doctor opensandbox
abx --provider opensandbox create --template opensandbox/code-interpreter:v1.1.0 --timeout 180 -y
abx --provider opensandbox exec <owned-sandbox-id> -- python3 -c 'print(6*7)'
abx --provider opensandbox kill <owned-sandbox-id> -y
```

## 快速开始（Python SDK）

安装[配套agent-sandbox-client](../../python-client-installation.md)及同一提供商／引擎，启动前配置下方独立设置。真实Agent Sandbox SDK示例仅执行shell／文件，已做语法检查、未跑真实后端。

```python
import asyncio, uuid
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    provider = "opensandbox"
    sb = await Sandbox.create(provider=provider, template="opensandbox/code-interpreter:v1.1.0", timeout=180,
        metadata={"verification": "managed-example-" + uuid.uuid4().hex})
    sid = sb.id
    try:
        result = await sb.commands.run("python3 -c 'print(6*7)'", timeout=30)
        assert result.exit_code == 0 and result.stdout.strip() == "42"
        path = "/tmp/owned-example-" + uuid.uuid4().hex + ".txt"
        await sb.files.write(path, "owned-example\n")
        assert await sb.files.read(path) == "owned-example\n"
        await sb.files.remove(path)
        assert not await sb.files.exists(path)
    finally:
        try:
            await sb.kill()
        finally:
            await sb.close()
    try:
        await Sandbox.get_info_by_id(sid, provider=provider)
    except SandboxNotFoundError:
        pass
    else:
        raise RuntimeError("owned sandbox cleanup is not verified")

asyncio.run(main())
```

生产流程需唯一metadata及私有创建意图，处理不确定创建响应；响应丢失加空列表不能证明清理成功。这里没有模型生成代码。

## 快速开始（HTTP POST）

镜像没有本仓库定义的POST /commands/execute_code。提供商使用POST /v1/sandboxes和可选OPEN-SANDBOX-API-KEY创建，保留原生解释器启动脚本，再通过execd执行shell／文件。原生解释器需要上游Code Interpreter SDK；Agent Sandbox run_code返回不支持E8004，不静默当作成功。见[准确契约](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d/opensandbox/README.md)。不虚构HTTP结果封装。

## 命令参考

| 操作 | 参数／结果 | 范围 |
| --- | --- | --- |
| Sandbox.create | provider字符串、template字符串、timeout整数秒、metadata字典；返回自有沙箱 | 提供商生命周期 |
| commands.run | command字符串、timeout整数秒；exit_code/stdout/stderr | 通用shell，不代表GUI或原生解释器 |
| files.write/read/remove/exists | 沙箱路径及文本／字节 | 文件往返 |
| kill/get_info_by_id | 准确自有ID和相同提供商配置 | 清理后独立回查不存在 |

未注册本仓库@command。不支持能力返回E8004，认证／网络／权限错误仍为失败。客户端超时与后端TTL不同；执行需期限与明确清理。

## 配置

ABX_OPENSANDBOX_BASE_URL必须为可用服务根地址，尾部/v1会规范化；自有服务允许匿名时密钥可省，其他情况配置ABX_OPENSANDBOX_API_KEY／OPEN_SANDBOX_API_KEY。域名／协议／代理／镜像项见固定提供商指南。不使用Express凭证，不转换Express模板ID；保留解释器原启动脚本，显式覆盖可能禁用原服务。

## 资源

CPU／内存／镜像版本／端点／设备能力由外部部署决定，本次没有真实运行时清单。示例180秒TTL不是提供商配额承诺。目录不能证明KVM／特权／GUI／原生内核可用；不公开密钥／私有地址／资源ID／原始日志，只删除本次沙箱／转发／测试文件。

## 已验证

尚未记录任何通过的产品／提供商运行。[日期NOT_VERIFIED状态](../evidence/verification-opensandbox-code-interpreter-2026-10-21.json)。

未配置明确服务；默认本地TCP接受连接，但只读HTTP请求RemoteProtocolError。准确已发布提供商单元／本地HTTP测试51通过、0失败／跳过，真实SDK原生解释器能力拒绝通过。这些是客户端／协议测试，不是真实OpenSandbox服务／解释器结果。真实后端仍待可用服务，不宣称Express资格。

## 二次开发

保留在managed_templates，排除源镜像选择／steps；不添加伪造目录、Alibaba Dockerfile、commands.py或tested_on。按[验证记录](../../../.agents/evidence/verify/2026-10-21-external-managed-catalog.md)复现固定提供商测试。提升运行时声明前必须真实SDK创建／shell／文件，原版解释器计算／输出和声明的持久内核行为，再独立清理；shell成功不能代替。新运行使用独立日期记录；源模板L1／L2／steps不认证外部托管ID。

## 贡献

遵守[贡献说明](../../../CONTRIBUTING.md)、[项目规范](../../project-standards.zh-CN.md)、[文档规范](../../documentation-standards.zh-CN.md)。双语指南／目录范围／日期证据一致；托管检查器只检查元数据与声明，不把NOT_VERIFIED升级为后端成功。

## 问题反馈

[Issue34](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/34)；[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[提供商](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原生服务／GUI行为属于上游。

## 许可证

本仓库文档／测试Apache-2.0；外部镜像／OS／应用／SDK／服务保留独立许可证和条款。不复制上游Dockerfile／二进制／注册镜像，源码检查不等于再分发授权或厂商背书。
