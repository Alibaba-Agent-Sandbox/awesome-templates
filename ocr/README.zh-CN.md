# OCR

使用官方 Tesseract 在 CPU 上识别英文图片。参见 [English](README.md)。

## 做什么

`ocr(image_path)` 处理工作区中的一张 PNG/JPEG，返回文字、尺寸、词数，以及私有 TXT/TSV 文件路径和 SHA256。实际运行 OCR 引擎，无需模型、API key 或网络。空白图片可以正常返回零个词。当前只安装英文识别数据；中文文档不代表支持中文 OCR。

## 技术栈

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，默认区域/版本为 `cn-hangzhou` / `v0.0.49`。Debian 13 的 Tesseract/libtesseract 固定为 `5.5.0-1+b1`，英文和方向数据为 `1:4.1.0-2`，Leptonica 为 `1.84.1-4`；其他系统依赖由发行版仓库解析。Pillow `11.3.0` 先按提交的 wheel SHA256 白名单下载，再以 --no-index/--no-deps 离线安装，禁止源码安装。SDK 优先使用构建时注入的 wheel，否则使用固定源码提交 `e2cb27e24fde0a67112f82b8d44af463445a5d1a`。以非 root 的 `user` 运行，工作区 `/home/user/app`，端口 9000；保留原 HOME。

## 解决的问题

无需 GPU 或外部 OCR 服务，将英文图片转为可检索文字和词级坐标。本接口每次处理一张图片，使用固定分段模式；不支持 PDF、压缩包、批量、自动下载语言或承诺手写识别。

## 快速开始（CLI）

先用 `abx create --help` 确认已安装入口。下面的完整示例使用原生 CLI 语法。若帮助列出 `--detach`，则是标准极速版入口：创建改用 `abx create <template-id> --detach`，清理改用 `abx kill <sandbox-id>`（不加 `-y`）；命名命令 `abx run` 不变。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

