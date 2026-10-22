# 在阿里云极速版验证 CI 镜像

[English](ci-image-acceptance.md)。大型资产在[平台步骤](platform-steps.zh-CN.md)中
可能传输较慢。显式镜像路径使用仓库现有 Dockerfile CI 导出，以及原生 CLI 的
`template from-image`，记录 `build_mode: image`。模板仍需真实运行验收。

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
建立所有权，确认新仓库为 PRIVATE，再传输已验证镜像并读回内容摘要。
不修改账号策略。

真实 `abx template from-image` 注册本次独占的 review 标签，并在注册前和运行后独立读回内容摘要确认未变，官方 API 必须返回 READY，再执行
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

2026-10-19 真实 digest 形式注册被平台按 latest 拉取而失败，因此该路径使用本次独占标签并在前后读回摘要；不宣称平台支持 digest 引用或仓库标签不可变。

执行器在产物或云端操作前检查外部控制器导入依赖。先安装所需模块（OCR需要Pillow），缺少控制器不代表提供方通过。测试失败与独立观测到的云资源清理分别记录；code-server/Next/Vite 的次要端口地址来自 SDK。

### 选择真实 Python SDK 创建

验收要求实际执行 `agent_sandbox.api.sandbox.Sandbox.create` 时，为 step 或已验证
镜像 runner 添加 `--sandbox-create sdk`。默认 `cli` 保留已有 `abx create` 行为。
两种入口均先等待自有模板 READY，再通过 CLI 与 SDK 执行命名 smoke，最后执行
同样的 sandbox/template 清理和独立不存在检查。

例如 `python scripts/run_steps_e2e.py python-hello --sandbox-create sdk` 真实构建
平台 step，并通过 Python 创建其沙箱。已核验镜像路径则在
`scripts/run_ci_image_e2e.py` 已有的 artifact ID、已验证 crane 参数外添加
`--sandbox-create sdk`。回执 `sandbox_create` 明确记录
`python-sdk-Sandbox.create` 或 `abx create`；较早回执不能证明未记录的 SDK 创建。
SDK timeout 表示沙箱生命周期，与构建 READY 等待和请求时限分别配置。创建响应
丢失时保留私有恢复记录，不能发布验收。关闭本地客户端不删除云沙箱；runner
随后销毁自有资源并独立确认不存在。

控制器先验证实际 CLI 的 `template from-image --help` 契约，再下载归档或写入云资源。
`--private-root` 可指定私有归档和恢复记录目录，内存认证所需的文件描述符链接仍使用
原生临时文件系统，认证值始终只保存在匿名内存中。
