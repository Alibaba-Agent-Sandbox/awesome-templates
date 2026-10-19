# 在阿里云极速版验证 CI 镜像

[English](ci-image-acceptance.md)。大型资产在[平台步骤](platform-steps.zh-CN.md)中
可能传输较慢。显式镜像路径使用仓库现有 Dockerfile CI 导出，以及原生 CLI 的
`template create`，记录 `build_mode: image`。模板仍需真实运行验收。

## 准备公开输入

按照[步骤指南](platform-steps.zh-CN.md)安装已验证的原生 CLI 和 SDK。从
[上游 crane](https://github.com/google/go-containerregistry/releases)下载 Linux
工具并检查 SHA256。本次使用0.22.1，Linux_x86_64 压缩包 SHA256 为
`0ab7a1d6932a213aed964ce97666c3077fe691c8606413674a8b3e0b9ec4cda0`。

在精确已发布源码分支手动运行 `image-build.yml`，输入
`templates=<name>`、`export_images=true`。Actions 只构建公开源码，不上传云端、
仓库或模型凭据。等待整个工作流成功，在一天保留期内获取
`image-<name>-<checkout>` 产物 ID，并将对应源码提交拉到本机。

控制器验证仓库、工作流、产物身份、手动触发及成功状态、ZIP/TAR 哈希、当前
Dockerfile/COPY/清单契约、最终镜像的 commands.py 字节、固定服务端 SDK、
Linux amd64、非 root 用户及工作目录。仅 `tested_on` 元数据变化不要求重建，
运行源码变化必须重新导出。

## 执行真实验收

在进程环境中提供已有的 `ALICLOUD_ACCESS_KEY_ID`、
`ALICLOUD_ACCESS_KEY_SECRET`、`ACR_NAMESPACE`、`ABX_SANDBOX_API_KEY`、
`ABX_SANDBOX_BASE_URL`、`ABX_SANDBOX_DOMAIN`，以及读取产物用的
`GH_TOKEN` 或 `GITHUB_TOKEN`。`ABX` 指定原生 CLI，`NODE_PATH` 提供其依赖。
凭据值不可写入命令、版本文件或 Actions。

```bash
python scripts/run_ci_image_e2e.py ocr \
  --artifact-id <成功镜像产物ID> \
  --crane /path/to/verified/crane
```

临时 ACR 授权仅存放在 Linux 匿名内存 fd 中。临时私有目录只有指向继承 fd 的
符号链接，退出后清理。crane 不接收长期云密钥。先推送不含平台内容的空镜像
建立所有权，确认新仓库为 PRIVATE，再传输已验证镜像并读回不可变摘要。
不修改账号策略。

真实 `abx template create` 注册镜像摘要，官方 API 必须返回 READY，再执行
CLI/SDK 冒烟与完整外部 HTTP 验收。本控制器明确记录模型验收 NOT_RUN；Issue
要求真实模型时，仍需独立严格的镜像内模型验证。`--smoke-only` 明确跳过完整
HTTP 验收，不代表整个产品通过。

## 证据和清理

规范执行器独立读回沙箱及模板不存在；所有权日志限定的两个镜像标签及随机
仓库也必须删除并读回不存在，才发布通过回执。公开证据包含 CI/源码哈希和
结果，不包含账号命名空间、镜像引用、沙箱 ID 或凭据，并保留旧回执。

失败时保留仓库外的私有恢复目录，仅导出脱敏失败记录。丢弃日志前应核对并
清理其中的本次资源。失败或结果不明的注册不会因清理恢复而变成验收通过。
此前 step 失败与后续镜像成功分别记录，合并仍需当前提交的 CI 和正常审查。
