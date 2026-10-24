# 需明确授权的 canonical Express 验收

本页保留2026-10-18任务的固定版本维护流程，不是当前默认安装／启动指南。当前CLI/SDK验收请使用[公开源码启动测试](public-launch-testing.md#中文)；下文历史记录仍绑定原输入。

## 当前任务：本地极速版验收

用户于 2026-10-18 明确选择在本地发起真实部署和模型验收；本任务不要求在
Actions 运行云端／模型验收，本地执行也不等待临时 Actions Secret 存储授权。
下文 Actions 方案作为可选准备保留，尚未调度；正常 PR 的基础检查保留。

本地具备可用 Docker Engine、已授权的 Express／ACR 环境配置，并在 `ABX`
指定审查过的源码构建 CLI 后，执行现有命令：

```bash
python scripts/express_e2e.py python-hello --timeout 900 --idle-timeout 300 --wall-timeout 3600 --push-retries 0
```

逐个运行已审查模板，出现未完成的自有 intent 时先核对清理，再继续。
此命令覆盖真实镜像部署及 CLI／SDK 烟测；编码模板仍需严格真实模型验收。
见[源码运行指南](express-source-runtime.md)和[本轮结果](local-express-review-2026-10-18.md)。
当前控制端没有 Docker 可执行文件、socket 或引擎端点，完整镜像部署验收因本地
前置条件缺失而 BLOCKED。源码模型通过不能代替镜像部署证据，也不填写 `tested_on`。

此工作流仅供审查：尚未上传云凭据、调度云运行或获得 L2 通过。它真实执行已修复
清理结果的 `scripts/express_e2e.py`，覆盖生产 CLI 的 Docker 构建／推送、模板
READY、新沙箱、CLI／SDK 烟测及清理；镜像转移加官方注册仍是独立的补充验证。

模板／Docker 输入固定 integrated23 `b30833c`，生产 CLI 固定 `37b6d27`，控制器 SDK 固定
已合并的 `e86cb0b`，注入的 server 轮子源码独立固定 `e2cb27e`。canonical
运行器使用控制器常量中另行固定的清理修复版本，与模板固定同一个含清理修复的集成提交 b30833c。
CLI 使用 lockfile 的 `npm ci`；Python 使用固定公开源码包及明确的构建工具版本。

默认只生成 BLOCKED 授权报告，配置检查为绿不代表 L2。只有同仓 PR、显式开关
`approved` 及精确审查过的 workflow head SHA 均符合，才进入云任务；缺少配置
退出 2、记录 BLOCKED，不生成 provider 通过文件。更改源码后原 SHA 授权失效。

上传凭据到 GitHub Actions 是新的存储位置，必须先取得用户对具体工作流和凭据名
的授权。本改动不上传 secret、不创建云环境。完整名称与意义见
[英文表格](canonical-express-review.md#concrete-approval-and-secret-names)：两个
`ABX_REVIEW_20261016_` 授权控制项，加六个同前缀的 AK／SK、ACR namespace、
Express API key／URL／domain。地域固定杭州，不上传整个 `.env`、原生 E2B key
或模型凭据。云密钥仅注入实际执行和清理步骤。

先选 `python-hello`。之后可通过 dispatch 的 `templates` 或 PR 路径使用的仓库
变量 `ABX_REVIEW_20261016_TEMPLATES` 选择白名单名称、逗号列表或 `all`（23 个）。
串行执行，任一失败即停止排队的矩阵；全局 concurrency 防止同批重叠。工作流未进入
默认分支前，GitHub 不提供新 dispatch；取得存储授权并配置精确 SHA 后，操作者可
编辑同仓 PR 描述，触发支持的 `pull_request: edited` 事件。本文件不声称已调度。

运行器使用真实现有 flags：READY 900 秒、输出空闲 300 秒、单次部署 wall
3600 秒、推送重试 0；控制器到期先发 SIGINT 给 `finally` 清理机会，任务上限
120 分钟。只覆盖 canonical L2 烟测，不包含完整外部 HTTP 套件或镜像内真实模型 L3。

部署前拒绝已有 alias，并将本轮标识写入私有 intent；ACR 也先确认精确仓库不存在。
仅清理 `e2e-gh-<run_id>-<run_attempt>-<template>` 对应的本轮 tag／仓库，删除后须
官方 GET 返回 404。计算资源清理不明则保留镜像，不导出 PASS；`always()` 步骤
仅重试本轮 intent。不会删除共享仓库或 namespace。响应不明后的空列表不证明取消。

强制中止或 runner 丢失仍可能阻断清理、丢失 VM 内的私有 intent；该运行保持失败／
阻塞，操作者须按精确派生 alias 用同账号恢复核对，不能先启动更大的批次。
私有 journal、Docker 认证、原始日志及资源 ID 不上传；不替换临时 runner 的 HOME。

只有 canonical 退出 0、校验过的新 provider-pass 文件及清理全部确认，才上传
`express-日期.json`。状态报告单独记录源码 pin 与失败／阻塞。不自动提交 evidence、
填写 `tested_on` 或晋级 catalog。按规范审查后再集成通过记录，完成授权批次及清理后
通过批准的操作流程移除临时 Actions secrets。

控制器用 WNOWAIT 保留 leader 身份，在回收前清理自有进程组，覆盖正常退出、
非零退出与超时；继承平台 Requests/curl CA bundle 及代理配置。正式回执必须
包含 canonical runner 对 official alias 与 SDK sandbox 不存在的独立读回确认，
随后自有镜像 tag/repo 均经 HTTP 404 确认，才允许上传。
