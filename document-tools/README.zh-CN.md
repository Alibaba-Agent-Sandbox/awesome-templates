# Document tools

Pandoc 离线 Markdown 文档转换。[English](README.md)。

## 做什么

把工作目录内 UTF-8 Markdown 转为真实 DOCX 或纯文本，返回路径、字节数和 SHA256，通过 files API 下载产物。无需模型、外部账号、显示器、GPU 或特权守护进程。

## 技术栈

- 阿里云基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，通常为 `cn-hangzhou` / `v0.0.49`。
- Debian 13 固定 `pandoc=3.1.11.1+ds-2`、`pandoc-data=3.1.11.1-3`，二者版本字符串不同是发行包事实；其他系统依赖由 Debian 仓库解析。
- 注入的 server wheel 或不可变 python-sdk 源码 `e2cb27e24fde0a67112f82b8d44af463445a5d1a`。
- 非 root `user`，可写 `/home/user/app`，generation 2 标准 serve/healthcheck，端口 9000。

## 解决的问题

交付 [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55) 允许先做的 Pandoc 文本切片：标题、强调、列表及 Unicode 文本转为可独立核验的文档。当前仅接收 GFM Markdown，输出 DOCX/TXT。HTML 输入、图片、PDF、幻灯片和 LibreOffice 尚未实现，不能由模板名称推断为已交付。

## 快速开始（CLI）

```bash
abx template deploy ./document-tools -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> document_smoke
abx run <sandbox-id> convert --arg input_path=report.md --arg output_name=report.docx
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

先把 `report.md` 上传到 `/home/user/app`。`document_smoke` 自行生成 Markdown，实际转码并独立检查 DOCX XML/TXT，最后删除自有文件。普通转换产物由调用方删除，或随沙箱销毁。

## 快速开始（Python SDK）

按[客户端安装说明](../docs/python-client-installation.md)安装 `agent-sandbox-client`，导入 `agent_sandbox`。

```python
import asyncio
from agent_sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("document_smoke"))
        # 先把 report.md 上传到 /home/user/app：
        result = await sb.run("convert", input_path="report.md", output_name="report.docx", timeout=90)
        print(result["output_path"], result["sha256"])
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 调用命名命令；`sb.commands.run` 调用共享 server shell；files API 负责文件传输。上例 `timeout` 为 HTTP 超时，命名命令的服务端 deadline 参数为 `command_timeout`。

## 快速开始（HTTP POST）

使用沙箱 9000 端口 URL，并携带提供方网关要求的访问头。运行中的 server 配置了 `ABX_SERVER_TOKEN` 时另需 bearer token。

```bash
curl --fail-with-body --max-time 90 --request POST "$ABX_SERVER_URL/commands/convert" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"input_path":"report.md","output_name":"report.docx","output_format":"docx","command_timeout":30}'
```

JSON 对象直接包含参数。HTTP 200 返回 `{"result":{"output_path":"/home/user/app/report.docx","output_format":"docx","bytes":12345,"sha256":"<64位十六进制>"}}`，大小和哈希取决于内容。缺失/错误类型参数为 400；鉴权失败 401；未知命令 404；路径、内容、限制或执行错误为 500，含 `error` 和 `type`。结果缓冲返回；HTTP 超时/断连不保证服务端取消。

## 命令参考

| 命令 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `document_version` | 无 | 字符串 | 实际固定版本 `pandoc 3.1.11.1`。 |
| `document_setup_check` | 无 | 对象 | 固定程序可用性；不处理输入。 |
| `convert` | 必填字符串 `input_path`、`output_name`；`output_format` 默认 `docx`，或 `txt`；整数 `command_timeout` 默认 30，范围 1–60 | 对象 | 新产物路径、格式、字节数和 SHA256。 |
| `document_smoke` | 无 | 字符串 | 原创 Markdown → 实际 DOCX/TXT，独立检查内容并清理。 |

输入为 `WORKSPACE` 内相对路径的非空 UTF-8 普通文件，最大 1 MiB；拒绝父目录穿越、绝对路径、各层软链接、设备和 FIFO，描述符读取后生成私有快照。输出必须为普通 ASCII 文件名：字母/数字开头，后接最多 119 个字母/数字/下划线/点/连字符，再接所选扩展名；不覆盖现有文件或软链接。

