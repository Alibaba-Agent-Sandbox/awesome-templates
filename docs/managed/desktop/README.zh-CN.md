# desktop

[English](README.md).

## 做什么

E2B托管desktop目录条目，厂商持有可变模板注册／镜像和桌面运行时；本仓库提供文档与测试，不复制或重建该模板。

## 技术栈

[固定上游9fe5f55f](https://github.com/e2b-dev/desktop/tree/9fe5f55fabe3bd9f0277661a830e1d228b463b44)将Ubuntu22.04／Xfce构建为desktop生产别名。这是源码观察，不是已部署版本实测；Desktop SDK已迁到E2B主仓库。Agent Sandbox通用shell／文件不代表原生GUI接口。

## 解决的问题

发现外部桌面ID，同时与独立[Express OSWorld切片](../../../osworld/README.zh-CN.md)区分。通用shell／文件和真实截图／输入／流验收分别记录。

## 快速开始（CLI）

使用支持Node的[提供商宿主](../../using-templates.md#client-entry-compatibility)，不是仅原生steps构建入口。先安装准确公开提交并配置独立账号／服务。下面是源码／语法审查，真实后端NOT_RUN。替换本次创建的自有ID，只删除沙箱，不删托管模板定义。

```bash
abx provider install Alibaba-Agent-Sandbox/awesome-providers//e2b@9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d --yes
abx provider info e2b
abx provider doctor e2b
abx --provider e2b create --template desktop --timeout 180 -y
abx --provider e2b exec <owned-sandbox-id> -- python3 -c 'print(6*7)'
abx --provider e2b kill <owned-sandbox-id> -y
```

## 快速开始（Python SDK）

安装[配套agent-sandbox-client](../../python-client-installation.md)及同一提供商／引擎，启动前配置下方独立设置。真实Agent Sandbox SDK示例仅执行shell／文件，已做语法检查、未跑真实后端。

```python
import asyncio, uuid
from agent_sandbox.api.sandbox import Sandbox
from agent_sandbox.models.errors import SandboxNotFoundError

async def main():
    provider = "e2b"
    sb = await Sandbox.create(provider=provider, template="desktop", timeout=180,
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

这个托管ID没有本仓库定义的POST /commands/screenshot或9000命令服务。E2B提供商使用POST /sandboxes和X-API-Key创建，shell走原生进程协议，不是虚构命名命令JSON。使用上面的SDK和[准确提供商契约](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d/e2b/docs/README.md)。Desktop截图／输入／流需要原版Desktop SDK及独立真实GUI验收。

## 命令参考

| 操作 | 参数／结果 | 范围 |
| --- | --- | --- |
| Sandbox.create | provider字符串、template字符串、timeout整数秒、metadata字典；返回自有沙箱 | 提供商生命周期 |
| commands.run | command字符串、timeout整数秒；exit_code/stdout/stderr | 通用shell，不代表GUI或原生解释器 |
| files.write/read/remove/exists | 沙箱路径及文本／字节 | 文件往返 |
| kill/get_info_by_id | 准确自有ID和相同提供商配置 | 清理后独立回查不存在 |

未注册本仓库@command。不支持能力返回E8004，认证／网络／权限错误仍为失败。客户端超时与后端TTL不同；执行需期限与明确清理。

## 配置

ABX_E2B_API_KEY必须独立真实E2B账号密钥；仅当自己的部署需要时设置ABX_E2B_BASE_URL／ABX_E2B_DOMAIN。固定提供商不读通用E2B_API_KEY或Express密钥。此环境通用密钥等于Express别名，未转发；没有真实ABX_E2B_API_KEY。

## 资源

CPU／内存／镜像版本／端点／设备能力由外部部署决定，本次没有真实运行时清单。示例180秒TTL不是提供商配额承诺。目录不能证明KVM／特权／GUI／原生内核可用；不公开密钥／私有地址／资源ID／原始日志，只删除本次沙箱／转发／测试文件。

## 已验证

尚未记录任何通过的产品／提供商运行。[日期NOT_VERIFIED状态](../evidence/verification-desktop-2026-10-21.json)。

Issue明确允许缺少真实E2B密钥时交付未验证目录。真实Agent Sandbox SDK在缺少独立密钥时于引擎／网络前拒绝，即使存在合成通用Express密钥。准确已发布提供商14项测试通过、0失败／跳过，包含真实固定E2B2.55.0SDK对本地HTTP的测试。这不是E2B桌面创建／截图／输入或Express验收。

## 二次开发

保留在managed_templates，排除源镜像选择／steps；不添加伪造目录、Alibaba Dockerfile、commands.py或tested_on。按[验证记录](../../../.agents/evidence/verify/2026-10-21-external-managed-catalog.md)复现固定提供商测试。提升运行时声明前必须真实SDK创建／shell／文件，原版Desktop SDK截图像素及输入／应用状态变化，再独立清理。新运行使用独立日期记录；源模板L1／L2／steps不认证外部托管ID。

## 贡献

遵守[贡献说明](../../../CONTRIBUTING.md)、[项目规范](../../project-standards.zh-CN.md)、[文档规范](../../documentation-standards.zh-CN.md)。双语指南／目录范围／日期证据一致；托管检查器只检查元数据与声明，不把NOT_VERIFIED升级为后端成功。

## 问题反馈

[Issue33](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/33)；[模板](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)、[SDK](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)、[提供商](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/issues)、[CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。原生服务／GUI行为属于上游。

## 许可证

本仓库文档／测试Apache-2.0；外部镜像／OS／应用／SDK／服务保留独立许可证和条款。不复制上游Dockerfile／二进制／注册镜像，源码检查不等于再分发授权或厂商背书。
