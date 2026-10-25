# 极速版云端审查

[English](canonical-express-review.md).

当前极速版验证统一使用[公开模板启动工作流](public-launch-testing.md#中文)、已发布 CLI/Python 包和 provider 返回的应用访问地址；旧的固定提交部署任务已退役。

## 当前任务：本地极速版验收

从指南中的工具安装开始，配置自己的极速版账号及构建环境，再对选定源码运行 `scripts/public_launch_e2e.py`。已有镜像的消费见[源码镜像验证](source-image-acceptance.zh-CN.md)，并与默认源码构建分开记录。

现有 `authorization` CI 检查保留为只读验证，核对显式启用、精确审阅提交及同仓库范围，不执行云端请求。真正的云验证只通过显式公开启动工作流或操作员已配置的本地调用执行。授权检查成功不等于部署通过。

旧部署实现、23 模板快照、旧 SDK/CLI 固定源码及对应云任务已删除，不新增兼容部署程序。按照当前公开工作流的配置名使用凭据；未经明确授权，不把凭据复制到 Actions；值不写入文件、回执或 Issue。只读检查不存储或转发 provider 凭据。

在 **Public template launch matrix** 选择当前目录或 `all`，平台选 `alicloud-express`，按指南固定准确输入。授权辅助程序读取当前源码目录，不再维护另一份快照名单。

记录实际包/源码、完整 CLI/SDK/HTTP 结果、跳过项和独立清理，失败尝试保持失败。历史 canonical 回执仍对应当时输入；[旧实现](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/2bacceec5161181e1f73f737955ddc8fae250ed9/scripts/canonical_express_review.py)可在不可变 Git 历史中查看。当前辅助文件只保留只读授权计划，以及公开启动程序仍调用的自有 ACR 删除逻辑。
