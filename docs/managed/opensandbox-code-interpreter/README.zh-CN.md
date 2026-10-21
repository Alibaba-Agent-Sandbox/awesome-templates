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

安装[配套agent-sandbox-client](../../python-client-installation.md)及同一提供商／引擎，启动前配置下方独立设置。以下真实Agent Sandbox SDK创建／shell／文件及原版解释器流程已在托管Docker验证。原生SDK使用[复现工作流](../../../.github/workflows/managed-opensandbox.yml)内准确上游源码及uv锁文件安装；上方访客CLI操作仍为源码审查，不能算单独CLI产品验收。

```python
import asyncio, os, uuid
from urllib.parse import urlsplit
from opensandbox import Sandbox as NativeSandbox
from opensandbox.config import ConnectionConfig
from code_interpreter import CodeInterpreter, SupportedLanguage
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
        url = urlsplit(os.environ.get("ABX_OPENSANDBOX_BASE_URL", "http://127.0.0.1:8080"))
        config = ConnectionConfig(domain=url.netloc, protocol=url.scheme,
            api_key=os.environ.get("ABX_OPENSANDBOX_API_KEY") or os.environ.get("OPEN_SANDBOX_API_KEY"),
            use_server_proxy=True)
        native = await NativeSandbox.connect(sid, connection_config=config)
        try:
            interpreter = await CodeInterpreter.create(sandbox=native)
            try:
                context = await interpreter.codes.create_context(SupportedLanguage.PYTHON)
                first = await interpreter.codes.run("owned_value = 37\nowned_value", context=context)
                assert first.error is None and first.result[0].text.strip() == "37"
                second = await interpreter.codes.run("owned_value + 5", context=context)
                assert second.error is None and second.result[0].text.strip() == "42"
                await interpreter.codes.delete_context(context.id)
            finally:
                await interpreter.aclose()
        finally:
            await native.close()
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
| 原版codes.create_context/run/delete_context | Python源码及原生上下文，result／error | 原生解释器／会话API |
| interpreter.aclose／native.close | 不删除远端 | 释放原生SDK本地资源 |
| kill/get_info_by_id | 准确自有ID和相同提供商配置 | 清理后独立回查不存在 |

未注册本仓库@command。不支持能力返回E8004，认证／网络／权限错误仍为失败。客户端超时与后端TTL不同；执行需期限与明确清理。

## 配置

ABX_OPENSANDBOX_BASE_URL必须为可用服务根地址，尾部/v1会规范化；自有服务允许匿名时密钥可省，其他情况配置ABX_OPENSANDBOX_API_KEY／OPEN_SANDBOX_API_KEY。域名／协议／代理／镜像项见固定提供商指南。不使用Express凭证，不转换Express模板ID；保留解释器原启动脚本，显式覆盖可能禁用原服务。

## 资源

本次真实托管Linuxamd64 Docker运行请求2CPU／3072MB／600秒，并核对实际容器镜像身份；未测量真实资源利用率，访客容量仍由所选后端决定。示例180秒TTL不是提供商配额承诺。目录不能证明KVM／特权／GUI／原生内核可用；不公开密钥／私有地址／资源ID／原始日志，只删除本次沙箱／转发／测试文件。

## 已验证

通过：原版OpenSandbox Docker后端、真实Agent Sandbox SDK创建／shell／文件、原版SDK连接同一ID、真实Jupyter健康与Python执行、持久／隔离上下文、程序异常、上下文删除、独立SDKNotFound／Docker容器不存在及本地引擎／服务退出。依赖及镜像准备后24项检查全通过，11.769秒。[原生回执](../evidence/verification-opensandbox-code-interpreter-2026-10-21-native-docker.json)、[真实托管运行](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39643705253)。

原解释器镜像摘要`opensandbox/code-interpreter@sha256:133a3c1720dd52291a019740c2987e7164ea6de79e23d8198798e58950ae2e6e`；execd摘要、准确原服务／原生SDK／提供商／CLI／客户端来源与实测版本见回执。原生SDK版本1.2.0rc2.dev222+g30348cbd，配套Agent Sandbox包0.3.0。隔离本地服务没有使用真实云／厂商账号或模型凭证。

这是OpenSandbox原生解释器验收，不是Express部署，也不代表Agent Sandbox原生code.interpret支持；通用run_code仍返回E8004。不推断GUI、特权嵌套或其他提供商资格。[原NOT_VERIFIED记录](../evidence/verification-opensandbox-code-interpreter-2026-10-21.json)及失败工程回执保留历史。

## 二次开发

保留在managed_templates，排除源镜像选择／steps；不添加伪造目录、Alibaba Dockerfile、commands.py或tested_on。按[验证记录](../../../.agents/evidence/verify/2026-10-21-external-managed-catalog.md)复现固定提供商测试。以后每次修改运行时／SDK／镜像均需真实SDK创建／shell／文件，原版解释器计算／输出和声明的持久内核行为，再独立清理；shell成功不能代替。新运行使用独立日期记录；源模板L1／L2／steps不认证外部托管ID。

## 贡献

遵守[贡献说明](../../../CONTRIBUTING.md)、[项目规范](../../project-standards.zh-CN.md)、[文档规范](../../documentation-standards.zh-CN.md)。双语指南／目录范围／日期证据一致；托管检查器只检查元数据与声明，不把NOT_VERIFIED升级为后端成功。

## 问题反馈

[Issue34](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/34)；[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[提供商](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原生服务／GUI行为属于上游。

## 许可证

本仓库文档／测试Apache-2.0；外部镜像／OS／应用／SDK／服务保留独立许可证和条款。不复制上游Dockerfile／二进制／注册镜像，源码检查不等于再分发授权或厂商背书。