第一阶段以固定 Pandoc `--sandbox` 将 GFM 读取为有界 JSON AST，拒绝 Image/Raw 节点、非 web/mail/fragment 链接、过多节点或嵌套，并清空 metadata。TXT writer 也运行在 sandbox 模式。Debian Pandoc 的数据文件未嵌入二进制，DOCX writer 使用 `--sandbox` 会因内部模板不可读而失败；因此仅把经过校验、无图片/Raw 的 AST 交给固定 DOCX writer，允许它读取已安装的包数据。不接受 filter、include 参数、自定义模板、PDF engine 或任意 argv。这是明确的应用边界，不等于对整个 writer 建立操作系统禁网沙箱。

一次仅运行一个转换。每个原生进程有 1 GiB 地址空间、256 MiB Haskell heap、两条 runtime capabilities、30/31 秒 CPU 软/硬上限、8 MiB 单文件上限、禁止 core dump，并共享操作 wall deadline。只转发 HOME/PATH/可选库路径、固定语言/线程/allocator 设置及运维指定的包数据目录。每路诊断/AST 输出最多 1 MiB，错误不回显原始诊断。DOCX 发布前检查 ZIP 条目数、展开总量及文档 XML，再进行无覆盖原子发布。

## 配置

| 名称 | 必需 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 空 | server 进程启动前配置鉴权。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地直接启动端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在且属于运行用户的输入/输出目录。 |
| `DOCUMENT_PANDOC_BINARY` | 否 | `/usr/bin/pandoc` | 运维指定绝对程序路径，仍检查版本。 |
| `DOCUMENT_PANDOC_DATA_DIR` | 否 | `/usr/share/pandoc` | 运维指定已安装包数据根目录，使用 Debian `pandoc_datadir` 转发。 |

预热 server 早于后续 shell 环境更改读取进程配置。命名命令的路径限制不限制已授权共享 shell/files API。后两个参数用于原生诊断，不是命名命令参数。

## 资源

| 资源 | 数值 |
|---|---|
| CPU | 2 vCPU，两个 Haskell runtime capabilities |
| 内存 | 沙箱 2048 MB，原生地址空间 1 GiB，heap 256 MiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs；输入 1 MiB、产物 8 MiB；调用方删除保留产物 |

## 已验证

尚未记录任何通过的提供方测试。

记录的运行时代码已实际通过镜像 L1 和专门的原生/SDK/HTTP CI，见 [CI 确认](../.agents/evidence/verify/2026-10-18-document-tools-ci-confirmation.md)。本地准备及首次远端失败保留在[原始记录](../.agents/evidence/verify/2026-10-18-document-tools-runtime.md)。canonical L2 尚未运行；保持 experimental 和空 `tested_on`。

## 二次开发

阅读[设计](../docs/design/document-tools.md)，运行 `python3 scripts/check_template.py document-tools`、`python3 -m pytest -q document-tools/test_commands.py document-tools/test_http.py` 及本地 E2E runner。测试需要实际固定 Debian 程序/数据。`E2E_REQUIRE_DOCUMENT=1` 使缺少原生依赖时失败，不能 SKIP。外部控制器上传包含随机 nonce/中文的 Markdown，下载完整产物核对哈希，独立解析 DOCX 标题、加粗及文本和 TXT，再清理。

原生清理通过 `waitid(WNOWAIT)` 保持 leader 未 reap，先终止 owned 进程组，覆盖成功、非零退出及重定向后代。主动 `setsid` 脱离和 server 被 SIGKILL 不在此保证内；销毁沙箱是最终隔离边界。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.md)、[Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55)。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。Server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。部署 CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 Python 代码：[Apache-2.0](../LICENSE)。[Pandoc](https://pandoc.org/) 保留 GPL-2.0-or-later 及 Debian copyright 文件，不改标为 Apache-2.0。精确发行源码见 [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) 和 [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data)。smoke Markdown 为原创生成文本。
