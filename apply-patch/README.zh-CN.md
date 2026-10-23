# apply-patch

## 做什么

执行官方 Codex 的 *** Begin Patch 方言，支持新增、更新、移动和删除。补丁通过私有临时文件进入原生二进制 stdin，不经过 shell 或命令行参数。

## 技术栈

阿里云 FC base v0.0.49，generation2，非 root user。`npm ci --ignore-scripts` 依据 [package-lock.json](package-lock.json) 的完整性值安装 @openai/codex0.162.1 和对应架构的官方原生包。版本检查后用 apply_patch argv0 调用同一个原生二进制。对应发布 tag 的源码提交为 [092d3acd](https://github.com/openai/codex/tree/092d3acd6bec3e3a14bdc7e7a2810ab628ab759d)。本模板使用官方预编译包，不宣称本地重新编译该提交。

## 解决的问题

为编码 Agent 提供真实 Codex 补丁工具，不需要模型账号、Rust 编译环境、Docker 或 KVM。支持 Linux x86_64/aarch64。

## 快速开始（CLI）

以下是原生 CLI 语法；标准入口差异参阅[兼容说明](../docs/using-templates.md#client-entry-compatibility)。

```bash
abx template deploy ./apply-patch -y
abx create <template-id> --detach --timeout 300
abx run <sandbox-id> apply_patch_smoke
abx run <sandbox-id> apply_patch --arg 'patch_text=*** Begin Patch
*** Add File: hello.txt
+hello
*** End Patch'
abx kill <sandbox-id>
abx template delete <template-id> -y
```

## 快速开始（Python SDK）

Install the paired [`agent-sandbox-client`](../docs/python-client-installation.md):

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        patch = "*** Begin Patch\n*** Add File: hello.txt\n+hello\n*** End Patch\n"
        result = await sb.run("apply_patch", patch_text=patch)
        assert result["exit_code"] == 0
        assert await sb.files.read("/home/user/app/hello.txt") == "hello\n"
    finally:
        await sb.kill()
        await sb.close()

asyncio.run(main())
```

## 快速开始（HTTP POST）

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <server-token>' \
  -d '{"patch_text":"*** Begin Patch\n*** Add File: hello.txt\n+hello\n*** End Patch\n"}' \
  '<sandbox-port-9000-url>/commands/apply_patch'
```

Response envelope: `{"result":{"stdout":"...","stderr":"","exit_code":0}}`.

## 命令参考

| Command | Parameters | Result |
| --- | --- | --- |
| apply_patch | patch_text: str required, nonempty UTF-8 up to256KiB; cwd: str optional empty=WORKSPACE, existing subdirectory | {stdout: str, stderr: str, exit_code: int} from actual native parser |
| apply_patch_version | none | actual native `codex-cli 0.162.1` |
| apply_patch_smoke | none | APPLY_PATCH_OK only after real add/update/move/delete/literal bytes and owned cleanup |

非零上游结果以非零 exit_code 返回，HTTP200 只表示命令完成，不表示补丁成功。缺失或未声明参数为400，未知命令404。SDK 会将 JSON 标量转成声明的字符串；无效补丁仍由原生解析器拒绝。所有文件路径和移动目标必须相对于选定 cwd，拒绝绝对路径、..、反斜杠与现存符号链接。整个补丁先检查路径。上游失败可能留下工作区内部分改动；操作不保证事务。

## 配置

无需模型密钥。WORKSPACE 默认 /home/user/app；ABX_SERVER_TOKEN 为空占位符，应在服务进程注入。参阅[运行环境](../docs/runtime-environment.md)。原生补丁进程只继承 PATH 和 LANG，不获得模型或云密钥。

## 资源

2vCPU、2048MB、9000端口。每次补丁最多30秒，每个输出流最多256KiB，清理自建进程组后才回收父进程。临时补丁文件自动关闭；补丁修改的用户文件由调用者管理。预检不是防御同一用户并发改名/符号链接竞态的系统隔离边界。

## 已验证

当前工作流清单尚无项目认可的验收收据。历史验收记录仅证明原输入和原调用路径；参见[工作流验证](../docs/workflows.zh-CN.md)。

## 二次开发

从[平台 steps](../docs/platform-steps.zh-CN.md)生成：`python scripts/prepare_steps.py apply-patch --output /tmp/patch-steps`。真实构建验收：`python scripts/run_steps_e2e.py apply-patch`。本地先 `npm ci --prefix apply-patch --ignore-scripts`，再运行 install_alias.py，将独立 bin 目录加入 PATH 后执行测试。更新时同步 npm 锁文件、原生版本、源码 tag 和许可证；保留历史证据。

## 贡献

遵循[贡献规范](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计](../docs/design/apply-patch.md)。

## 问题反馈

[模板 Issue60](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/60)；CLI 问题：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)；SDK 问题：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。

## 许可证

模板与 Codex：Apache-2.0。保留源码固定提交的 [upstream-LICENSE](upstream-LICENSE)，并保留官方 npm 原生包的元数据和通知。

### 2026-10-20完整 step 检查点：模板1.0.0

[真实对应版本 step](evidence/express-2026-10-20.json)及[完整外部 HTTP 控制器](evidence/verification-steps-2026-10-20T154625Z.json)通过：官方 READY、真实 Python SDK 创建、全部 CLI/SDK smoke，5 PASS/0 FAIL/0 SKIP；自有沙箱／模板均独立确认清理。本回执模型验收仍为 NOT_RUN，不改变旧镜像／模型范围。复现及精确服务端／控制器来源见[step 指南](../docs/platform-steps.zh-CN.md)。
