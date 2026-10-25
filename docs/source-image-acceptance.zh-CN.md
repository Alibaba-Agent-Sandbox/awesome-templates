# 源码镜像验证

[English](source-image-acceptance.md).

当前目录有 46 个源码模板和 4 个提供方托管条目。按照[公开启动测试指南](public-launch-testing.md#中文)从安装工具开始，测试极速版和 OpenSandbox 的源码构建、提供方返回的 CLI/SDK/HTTP 入口及独立清理。托管标识在其所属提供方单独验证。

## 镜像构建检查

**Template images (L1)** 工作流直接构建选定 Dockerfile、安装精确的已发布服务包，并检查原生依赖版本、非 root 工作目录写入及命名自检。它不注入 SDK 源码 wheel。镜像构建通过本身不能证明提供方启动或真实模型任务通过。

可选 `export_images` 保存已经验证的镜像一天；元数据记录准确源码、镜像摘要及实测服务包版本。镜像传输与默认源码构建是不同实验。

## 提供方启动与完整 HTTP 检查

使用 **Public template launch matrix**，选择 `distribution=published`、`provider=opensandbox`、`alicloud-express` 或 `both`，并设置 `templates=all` 或具体目录名。工作流安装官网已发布的 CLI/Python 包、所需公开 provider 插件，再调用已有 `scripts/public_launch_e2e.py`。精确的软件包/provider 提交及平台配置见该指南。

控制器启动文档中的源码，读取沙箱内实际服务包版本并核对 Dockerfile，通过 CLI、Python 和 HTTP 调用清单命令，检查服务认证、shell/文件及模板的完整 HTTP 控制器。浏览器模板直接使用提供方返回的 CDP/noVNC 访问地址。只删除本轮自建资源，并独立确认不存在。模型或厂商账号缺失单独列明。

旧 `test_opensandbox` 分支、固定旧 CLI/SDK 源码和直接使用 Docker bridge 的控制器已由该公开路径替代。模板自己的 Python 应用命令不依赖 provider 原生解释器。

## 极速版镜像传输

对已经验证并导出的镜像，可使用[镜像消费者](../scripts/run_ci_image_e2e.py)或有限并发批处理：

```bash
python scripts/run_image_e2e_batch.py --workflow-run EXPORTED_RUN_ID \
  --crane /path/to/verified/crane --private-root /private/template-acceptance \
  --workers 4 --output /private/template-acceptance/progress.json
```

`EXPORTED_RUN_ID` 是成功的精确源码镜像导出运行，`crane` 是已验证的镜像仓库客户端。私有目录保存本地控制台与恢复数据，必须位于仓库外。提供方与镜像仓库凭据保留在操作员环境中。`--templates` 选择具体目录；每个选中项都会实际运行，历史 PASS 不会自动跳过。清理不确定时停止新操作，已拥有资源的任务继续完成清理。

消费者传输本轮拥有的私有镜像并注册，通过当前统一启动流程使用清单中的启动命令、服务和环境，执行最新 SDK/CLI/HTTP 测试，并独立确认沙箱、模板和镜像仓库不存在。此实验验证已有镜像的消费，不证明默认源码构建路径。

## 记录与清理

保留失败尝试和日期回执，记录精确输入、控制器哈希、实际包版本、真实或受控 fixture 及独立清理结果。[2026-10-22 矩阵](../.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json)保留为历史。运行依赖变化后必须重新实测。
