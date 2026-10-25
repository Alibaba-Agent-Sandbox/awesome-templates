# Document tools

Pandoc 离线 Markdown 文档转换。[English](README.md)。

## 做什么

把工作目录内 UTF-8 Markdown 转为真实 DOCX 或纯文本，返回路径、字节数和 SHA256，通过 files API 下载产物。无需模型、外部账号、显示器、GPU 或特权守护进程。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a4`，由 Dockerfile 直接安装。

- 阿里云基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，通常为 `cn-hangzhou` / `v0.0.49`。
- Debian 13 固定 `pandoc=3.1.11.1+ds-2`、`pandoc-data=3.1.11.1-3`，二者版本字符串不同是发行包事实；其他系统依赖由 Debian 仓库解析。
- 非 root `user`，可写 `/home/user/app`，generation 2 标准 serve/healthcheck，端口 9000。

## 解决的问题

交付[Issue55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55)的有界文本文档转换：Markdown/HTML标题、强调、列表和Unicode生成可独立核验的Office文档、幻灯片与PDF。1.1实现HTML/PPTX/原生Writer PDF，保留既有DOCX/TXT接口；图片、任意原生参数和交互GUI不在此配置内。

## 快速开始（CLI）

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装客户端、配置提供方及独立的 `ABX_SERVER_TOKEN`。在本仓库根目录启动应用，保留输出的沙箱 ID；以下 `<sandbox-id>` 均替换为该 ID。

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./document-tools --yes
abx run <sandbox-id> document_version --json-args '{}'
```

`template launch` 负责准备并启动该实例的应用。使用 OpenSandbox 时先将上面的值改为 `ABX_PROVIDER=opensandbox`，Python 使用 `provider="opensandbox"`。提供方配置和自有资源清理见[完整调用流程](../docs/using-templates.zh-CN.md#clisdk-与-http)。下面沿用同一个已启动实例。

## 快速开始（Python SDK）

安装 `agent-sandbox-client`，按[Python 连接示例](../docs/using-templates.zh-CN.md#clisdk-与-http)使用 `ProviderSandbox.connect` 和带独立应用令牌的 `application_client`。在该示例的 `try` 块内，将命令调用替换为：

```python
print(await client.commands.run('document_version'))
```

复用指南中的连接与关闭流程；`sb.commands.run` 执行进程，`client.commands.run` 调用本模板命名命令。业务命令、参数与限制见下方命令参考。

## 快速开始（HTTP POST）

按[HTTP 示例](../docs/using-templates.zh-CN.md#clisdk-与-http)获取端点并保留提供方网关头、路径及查询参数，配置独立应用令牌。将请求路径改为 `POST /commands/document_version`，`Content-Type: application/json`，直接发送以下参数对象：

```json
{}
```

该检查的预期响应：

```json
{"result": "pandoc 3.1.11.1"}
```

`result` 是缓冲结果，不是事件流。缺参或类型错误为 400，认证失败为 401，未知命令为 404，执行错误为 500。请求等待时间与命令执行期限分别设置；客户端超时不保证任务取消。

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

## 资源

| 资源 | 数值 |
|---|---|
| CPU | 2 vCPU，两个 Haskell runtime capabilities |
| 内存 |沙箱4096MB；Pandoc地址空间1GiB/堆256MiB；Office地址空间2GiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs；输入 1 MiB、产物 8 MiB；调用方删除保留产物 |

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 1.0历史验证


| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |

该历史记录采用 e2cb27e 服务端来源覆盖，与当时的镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

## 二次开发

阅读[设计](../docs/design/document-tools.md)，运行 `python3 scripts/check_template.py document-tools`、`python3 -m pytest -q document-tools/test_commands.py document-tools/test_http.py` 及本地 E2E runner。测试需要实际固定 Debian 程序/数据。`E2E_REQUIRE_DOCUMENT=1` 使缺少原生依赖时失败，不能 SKIP。外部控制器上传包含随机 nonce/中文的 Markdown，下载完整产物核对哈希，独立解析 DOCX 标题、加粗及文本和 TXT，再清理。

原生清理通过 `waitid(WNOWAIT)` 保持 leader 未 reap，先终止 owned 进程组，覆盖成功、非零退出及重定向后代。主动 `setsid` 脱离和 server 被 SIGKILL 不在此保证内；销毁沙箱是最终隔离边界。

运行时工作目录的文件系统必须支持硬链接，才能原子且不覆盖地发布产物。部分托管源码挂载拒绝该调用；可在普通可写 Linux 文件系统中运行字节一致的本地测试副本，或在进程启动前设置合适工作目录。硬链接失败会拒绝转换，不退回覆盖已有文件的实现。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py document-tools`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.md)、[Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55)。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。Server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。部署 CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

LibreOffice 遵循 [MPL-2.0 及所含组件许可](https://www.libreoffice.org/licenses/)。保留[准确 Debian 源码入口](https://packages.debian.org/source/trixie/libreoffice)及安装包中的版权文件；字体的版权与许可文件也保留。


模板 Python 代码：[Apache-2.0](../LICENSE)。[Pandoc](https://pandoc.org/) 保留 GPL-2.0-or-later 及 Debian copyright 文件，不改标为 Apache-2.0。精确发行源码见 [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) 和 [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data)。smoke Markdown 为原创生成文本。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
