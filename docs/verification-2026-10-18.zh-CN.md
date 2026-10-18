# 模板验收复核：2026-10-18

本页是日期化快照，不是发布或厂商认证。主分支与现有草稿合计 **23 个产品模板**；当前文档分支在 PR #82 的 16 个目录上继续工作，其他模板须通过表内所属 PR 查看。每行只适用于列出的准确提交。

| 模板 | 源码 PR / 提交 | 镜像与常规 CI | 当前标准部署 L2 |
|---|---|---|---|
| agents-cli | [#101](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/101) `d7e74574` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| amp | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| browser-automation | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| claude-code | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| codex | [#97](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/97) `2f4d33be` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| codex-agent-api | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| deepseek-harness | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| droid | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| gemini | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| hermes-agent | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| node-web | [#105](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/105) `7689edae` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| openclaw | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| opencode | [#104](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/104) `8bb61cfe` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| python-hello | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| qoder | [#82](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/82) `7cb0d943` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| qwen-code | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| pi | [#100](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/100) `ff0106c6` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| aider | [#102](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/102) `50c11425` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| swe | [#96](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/96) `70ac5a6e` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| osworld | [#94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94) `9a53b56c` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| ocr | [#103](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/103) `a4a18b0d` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| media-tools | [#106](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/106) `a7b8bdca` | 已通过对应镜像/本地任务；详见 PR | 未完成 |
| document-tools | [#107](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/107) `b06359f3` | 已通过对应镜像/本地任务；详见 PR | 未完成 |

镜像构建成功和源码运行 HTTP/模型证据仍分开记录。所有模板都有 CLI、Python SDK、HTTP POST 说明；新模板和具体参数以所属 PR 的双语 README 为准。源代码诊断不代表该版 Dockerfile 已通过标准部署。没有执行的原生厂商不能标记通过，历史 `tested_on` 不能转移到变更后的版本。

标准部署控制器 [PR #92](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/92) 仍默认关闭，当前选择器只支持其固定的 17 个输入，**不覆盖全部 23 个模板**。本机缺少 Docker；向 GitHub Actions 临时存储云配置还需单独明确批准。批准并更新准确审查提交与模板输入前，不能把 `all` 解释为全部现有模板，不能声称这批 PR 已全部可合并。

其他厂商（原生 E2B、Cube、OpenSandbox、容器版）按其实际环境、镜像适配和凭据分别验收；Express 配置不能转发给 E2B。已有镜像 URI 支持不代表原生模板部署已验收。

开发与验收层级见[规范](template-spec.zh-CN.md)，调用与文档归属见[使用模板](using-templates.zh-CN.md)。

[English](verification-2026-10-18.md)
