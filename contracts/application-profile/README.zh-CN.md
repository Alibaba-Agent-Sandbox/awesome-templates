# 应用 profile 默认值

[English](README.md)

`profiles.json` 定义显式 `application.deployment.profile` 的固定字段。
`spec_version` 仍是 schema 版本，不用于选择 profile。`normalize.mjs` 与
`normalize.py` 复制清单，只补齐缺失字段；不校验预算、不构建镜像、不解析凭据、
不部署资源。消费者使用展开结果前，必须执行受支持的 schema 和语义校验。

保留显式 null 与冲突值，让校验拒绝它们。binding 目标仅补齐已有 binding，
并遵循 `state.bindingRef` 与 `deployment.ingressBindingRef`。
不合成引用、提供方或可配置预算。额外 binding 必须显式声明目标。

运行 `node contracts/application-profile/test.mjs` 与
`python scripts/test_spec_tools.py` 验证共享用例和 schema 回归。
消费者副本应保留源文件字节并记录来源版本及内容摘要，不另行维护默认字段表。
