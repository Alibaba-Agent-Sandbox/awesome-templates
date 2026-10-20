# 使用 Agent Sandbox step 构建模板

`abx template deploy --build steps` 向阿里云极速版发送基础镜像和有序步骤，
不需要本地 Docker 或 ACR 上传。[English](platform-steps.md)。

## 前置条件和模式

通过环境配置已有授权的 Express API 与阿里云控制面凭据。CLI 的 deploy、官方
list/info/delete 和 sandbox 命令须匹配[验收运行器](../scripts/express_e2e.py)。
[安装指南](using-templates.zh-CN.md)中的源码 CLI 提供这些接口。仅有版本号不足以
证明兼容：公开 0.4.0 的标准 list/create 接口与本运行器的原生接口不同；0.3.0
独立二进制还需要可用的官方阿里云 SDK 模块，固定源码构建会安装它们。

auto 有 Dockerfile 时选 Dockerfile；显式 steps 使用 manifest 步骤。不与
`--acr-namespace` 或 `--legacy-api` 混用；创建 sandbox 不选择构建模式。
CLI 的[模式契约](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/design/template-build-modes.md)
说明发送形式，提供方仍需实际验证。Express ENV 参数是交替键值，例如
`{type: ENV, args: [LANG, C.UTF-8]}`；2026-10-19 真实试验拒绝了单参数
`LANG=C.UTF-8`，失败记录保留。

## 准备真实模板

steps 不自动上传 COPY 源文件。生成独立临时 manifest：

```bash
python scripts/prepare_steps.py python-hello --output /tmp/python-hello-steps-review \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
```

输出目录必须全新。可选 server 提交与现有镜像 CI 注入的源码一致并单独记录；省略时
使用 Dockerfile 固定 fallback。转换器保留 RUN/ENV/WORKDIR/USER 顺序、heredoc 和
续行，仅传输明确 COPY 的公共源码及哈希和权限。优先压缩内嵌；较大配方下载已发布
checkout 精确提交的归档，并在写入前逐文件验证，临时网络错误有界重试。构建阶段显式
选择 root 安装 Docker profile 的依赖，最后恢复 USER user。云端构建前先发布不可变提交。
可选本地 wheel 分支替换为
固定源码安装。保留 USER user，EXPOSE 由 manifest ports 表达。

仅接受单 stage 阿里云 FC profile；未知指令、未审查的 wheel 分支、目录外/符号链接/
通配符/secret 命名的 COPY、过大文件、浮动提交和重复输出目录均拒绝。它是当前目录
profile 的适配器，不是通用 Dockerfile 解释器。Express 的 steps 序列化上限为 16 KiB；
RUN/源码压缩，超过保守的 15,000 字节预算在云调用前拒绝，记录实际大小及源码提交。
原生 ENV 未一致传给后续 RUN，因此转换器对 RUN 显式导出构建环境与工作目录，
并按真实独有 base 探针的 v0.0.49 PATH 展开运行 PATH。其他 tag 需传入独立验证的
--base-path，不使用控制器本机 PATH。
部署前检查生成 manifest 和
steps-provenance.json；仅含公共源码，不包含凭据或模型运行设置。

## 部署与调用

在源码仓库执行完整真实验收：

```bash
python scripts/run_steps_e2e.py python-hello \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
```

CLI 不在 PATH 时通过 ABX 环境变量指定已验证命令。可以传多个目录，或用 `--all`
顺序验证全部模板。命令会产生真实云端费用，使用唯一自有资源，私有恢复记录留在
checkout 外，不上传 Actions 凭据。

已准备目录的底层等价命令为：

```bash
python scripts/express_e2e.py /tmp/python-hello-steps-review --build steps --push-retries 0
```