```bash
abx template deploy ./ocr -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> ocr_smoke
abx run <sandbox-id> ocr --arg image_path=/home/user/app/fixtures/sample.png
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

自定义图片先通过 SDK 文件 API 上传至工作区。成功结果保留在返回的 `.ocr-<随机值>/` 目录，供下载；使用后由调用者删除，或销毁沙箱。smoke 只删除自己创建的图片和结果。

## 快速开始（Python SDK）

使用 `agent-sandbox-client` 与配套 `agent-sandbox-server`；按[固定源码安装说明](../docs/python-client-installation.md)安装。

按[固定版本源码安装说明](../docs/python-client-installation.md)安装客户端与配套服务端，导入 `agent_sandbox`。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        result = await sb.run("ocr", image_path="/home/user/app/fixtures/sample.png")
        print(result["text"])
        print(result["text_path"], result["tsv_path"])
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 调用命名命令，`sb.commands.run` 是通用 shell API。本模板保留共享服务器的 shell/files/code/ports 能力；OCR 路径限制只约束 OCR 命令，不限制其他已认证服务器 API。

## 快速开始（HTTP POST）

使用沙箱的 9000 端口 URL 和服务器认证 token，建议客户端超时至少 90 秒，以覆盖有界处理和清理。

```bash
curl --fail-with-body --request POST --max-time 90 "$ABX_SERVER_URL/commands/ocr" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"image_path":"/home/user/app/fixtures/sample.png"}'
```

HTTP 200 返回 `{"result": ...}`；参数缺失/类型错误为 400，认证失败为 401，路径/图片内容拒绝或执行失败为 500，错误对象包含 `error` 和 `type`。结果完成后一次性返回；客户端断开不保证服务端取消。

## 命令参考

| 命令 | 参数 | 返回 | 作用 |
|---|---|---|---|
| `ocr_version` | 无 | string | 实际 CLI 固定版本 `tesseract 5.5.0`。 |
| `ocr_setup_check` | 无 | object | 可用性、引擎/Pillow 版本和 `eng`，不处理图片。 |
| `ocr` | 必填 string `image_path` | object | 文字、词数、尺寸、语言、引擎版本、私有目录、TXT/TSV 路径和哈希。 |
| `ocr_smoke` | 无 | string | 真实样例像素识别并独立检查两份文件，最后清理自有结果。 |

路径可以相对 WORKSPACE 或绝对位于其内；拒绝 `..`、任何符号链接、设备、目录和 FIFO。工作区必须由运行用户拥有。编码文件最多 10 MiB，每边最多 8192 像素，总像素最多 1600 万，仅接受单帧 PNG/JPEG。应用 EXIF 方向、去掉元数据并将透明背景合成白色，在私有临时目录写 RGB PNG，原图保持不变。

同一时刻只运行一个 OCR；并发请求立即失败。固定 argv 为 `tesseract <私有input.png> <私有输出前缀> --tessdata-dir <固定数据目录> -l eng --psm 6 --dpi 300 txt tsv`，不用 shell，不接受自定义 flags。引擎墙钟超时 45 秒，CPU 软/硬限制 30/31 秒，地址空间 512 MiB，单文件 4 MiB，禁用 core dump，OpenMP 单线程。版本检查最多 5 秒。TXT 最多 1 MiB，TSV 最多 4 MiB，每个诊断管道最多 1 MiB，归一化临时 PNG 最多 64 MiB。输出目录权限 0700，文件 0600。

## 配置

| 名称 | 必填 | 默认值 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 空 | 创建沙箱时配置，客户端发送 bearer token。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 直接本地启动端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在、运行用户拥有的输入输出根目录。 |
| `OCR_TESSERACT_BINARY` | 否 | `/usr/bin/tesseract` | 运维配置的绝对程序路径，仍检查固定版本。 |
| `OCR_TESSDATA_DIR` | 否 | `/usr/share/tesseract-ocr/5/tessdata` | 运维配置的绝对目录，包含英文 traineddata。 |

后两项仅用于本机诊断，不是命令参数。子进程只接收原 HOME/PATH、可选动态库路径和固定 locale/线程设置，不转发云端或模型凭据。通用 shell/files API 和运维配置需要独立控制访问。

## 资源

| 资源 | 值 |
|---|---|
| CPU | 1 vCPU；引擎为 OpenMP 单线程 |
| 内存 | 沙箱 1024 MB；引擎地址空间上限 512 MiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs；调用者清理保留的结果目录 |

## 已验证

| 提供方 | 范围 | 证据 |
| --- | --- | --- |
| alicloud-express | 版本1.0.1真实CI镜像、官方READY、CLI/SDK、完整HTTP19通过/0跳过，沙箱/模板/镜像仓库独立清理确认 | [2026-10-20](evidence/express-2026-10-20.json)、[完整检查](evidence/image-http-2026-10-20T054627Z.json) |
| alicloud-express | 1.0.1 真实平台 step 构建、官方 READY、CLI/SDK 和完整 HTTP 19 通过 / 0 失败 / 0 跳过；独立确认 sandbox/template 清理 | [step 回执](evidence/express-2026-10-20T061143Z.json)、[完整 HTTP](evidence/full-http-steps-2026-10-20T061143Z.json) |

1vCPU/1024MB资源修复正式版本1.0.1已独立验收，包括随机数字图像、原始输入
字节不变、下载TXT/TSV后的文字/哈希/置信度/边界检查、空白负例和产物删除。
此前1.0.0候选通过及失败记录保留在历史部分，没有重标版本。本次使用已核验
CI镜像和真实原生镜像登记。上述另一组 step 成功回执证明同版本真实执行了
平台 step；较早失败尝试仍作为历史保留。


## 历史验收

| Provider | Scope | Evidence |
| --- | --- | --- |
| alicloud-express | Actual CI image, official READY, CLI/SDK, full HTTP19 PASS/0 SKIP and independent sandbox/template/registry cleanup | [2026-10-19](evidence/express-2026-10-19.json) |

当前1vCPU/1024MB配置已通过真实极速版完整验收，包括随机数字图片、原图字节不变、TXT/TSV下载及独立内容/哈希/像素边界检查、空白负例和所有权清理。[完整记录](evidence/image-http-2026-10-19T181012Z.json)。较早2vCPU/1GB配置被平台拒绝及本机控制器缺少Pillow的失败保留，均不重标为通过。

源码回归实际使用 Tesseract 5.5.0 / Pillow 11.3.0，27 项通过。source HTTP 验证 19 通过、0 失败、0 跳过，包括独立随机数字图片、下载 TXT/TSV 后核对哈希/文字/置信度/坐标，以及空白图片负控。这些是源码运行结果。实际镜像 L1、补充 changed-image Express 验证仍待执行；正式 `abx template deploy` / `scripts/express_e2e.py` L2 未执行。`tested_on` 保持空，目录状态为 experimental。详见[验证记录](../.agents/evidence/verify/2026-10-16-ocr-runtime.md)。

## 二次开发

运行 `python3 scripts/check_template.py ocr --strict` 和本目录两个 pytest 文件。`OCR_TEST_REAL=1` 开启真实引擎回归；实际验收必须设置 `E2E_REQUIRE_OCR=1`，缺失依赖应失败而非跳过。修改时保留独立 artifact 下载验证、原图不变和空白负控。语言、PDF、批量和分段模式扩展需独立设计与测试。见[设计](../docs/design/ocr.md)。

Linux 进程管理通过 `waitid(WNOWAIT)` 保留 leader 身份，持续排空有界管道，在成功、非零退出、超时或 Python 取消后先杀自有进程组再 reap。主动 `setsid` 逃离不在该进程组保证内；服务器被 SIGKILL 时无法执行 Python 清理。最终隔离边界是整个沙箱销毁。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py ocr --timeout 1200 --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。公开 runner 执行 CLI/SDK fixture smoke；另一完整 HTTP 控制器在 READY 后通过了全部 19 项断言，见[实际执行步骤](../.agents/evidence/verify/2026-10-20-ocr-step-acceptance.md)。此原生 OCR 任务不需要模型。

## 贡献

[贡献指南](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.md)、[Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57)。

## 问题反馈

模板问题：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。SDK/服务器：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板代码和原创生成样例图片采用仓库 [Apache-2.0](../LICENSE)。官方 [Tesseract 5.5.0](https://github.com/tesseract-ocr/tesseract/tree/5.5.0) 采用 Apache-2.0，镜像保留 Debian 版权/归属文件和 Pillow 安装包许可证。不重新分发字体文件；样例只是原创文字的栅格图。各依赖保留其原有许可证。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
