# OCR

[English](README.md)

## 做什么

`ocr(image_path)` 处理工作区中的一张 PNG/JPEG，返回文字、尺寸、词数，以及私有 TXT/TSV 文件路径和 SHA256。实际运行 OCR 引擎，无需模型、API key 或网络。空白图片可以正常返回零个词。当前只安装英文识别数据；中文文档不代表支持中文 OCR。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

Alibaba 基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，默认区域/版本为 `cn-hangzhou` / `v0.0.49`。Debian 13 的 Tesseract/libtesseract 固定为 `5.5.0-1+b1`，英文和方向数据为 `1:4.1.0-2`，Leptonica 为 `1.84.1-4`；其他系统依赖由发行版仓库解析。Pillow `11.3.0` 先按提交的 wheel SHA256 白名单下载，再以 --no-index/--no-deps 离线安装，禁止源码安装。以非 root 的 `user` 运行，工作区 `/home/user/app`，端口 9000；保留原 HOME。

## 解决的问题

无需 GPU 或外部 OCR 服务，将英文图片转为可检索文字和词级坐标。本接口每次处理一张图片，使用固定分段模式；不支持 PDF、压缩包、批量、自动下载语言或承诺手写识别。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//ocr --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" ocr --json-args '{"image_path":"fixtures/sample.png"}'
```

识别内置样例，`text` 包含 SANDBOX、OCR 和 314159，并返回可导出的 TXT/TSV 路径及哈希。

处理自己的图片时，先 `abx upload "$SANDBOX_ID" ./scan.png /home/user/app/scan.png`，再把 `image_path` 改为 `scan.png`。仅内置英文 `eng` 识别，不是多模态模型，也不声称支持中文 OCR。

`--sandbox-timeout 1800` 将实例寿命设为 30 分钟，覆盖示例任务和导出所需时间；`ABX_HTTP_TIMEOUT` 只控制本机客户端等待，不延长实例寿命。完成后仍应主动释放实例。

OpenSandbox 用户将 `ABX_PROVIDER` 改为 `opensandbox`，并按[提供方指南](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md)配置；后续 CLI 和 Python 必须继续选择同一个平台。

## 快速开始（Python SDK）

先在虚拟环境执行 `python -m pip install agent-sandbox-client==0.4.0a6`。

在完成上述 CLI 启动、设置 `SANDBOX_ID` 后，将以下保存为 `use_template.py`，执行 `python3 use_template.py`。它连接同一实例，不另建沙箱。对于需要输入的示例，先在本机准备上面的文件。

```python
import asyncio
import os
from pathlib import Path
from agent_sandbox import ProviderSandbox

async def main():
    sb = await ProviderSandbox.connect(
        os.environ["SANDBOX_ID"], provider=os.environ["ABX_PROVIDER"]
    )
    try:
        client = await sb.application_client(
            9000, token=os.environ["ABX_SERVER_TOKEN"], timeout=450
        )
        try:
            result = await client.commands.run('ocr', image_path='fixtures/sample.png')
            print(result)
            Path('recognized.txt').write_bytes(await sb.files.read_bytes(result['text_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/ocr`

```json
{
  "image_path": "fixtures/sample.png"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

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
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `ABX_SERVER_PORT` | 否 | `9000` | 直接本地启动端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在、运行用户拥有的输入输出根目录。 |
| `OCR_TESSERACT_BINARY` | 否 | `/usr/bin/tesseract` | 运维配置的绝对程序路径，仍检查固定版本。 |
| `OCR_TESSDATA_DIR` | 否 | `/usr/share/tesseract-ocr/5/tessdata` | 运维配置的绝对目录，包含英文 traineddata。 |

后两项仅用于本机诊断，不是命令参数。子进程只接收原 HOME/PATH、可选动态库路径和固定 locale/线程设置，不转发云端或模型凭据。通用 shell/files API 和运维配置需要独立控制访问。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 text_path
abx download "$SANDBOX_ID" '<returned-path>' ./recognized.txt
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

| 资源 | 值 |
|---|---|
| CPU | 1 vCPU；引擎为 OpenMP 单线程 |
| 内存 | 沙箱 1024 MB；引擎地址空间上限 512 MiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs；调用者清理保留的结果目录 |

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/ocr.md)。

## 问题反馈

模板问题：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。SDK/服务器：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。CLI 部署：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板代码和原创生成样例图片采用仓库 [Apache-2.0](../LICENSE)。官方 [Tesseract 5.5.0](https://github.com/tesseract-ocr/tesseract/tree/5.5.0) 采用 Apache-2.0，镜像保留 Debian 版权/归属文件和 Pillow 安装包许可证。不重新分发字体文件；样例只是原创文字的栅格图。各依赖保留其原有许可证。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
