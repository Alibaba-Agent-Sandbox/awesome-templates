# code-interpreter-v1

## 做什么

阿里云极速版托管的模板 ID，直接创建沙箱。此仓库不拥有它的 Dockerfile、镜像版本或部署生命周期。

## 技术栈

2026-10-19 实测清单；托管镜像可变，这些版本不是仓库固定依赖。

| Component | Observed version |
| --- | --- |
| Python | 3.13.13 |
| Node.js | v20.20.2 |
| Git | git version 2.47.3 |
| pip | 26.0.1 |
| numpy | 2.4.6 |
| pandas | 3.0.3 |
| matplotlib | 3.11.1 |
| jupyter | not installed |
| ipykernel | 7.3.0 |

## 解决的问题

无需构建用户镜像即可使用基础 shell、文件 API 和 SDK 代码执行。

## 快速开始（CLI）

Native CLI0.3 syntax (check `abx create --help`):

```bash
abx create --template code-interpreter-v1 --timeout 180 -y
abx exec <sandbox-id> -- python3 -c 'print(6*7)'
abx kill <sandbox-id> -y
```

标准入口差异见[兼容性](../../using-templates.md#client-entry-compatibility)。不删除提供方托管模板定义。

## 快速开始（Python SDK）

Install the [paired `agent-sandbox-client`](../../python-client-installation.md), then:

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="code-interpreter-v1", timeout=180)
    try:
        print((await sb.commands.run("python3 --version")).stdout)
        await sb.files.write("/tmp/owned-example.txt", "hello")
        print(await sb.files.read("/tmp/owned-example.txt"))
        await sb.files.remove("/tmp/owned-example.txt")
        result = await sb.run_code("print(6*7)")
        assert result.exit_code == 0 and result.stdout.strip() == "42"
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

本次 run_code 的原生服务返回 HTTP 404；SDK 回退到 shell，执行得到 42。没有验证原生代码解释器、多语言内核或持久上下文。安装 ipykernel 也不等于原生服务可用。

## 快速开始（HTTP POST）

该托管模板没有本仓库定义的 `/commands/*` HTTP 服务。使用 SDK 的 shell/files/run_code API；不编造 HTTP 地址或命名命令。

## 命令参考

SDK 参数：Sandbox.create(template: str, timeout: int=300)；commands.run(cmd: str, timeout: int) 返回 exit_code/stdout/stderr；files.write/read/remove/exists 接受沙箱路径；run_code(code: str) 返回执行结果。参见[公开 SDK 源码](https://github.com/Alibaba-Agent-Sandbox/python-sdk)。命名命令不适用。

## 配置

使用已配置的阿里云 SDK/CLI 账号。密钥只进入进程环境；不用模型密钥。创建时环境变量不保证修改已预热服务，参见[进程环境](../../runtime-environment.md)。

## 资源

本次实测 Linux x86_64、非 root；/dev/kvm 和 Docker socket 不存在。平台托管资源，不在此承诺固定容量、费用或镜像版本；创建时设置 timeout，结束后 kill 并回查列表。

## 已验证

| Provider | Runtime verification | Scope |
| --- | --- | --- |
| alicloud-express | [PASS receipt](../evidence/code-interpreter-v1-2026-10-19T154153Z.json) | SDK shell/files/run_code fallback + real CLI exec; cleanup confirmed |

本次 run_code 的原生服务返回 HTTP 404；SDK 回退到 shell，执行得到 42。没有验证原生代码解释器、多语言内核或持久上下文。安装 ipykernel 也不等于原生服务可用。

其他提供方未测试。此记录不属于仓库源码镜像的 L1/L2 部署证明。

## 二次开发

steps 用于构建新的源码模板，不用于重建这些提供方托管 ID。若需自定义依赖，从[源码骨架](../../../_skeleton/README.md)开始并创建新模板。复测本条目：

```bash
python scripts/verify_managed_templates.py code-interpreter-v1 --cli /path/to/abx --output /tmp/managed-proof
```

## 贡献

参见[贡献规范](../../../CONTRIBUTING.zh-CN.md)。更新证据时新增带时间戳的记录，不覆盖历史。

## 问题反馈

[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues) · [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues) · [agent-sandbox CLI](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues). 跟踪 Issue [32](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/32).

## 许可证

文档与验证脚本：Apache-2.0。托管镜像及内置软件遵循各自许可证；本仓库不重新分发该镜像。