运行器执行真实 CLI deploy，先私有记录返回 ID，再轮询官方 GetTemplate 到 READY，
创建新实例，通过外部 CLI 和 SDK 调用全部 smoke，清理后独立读回确认 sandbox 和
template 不存在。submitted、构建失败、未知状态、smoke 错误、超时或不确定清理不能
写 pass。恢复沿用精确所有权的 `--recover-intent`。

手动操作可用 `abx template deploy /tmp/python-hello-steps-review --build steps -y`，
等官方 READY 后使用原模板 README 的 CLI/SDK/HTTP 调用，结束时只删除本次资源。
提交成功本身不是验收记录。

## 证据与限制

批量运行器在原模板 evidence 中保留每次脱敏结果，包括失败、源码哈希、基础镜像和
server override。完整成功记录包含 build_mode steps、外部调用结果和清理确认。
旧记录不覆盖，原始云日志与资源 ID 不进入仓库。

当前全部 Dockerfile profile 可以本地转换；这不代表全部真实构建通过。step 通过仅
证明记录哈希的生成配方，不证明本地 Docker 构建、未实测依赖、未运行模型 L3 或其他
提供方通过。以每模板本轮记录及[分级规范](template-spec.zh-CN.md)为准。

## 本次实测的原生 CLI 配方

下面固定的是本次实际运行的 Linux x86_64 原生入口，与现有标准入口并存。控制器使用 Node22.22.2/npm；独立二进制本身需要下列两个精确版本的阿里云 SDK 外部模块。来源、SHA256 和模块组合已经实际使用，不能仅凭显示版本号替换接口。该步骤只下载公开工具，不创建云资源。

```bash
ABX_NATIVE_DIR="$(mktemp -d /tmp/abx-native-review.XXXXXX)"
curl --fail --location --max-time 120 \
  --output "$ABX_NATIVE_DIR/abx" \
  https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/download/v0.3.0/abx-0.3.0-linux-x64
printf '%s  %s\n' \
  e6d1c46626fd3f48e86b23bc99b0b8d565dfadd3f61a42ea352a27cb637d9cdd \
  "$ABX_NATIVE_DIR/abx" | sha256sum --check
chmod 700 "$ABX_NATIVE_DIR/abx"
npm install --prefix "$ABX_NATIVE_DIR/modules" --ignore-scripts --no-audit --no-fund \
  --save-exact @alicloud/fcsandbox20260509@1.5.1 @alicloud/openapi-core@1.0.8
export ABX="$ABX_NATIVE_DIR/abx"
export NODE_PATH="$ABX_NATIVE_DIR/modules/node_modules"
"$ABX" template deploy --help
```

随后按上文配置进程环境中的极速版账号，并使用固定服务端提交的构建命令。脚本通过 ABX/NODE_PATH 使用该独立工具目录。不要把标准入口的参数与原生验收入口混用。清理本次沙箱、模板和日志后，再删除自己创建的工具目录。

大型资产也可使用独立记录的 [CI 镜像验收路径](ci-image-acceptance.zh-CN.md)，
通过真实 Dockerfile CI 导出及原生镜像注册运行，保留独立来源信息。

## 实测的大资产传输限制

2026-10-19 的真实构建步骤诊断下载8MiB时，所选 code-server/Rust 资产分别耗时
385/398秒，Go/Hermes 源码样本则不到2秒。这是实测，不是固定带宽承诺。
浏览器安装曾在306.777秒遇到 RUN 流截止，但后续成功诊断说明它不是统一的
300秒执行上限。应拆分构建阶段、限制下载并保留错误；超时不是验收通过。
重型模板仍需自己的当前配置成功回执，部分网络探针、本机安装和单独CI构建
均不能代替。

运行用户切换前，生成的步骤显式将 /home/user/app 归属设为 user:user。真实完整 Python/Node HTTP 验证发现原生 WORKDIR 的 root 归属导致文件写入失败；仅设置 COPY 文件归属不足。基础版本冒烟不能代替工作区文件往返测试。旧失败与基础冒烟回执保留各自范围。

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
