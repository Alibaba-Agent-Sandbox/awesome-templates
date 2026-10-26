# Document tools

[English](README.md)

## 做什么

把工作目录内 UTF-8 Markdown 转为真实 DOCX 或纯文本，返回路径、字节数和 SHA256，通过 files API 下载产物。无需模型、外部账号、显示器、GPU 或特权守护进程。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- 阿里云基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，通常为 `cn-hangzhou` / `v0.0.49`。
- Debian 13 固定 `pandoc=3.1.11.1+ds-2`、`pandoc-data=3.1.11.1-3`，二者版本字符串不同是发行包事实；其他系统依赖由 Debian 仓库解析。
- 非 root `user`，可写 `/home/user/app`，generation 2 标准 serve/healthcheck，端口 9000。

## 解决的问题

交付[Issue55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55)的有界文本文档转换：Markdown/HTML标题、强调、列表和Unicode生成可独立核验的Office文档、幻灯片与PDF。1.1实现HTML/PPTX/原生Writer PDF，保留既有DOCX/TXT接口；图片、任意原生参数和交互GUI不在此配置内。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//document-tools --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

在本机准备输入文件后上传：

```bash
printf '# Quarterly report\n\nRevenue: 51.30.\n' > report.md
```

```bash
abx upload "$SANDBOX_ID" ./report.md /home/user/app/report.md
```

```bash
abx run "$SANDBOX_ID" convert --json-args '{"input_path":"report.md","output_name":"report.docx","output_format":"docx"}'
```

返回 `output_path`、`output_format: docx`、`bytes` 和 `sha256`；DOCX 会保留供下载。

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
            await sb.files.write('/home/user/app/report.md', Path('report.md').read_bytes())
            result = await client.commands.run('convert', input_path='report.md', output_name='report.docx', output_format='docx')
            print(result)
            Path('report.docx').write_bytes(await sb.files.read_bytes(result['output_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/convert`

```json
{
  "input_path": "report.md",
  "output_name": "report.docx",
  "output_format": "docx"
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

## 命令参考

| 命令 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `document_version` | 无 | 字符串 | 实际固定版本 `pandoc 3.1.11.1`。 |
| `document_setup_check` | 无 | 对象 | 固定程序可用性；不处理输入。 |
| `convert` | 必填字符串 `input_path`、`output_name`；`output_format`默认`docx`，或`txt`/`pptx`/`pdf`；`input_format`默认`markdown`，或`html`；整数`command_timeout`默认30，范围1–60 | 对象 | 新产物路径、格式、字节数和 SHA256。 |
| `document_smoke` | 无 | 字符串 | 原创 Markdown → 实际 DOCX/TXT，独立检查内容并清理。 |
| `office_version` | 无 | 字符串 | 核对准确的 Debian Writer 包和真实原生程序版本。 |
| `document_extended_smoke` | 无 | 字符串 | 实际生成 HTML/DOCX、PPTX 和无头 PDF，检查格式并清理自有文件。 |

输入为 `WORKSPACE` 内相对路径的非空 UTF-8 普通文件，最大 1 MiB；拒绝父目录穿越、绝对路径、各层软链接、设备和 FIFO，描述符读取后生成私有快照。输出必须为普通 ASCII 文件名：字母/数字开头，后接最多 119 个字母/数字/下划线/点/连字符，再接所选扩展名；不覆盖现有文件或软链接。

第一阶段以固定 Pandoc `--sandbox` 将 GFM 读取为有界 JSON AST，拒绝 Image/Raw 节点、非 web/mail/fragment 链接、过多节点或嵌套，并清空 metadata。TXT writer 也运行在 sandbox 模式。Debian Pandoc 的数据文件未嵌入二进制，DOCX writer 使用 `--sandbox` 会因内部模板不可读而失败；因此仅把经过校验、无图片/Raw 的 AST 交给固定 DOCX writer，允许它读取已安装的包数据。PDF 仅使用固定的隔离 Writer 阶段；不接受 filter、include 参数、自定义模板或任意 argv。这是明确的应用边界，不等于对整个 writer 建立操作系统禁网沙箱。

一次仅运行一个转换。Pandoc 使用 1 GiB 地址空间、256 MiB Haskell heap、两条 runtime capabilities 和 30/31 秒 CPU 软/硬上限；Writer 使用 2 GiB 地址空间及 60/61 秒 CPU 上限。两者保留 8 MiB 单文件上限、禁止 core dump，并共享操作 wall deadline。只转发 HOME/PATH/可选库路径、固定语言/线程/allocator 设置及运维指定的包数据目录；Writer 替换为自有 HOME/XDG/temp 目录。每路诊断/AST 输出最多 1 MiB，错误不回显原始诊断。OOXML 发布前检查 ZIP 条目数、展开总量及必需 XML，再进行无覆盖原子发布。

## 配置

| 名称 | 必需 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地直接启动端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在且属于运行用户的输入/输出目录。 |
| `DOCUMENT_PANDOC_BINARY` | 否 | `/usr/bin/pandoc` | 运维指定绝对程序路径，仍检查版本。 |
| `DOCUMENT_PANDOC_DATA_DIR` | 否 | `/usr/share/pandoc` | 运维指定已安装包数据根目录，使用 Debian `pandoc_datadir` 转发。 |

预热 server 早于后续 shell 环境更改读取进程配置。命名命令的路径限制不限制已授权共享 shell/files API。后两个参数用于原生诊断，不是命名命令参数。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 output_path
abx download "$SANDBOX_ID" '<returned-path>' ./report.docx
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

| 资源 | 数值 |
|---|---|
| CPU | 2 vCPU，两个 Haskell runtime capabilities |
| 内存 |沙箱4096MB；Pandoc地址空间1GiB/堆256MiB；Office地址空间2GiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs；输入 1 MiB、产物 8 MiB；调用方删除保留产物 |

## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/document-tools.md)。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。Server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。部署 CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

LibreOffice 遵循 [MPL-2.0 及所含组件许可](https://www.libreoffice.org/licenses/)。保留[准确 Debian 源码入口](https://packages.debian.org/source/trixie/libreoffice)及安装包中的版权文件；字体的版权与许可文件也保留。


模板 Python 代码：[Apache-2.0](../LICENSE)。[Pandoc](https://pandoc.org/) 保留 GPL-2.0-or-later 及 Debian copyright 文件，不改标为 Apache-2.0。精确发行源码见 [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) 和 [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data)。smoke Markdown 为原创生成文本。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
