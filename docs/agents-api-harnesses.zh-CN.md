# Agents API Harness 指南

[English](agents-api-harnesses.md)

通过同一个 Gateway 接入任务、会话、文件与产物。所有模板使用同一份
[API 规范](managed-agents-api.zh-CN.md)，区别是 Sandbox 中的原生 Harness 与认证方式。
这些开发候选依赖尚未发布的配套运行时0.4.0a8 和 YAML v1 CLI，旧运行时不能替代。

| Harness／模板 | 凭据 | 端点／模型 | 模型协议 |
| --- | --- | --- | --- |
| [Codex](../agents-api-codex/README.zh-CN.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`、`OPENAI_MODEL` | Responses |
| [Qwen Code](../agents-api-qwen-code/README.zh-CN.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`、`OPENAI_MODEL` | Chat Completions |
| [Claude Code](../agents-api-claude-code/README.zh-CN.md) | `ANTHROPIC_API_KEY` | `ANTHROPIC_BASE_URL`、`ANTHROPIC_MODEL` | Messages |
| [Qoder](../agents-api-qoder/README.zh-CN.md) | `QODER_PERSONAL_ACCESS_TOKEN` | `QODER_MODEL`，默认 `auto` | Qoder 原生服务 |
| [OpenCode](../agents-api-opencode/README.zh-CN.md) | `OPENAI_API_KEY` | `OPENAI_BASE_URL`、`OPENAI_MODEL` | v1 CLI 的显式兼容 Provider |
| [DeepSeek Harness](../agents-api-deepseek-harness/README.zh-CN.md) | `DEEPSEEK_API_KEY` | `DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` | Messages |

## 选择与配置

一个模型 Key 不一定能供所有 Harness 使用。Codex 需要真正支持工具回合的 Responses。
Qoder 使用官方 PAT 及账号允许的模型；BYOK 取决于[官方方案和账号配置](https://docs.qoder.com/cli/custom-models)。
OpenCode 固定使用 v1 CLI，v2 CLI 是不同产品，不能直接替换安装包。
DeepSeek 模板使用[官方 DSH](https://github.com/deepseek-ai/deepseek-harness)，与仓库旧
`deepseek-harness` 自有工具循环不同。DSH 使用 Messages 端点，例如
`https://api.deepseek.com/anthropic`。

凭据与模型放在对应项目的私有 `.env`。地域、预算和原生 FC props 在 `template.yaml`
修改；表单位于 `registry.yaml`，本地运行不依赖该文件。不同应用使用不同名称和私有
部署记录。不要只修改 `vars.adapter`，应选择安装了对应 Harness 的模板。

## 统一协议与能力边界

通过 `GET /v1/models` 查询允许的模型，通过 `GET /v1/agent-sandbox/capabilities`
查询实际能力。创建 Session 返回201；输入返回202 和 Submission 头。忙碌时普通输入
返回409，显式 Submission 用于排队后续轮次，这与 OpenAI 中途引导当前轮次的语义不同。
当前统一入口不支持函数结果回传、远程 MCP、子 Agent 或自动审核。各原生工具的进度
粒度不同，收到最终文本不表示支持逐 token 流。

Close 释放计算并保留已存结果，DELETE 删除公开资源。异步清理须查询 Operation 至成功。
应用通过 `python scripts/release.py destroy` 删除；已有数据库、角色、网络及用户镜像
tag 由用户管理。

每个模板均提供 CLI 部署、Python `httpx` 和 curl 示例。没有专用 Gateway SDK；业务客户端
无需 Sandbox SDK 或单个 Sandbox endpoint。本协议子集不承诺 OpenAI SDK 完全兼容。
