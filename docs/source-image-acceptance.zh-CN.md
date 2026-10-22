# 源码模板镜像验收

[English](source-image-acceptance.md).

[Issue185](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/185)
跟踪全部46个源码模板的极速版常规镜像和原生 OpenSandbox Docker 验收。
steps 记录单独计算；工作流、镜像构建或托管解释器通过，均不代表这些源码模板已经通过。

## 极速版常规镜像

手动运行 **Template images (L1)** 工作流，选择目录中的模板名称并设置
`export_images=true`。该精确源码工作流成功后，在操作端配置已验证的原生 CLI、
配套 SDK 及账号凭据，运行
`scripts/run_ci_image_e2e.py TEMPLATE --artifact-id ID --crane PATH --sandbox-create sdk`。
凭据不会复制到 Actions。控制器验证归档、源码、SDK 和摘要，推送至本次独占的
私有 ACR 仓库，登记真实镜像并等待 READY，通过 CLI 和 SDK 调用，再运行原模板
完整 HTTP 测试。独立确认沙箱、模板和镜像仓库删除后，才发布通过记录。

OpenClaw 使用生成的测试令牌，Cursor 使用明确无效的合成密钥。预热服务不会继承
创建时的环境变量，因此在同一沙箱内启动独立测试服务来注入这些配置。
OSWorld／Chrome 桌面操作、Cursor／Devin 原生认证拒绝路径均为必测，不能仅靠
版本输出或跳过操作通过。缺少供应商或模型账号的 L3 测试仍明确列出。

## 原始 OpenSandbox Docker 后端

手动运行同一工作流，选择模板并设置 `test_opensandbox=true`、
`export_images=false`。按原模板 Dockerfile 和固定 server SDK wheel 构建镜像，
随后在隔离 Docker 运行器中启动固定源码的原始 OpenSandbox 服务、提供方及 CLI。
此流程不需要云账号或模型账号。

`scripts/opensandbox_template_e2e.py` 验证镜像身份及源码字节，通过 Agent Sandbox SDK
创建沙箱，独立观察实际 Docker 容器，测试 SDK 命令与文件 API，以非 root 用户
启动模板服务，通过真实 SDK 调用命名命令，再对实际容器桥接地址运行原模板的
完整 HTTP 测试。清理后独立验证 SDK NotFound、容器不存在、提供方进程已回收及
原始服务已停止。每个模板输出独立的脱敏记录，不上传原始日志、私有地址或资源 ID。

此流程验证模板的命名 API。提供方通用 `run_code` 仍返回 `E8004`，测试会确认此边界。
缺少 `code` 能力时，声明该能力的模板仍会被 CLI `template launch` 拦截；本次 SDK
源码运行验收不删除该能力检查，也不代表该启动路径通过。托管原生解释器的代码
执行 API 是另一项测试。

## 记录与清理

按时间保留各模板记录、失败尝试及仓库工程汇总。通过结果绑定当前源码、构建输入、
测试控制器哈希、SDK 和镜像身份；历史记录不覆盖。只删除本轮创建的资源，清理状态
不明确时不得通过。全部46个当前模板均具备两种后端及完整 HTTP 记录后，本项才完成。
