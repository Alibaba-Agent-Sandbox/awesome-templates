# Claude Code usage

The maintained usage contract is in the template’s [English README](../claude-code/README.md) and [中文 README](../claude-code/README.zh-CN.md).

The template uses the Alibaba generation-2 base, a pinned official Claude Code CLI and the Agent Sandbox server. An actual compatible Anthropic credential is required for model calls; a missing key is not model acceptance.

Model settings must reach the server before it starts. Follow [runtime environment configuration](runtime-environment.md) ([中文](runtime-environment.zh-CN.md)) for prewarmed services. Use the same configured port from SDK, CLI and HTTP.

旧文档链接保留。当前镜像、命令参数、认证、超时、开发及验收说明统一维护在上方双语模板指南中；创建环境不能追溯修改已运行的命名服务。
