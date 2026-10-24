# 为 Agent Sandbox 模板贡献代码

[English](CONTRIBUTING.md)。先阅读 [AGENTS.md](AGENTS.md)、
[项目规范与完成标准](docs/project-standards.zh-CN.md)、
[文档规范](docs/documentation-standards.zh-CN.md)、
[模板规范](docs/template-spec.zh-CN.md)及[工程记录要求](.agents/README.md)。

## 模板清单

1. 复制 `_skeleton/` 到 kebab-case 目录，目录、manifest name 和目录索引 path 一致。
2. 默认 Express 构建文件保留阿里云基础镜像、generation 2、start_cmd、ready_cmd、固定依赖和 USER user，不添加 CMD/ENTRYPOINT。独立声明的显式构建方案可采用其他固定基础镜像，但保留原构建文件与非 root 运行契约，由调用方按名称选择，不由 Provider 自动改写。
3. 在 commands.py 用 server SDK 的 `@command` 注册命令；只在 main guard 内调用 start。
4. 根据 [设计骨架](docs/design/_TEMPLATE.md) 完成 `docs/design/<name>.md`。
5. 双语 README 使用规范要求的标题，参数、默认值、错误、CLI/SDK/HTTP 示例和限制一致。
6. 在 awesome-templates.yaml 添加条目。official 表示本项目维护，community 表示外部维护，experimental 标记开发中；这些标签不认证运行能力。适用组件测试及准确的提供方／入口证据仍是必需，模型功能声明必须有真实模型测试。
7. 安装固定源码 server/client 和测试依赖（`python -m pip install -r scripts/requirements-spec.txt`）后，从仓库执行：

   ```bash
   python scripts/test_spec_tools.py
   python scripts/check_template.py --all
   python scripts/check_docs.py
   python scripts/run_local_e2e.py
   ```

   本地检查不证明镜像、提供方和模型通过。Express L2 使用
   `python scripts/express_e2e.py <name>`；配置与退出码见模板规范。
   ACR 上传使用共享锁、空闲超时及重试；只有退出 0 且自有清理独立读回成功才能提交 pass 记录。

运行器拒绝已有官方模板别名；不确定的 deploy/create 结果保留私有 intent。
用 `python scripts/express_e2e.py --recover-intent PRIVATE_PATH` 精确对账；空列表不等于
未知请求已取消。恢复成功不将原失败变成通过。临时 ACR 仓库/tag 的保留和删除独立于
sandbox/template 清理。不要提交 `.env`、凭据、缓存或原始敏感日志；manifest 只声明空 secret 名。

## 命名命令与使用

```python
from agent_sandbox.server import command, start

@command("hello", description="Say hello.")
def hello(name: str = "World") -> str:
    return f"Hello, {name}!"

if __name__ == "__main__":
    import os
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
```

CLI 用 `abx run <sandbox-id> hello --arg name=Ada`。Python 用 `ProviderSandbox.connect(...)`
连接，获取 `await sb.application_client(9000, token=...)` 后调用
`await client.commands.run("hello", name="Ada")`。CLI launch 会启动应用；单独新建沙箱不等于启动该服务。
完整示例见[使用指南](docs/using-templates.zh-CN.md#clisdk-与-http)。shell 使用 `sb.commands.run` 或 `abx exec`。
HTTP body 直接是参数对象，响应是 result envelope。进程启动配置见
[运行环境](docs/runtime-environment.zh-CN.md)。

## Issue、评审与完成

跨提供方以源码目录为权威，按[提供方准备规则](docs/provider-preparation.zh-CN.md)
由各提供方负责 base、镜像和注册，不转换跨云 ID。只有所选工作流实际要求的能力才限制该路径；
模板提供 Python 不等于依赖统一解释器。目录提示和启动命令不能代替实际后端验收。

模板、目录、规范问题提交到本仓库；SDK/server 问题提交到
[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)，CLI 问题提交到
[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)，标题前缀
`[templates]`。先搜索已有 Issue，附复现、期望/实际、版本、提供方、generation 和精确提交。

先检查 diff，保留已有修改；重叠时使用独立分支。行为缺陷增加真实回归，运行针对性检查
和全部适用 CI，双语与设计同步；每次修改加入英文工程决策与带日期验证记录并更新索引。
失败、跳过和阻塞不能记为通过。

复用 Issue 并逐条完成验收。experimental 实现合并不代表部署或模型验收完成。
使用 Conventional Commits、仓库 PR 模板和任务分支，最新 head 的 CI 及必要评审通过后
按允许方式合并；独立确认 MERGED、Issue 条件和清理，不绕过检查或直接推 main。
历史合并证据保留。完整要求见[完成标准](docs/project-standards.zh-CN.md#完成标准)。

## 名称

产品 Agent Sandbox；CLI abx；npm `@agent-sandbox/cli`；客户端 distribution
`agent-sandbox-client`（Python namespace `agent_sandbox`）；镜像 server 包
`agent-sandbox-server`。不要安装同名无关项目 `agent-sandbox`。

当前 Express 验收脚本在构建/部署前检查实际 CLI 的 list/create/kill 合同。默认创建使用 `abx create TEMPLATE --detach --timeout SECONDS`，仅解析单个沙箱 ID；清理使用 `abx kill ID`。显式 SDK 创建仍需要兼容的 CLI 列表和清理命令。固定历史版本的审查工作流继续使用其固定脚本。
