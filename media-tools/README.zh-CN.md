# Media tools

FFmpeg 离线 CPU 媒体转码。[English](README.md)。

## 做什么

检查上传的音视频文件，生成有大小和时长限制的 MP4/H.264、WAV 或 FLAC 产物。命令实际执行固定版本的 `ffmpeg` 和 `ffprobe`，无需模型、GPU、外部账号或显示器。产物保留在工作目录，直到调用方删除或销毁沙箱。

## 技术栈

- 阿里云基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，通常替换为 `cn-hangzhou` / `v0.0.49`。
- Debian 13 [FFmpeg `7:7.1.5-0+deb13u1`](https://packages.debian.org/trixie/ffmpeg)，FFmpeg ABI 库也固定相同版本；其他系统依赖由 Debian 仓库解析。
- 注入的 server wheel，或 python-sdk 源码 pin `fd72d3210b85079d93dcf08e19bfded73643162b`。
- 非 root 用户 `user`，可写目录 `/home/user/app`，generation 2 标准 serve/healthcheck，端口 9000。

## 解决的问题

为媒体工作流提供可预测的 CPU 转码和独立产物核验。1.1版在三个既有 preset 之外增加原生 JSON 参数列表，两种入口都限定为下述离线 CPU 子集。MP4 保留第一路视频及可选第一路音频，按比例缩放至宽 640、偶数高度，生成 24 fps H.264/yuv420p 与双声道 48 kHz AAC。WAV/FLAC 保留第一路音频，转换为单声道 16 kHz PCM16/无损 FLAC。

## 快速开始（CLI）

示例使用当前极速版 CLI：`abx create <template-id> --detach` 输出沙箱 ID，`abx kill <sandbox-id>` 清理沙箱；命名命令使用 `abx run`。完整对照见[使用指南](../docs/using-templates.zh-CN.md#客户端入口兼容性)。

```bash
abx template deploy ./media-tools -y --generation 2
abx create <template-id> --detach
abx run <sandbox-id> media_smoke
abx run <sandbox-id> transcode --arg input_path=uploaded.mkv --arg output_name=preview.mp4
abx run <sandbox-id> transcode_args --json-args '{"args":["-i","uploaded.mkv","-vn","-c:a","flac","audio.flac"],"max_seconds":5}'
abx kill <sandbox-id>
abx template delete <template-id> -y
```

自定义转码前，通过 files API 把 `uploaded.mkv` 上传到 `/home/user/app`。`media_smoke` 无需上传：自行生成音频、实际转码、独立解码逐样本比对，再清理自有文件。模板已声明 generation/start/readiness。

## 快速开始（Python SDK）

按[客户端安装说明](../docs/python-client-installation.md)安装 `agent-sandbox-client`，导入名为 `agent_sandbox`。

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("media_smoke"))
        # 先把输入上传到 /home/user/app：
        result = await sb.run("transcode", input_path="uploaded.mkv", output_name="preview.mp4", timeout=150)
        print(result["output_path"], result["sha256"])
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` 调用命名命令；`sb.commands.run` 调用共享 server shell。通过 files API 下载产物。上例 `timeout` 是客户端 HTTP 等待时限；服务端操作时限使用 `command_timeout`。

## 快速开始（HTTP POST）

使用沙箱 9000 端口 URL，同时携带提供方网关要求的访问头。运行中的 server 设置了 `ABX_SERVER_TOKEN` 时，需要下面的 bearer token。

```bash
curl --fail-with-body --max-time 150 --request POST "$ABX_SERVER_URL/commands/transcode" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"input_path":"uploaded.mkv","output_name":"preview.mp4","preset":"mp4","max_seconds":5,"command_timeout":60}'
```

JSON 对象直接包含参数。HTTP 200 返回 `{"result":{"output_path":"/home/user/app/preview.mp4","bytes":12345,"sha256":"<64位十六进制>","duration_s":5.0,"format":"mov,mp4,m4a,3gp,3g2,mj2","streams":[...]}}`，数值取决于输入。缺失或错误类型参数返回 400；鉴权失败 401；未知命令 404；路径、内容、限制检查或工具执行失败返回 500，含 `error` 和 `type`。结果缓冲后返回。HTTP 超时或断连不保证取消服务端操作。

## 命令参考

| 命令 | 参数 | 返回 | 说明 |
|---|---|---|---|
| `media_version` | 无 | 字符串 | 检查 FFmpeg 和 ffprobe 的精确版本。 |
| `media_setup_check` | 无 | 对象 | 固定工具是否可用；不处理媒体、不联网。 |
| `media_probe` | 必填字符串 `input_path`；整数 `command_timeout` 默认 30，范围 1–120 | 对象 | 时长、格式、流信息及输入字节数。 |
| `transcode` | 必填字符串 `input_path`、`output_name`；`preset` 为默认 `mp4`、`wav` 或 `flac`；整数 `max_seconds` 默认 5，范围 1–30；整数 `command_timeout` 默认 60，范围 1–120 | 对象 | 产物路径、字节数、SHA256、时长、格式和流。 |
| `transcode_args` | 必填 `args`：原生字符串数组；`max_seconds`：整数5（1–30）；`command_timeout`：整数60（1–120） | 对象 | 真实 `stdout`、`stderr`、`exit_code`；成功时增加独立核对的产物元数据。 |
| `media_args_smoke` | 无 | 字符串 | 原生 argv 转码、完整 PCM 比对及自有文件清理。 |
| `media_smoke` | 无 | 字符串 | 自有合成 WAV → 真实 FLAC → 独立 PCM 解码逐样本比对，并清理。 |
| `media_video_smoke` | 无 | 字符串 | 自有合成 MPEG4 → 真实 H.264 MP4，独立检查尺寸/时长后清理。 |

输入必须是 `WORKSPACE` 内相对路径指向的普通文件，最大 64 MiB；拒绝父目录穿越、绝对路径、各层软链接、设备和 FIFO。通过目录描述符读取后生成私有快照。仅允许 MOV/MP4、Matroska/WebM、WAV、FLAC、MP3、Ogg、AVI 解复用器和 `file` 协议。输入需要 1–8 路音视频流、有限且不超过 600 秒的时长，视频不超过 4096×2160，音频不超过 8 声道/192 kHz。拒绝播放列表、字幕、附件和网络输入。

输出为普通文件名：ASCII 字母/数字开头，后接最多 119 个字母/数字/下划线/点/连字符，再接 preset 扩展名。不会覆盖现有文件或软链接。删除输出元数据和章节；产物小于 64 MiB。一次运行一个 probe/转码，并发请求立即失败。子进程只接收 HOME/PATH/可选库路径和固定语言/线程变量；地址空间限制 1 GiB，CPU 软/硬限制 120/121 秒，单文件限制 64 MiB，禁止 core dump。每路诊断最多 1 MiB，错误中不回显原始诊断。输入检查、转码与输出检查共享一个操作 deadline，随后完成清理。

## 配置

| 名称 | 必需 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 否 | 空 | server 进程启动时鉴权。 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地直接启动的端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在且属于运行用户的输入/输出目录。 |

进程配置需在启动前生效。预热的命令 server 可能先于 create-time shell 环境启动；参见[客户端配置说明](../docs/python-client-installation.md)。命名命令路径限制不会限制其他已授权 shell/files API。

## 资源

| 资源 | 数值 |
|---|---|
| CPU | 2 vCPU，编解码/滤镜各限制两线程 |
| 内存 | 沙箱 2048 MB，原生工具地址空间上限 1 GiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs，输入及每个产物限 64 MiB；调用方删除保留产物 |


### 原生 argv 接口

调研要求的 `args: list[str]` 通过新增 `transcode_args` 提供，保留已发布的
`transcode(input_path, output_name, preset, ...)` 兼容接口。
列表以 `-i`、一个相对工作区输入开头，随后为输出选项，以单个普通
`.mp4`、`.wav` 或 `.flac` 文件名结尾。共3–64个非空字符串、最多8192个 UTF-8
字节；含空格的元素保留为一个参数。JSON 编码字符串不是数组，执行前返回400。

允许选项：`-an`、`-vn`、`-c:v libx264`、`-c:a aac|pcm_s16le|flac`、
`-preset ultrafast|superfast|veryfast|faster|fast|medium`、`-pix_fmt yuv420p`、
`-map 0:v:0|0:v:0?|0:a:0|0:a:0?`、`-movflags +faststart`、`-t`（正数且不超过
`max_seconds`）、`-ss`（正数≤600）、`-r`（正数≤60）、`-ac`（整数1–2）、
`-ar`（整数1–48000）、`-vf scale=W:H`（宽1–1920，高1–1080或原生比例值 `-2`）。
成对选项必须带值。拒绝未列出的参数、多输入、任意滤镜、协议及输出路径；
最终线程、时长、大小、禁止覆盖与元数据限制由 wrapper 强制追加。

```python
result = await sb.run("transcode_args", args=["-i", "literal file.wav", "-c:a", "flac", "result.flac"])
assert result["exit_code"] == 0
```

```json
{"args":["-i","uploaded.wav","-c:a","flac","result.flac"],"max_seconds":5}
```

将此对象直接 POST 到 `/commands/transcode_args`。已接受的 FFmpeg 原生失败返回
HTTP200和实际非零 `exit_code`、有限的 `stdout`/`stderr`，不发布部分产物。
路径、探测、时间和输出限制失败仍返回500；错误参数类型和缺少 args 返回400。
旧 preset 接口保留原有异常行为。成功时同时返回实际进程结果和产物字段，
下载后由调用者清理产物。无模型自检命令为 `media_args_smoke`。

`server-sdk.commit` 显式选择支持数组的不可变服务器源码，必须与 Dockerfile
fallback 一致；镜像 CI、归档及运行证明均核对同一 commit。没有该文件的其他
模板保留历史共同注入 pin。使用数组前重建1.0镜像；旧服务器会将注解转成字符串。

## 已验证

参见[测试结果与范围](../docs/using-templates.zh-CN.md#验收与厂商)。下面的日期记录标明实测输入与入口。

## 1.0历史验证

2026-10-20 同版本追加真实 step 复验，实际使用 Python `Sandbox.create`，通过 CLI/SDK 命名 smoke，并独立确认 sandbox/template 清理：[SDK 创建 step 回执](evidence/express-2026-10-20.json)。此记录单独证明创建入口；下方完整工作流回执保留原有范围。


| 提供方 | 已执行范围 | 证据 |
| --- | --- | --- |
| alicloud-express | steps 构建、官方 READY、CLI 与 SDK smoke、独立资源清理回查 | [2026-10-19](evidence/express-2026-10-19.json) |
| alicloud-express | 完整媒体 HTTP21 项断言，真实 steps READY/CLI/SDK 及独立清理确认 | [完整检查](evidence/full-http-steps-2026-10-19T184323Z.json)、[构建证据](evidence/steps-full-http-2026-10-19T184323Z.json) |

该记录采用已固定的 e2cb27e 服务端来源覆盖，与现有镜像 CI 注入版本一致；精确版本、输入哈希和构建模式在回执中。这里只更新验证元数据，模板仍为 experimental。Dockerfile L1、完整产品和真实模型验收按各自记录判断，不能从基础 smoke 推断。

## 二次开发

阅读[设计](../docs/design/media-tools.md)，运行 `python3 scripts/check_template.py media-tools`、`python3 -m pytest -q media-tools/test_commands.py media-tools/test_http.py` 及仓库本地 E2E runner。codec 回归实际运行固定 Debian 工具，不模拟原生进程。HTTP 验收设置 `E2E_REQUIRE_MEDIA=1`，缺少固定工具就失败；未要求时显式 SKIP，不算媒体功能通过。验收上传随机 PCM、下载产物核对完整哈希，再独立解析 WAV 往返产物并逐样本比对，最后删除自有文件。

Linux runner 使用 `waitid(WNOWAIT)` 固定 owned group 身份，先终止进程组再 reap leader，覆盖成功、非零退出和重定向后代进程。主动 `setsid` 脱离及 server 被 SIGKILL 不在该清理保证内；沙箱销毁是最终隔离边界。

### Agent Sandbox step 构建

在仓库 checkout 执行 `python scripts/run_steps_e2e.py media-tools`，通过真实极速版 step 构建并验收此模板。前置配置、源码来源和清理见 [step 指南](../docs/platform-steps.zh-CN.md)。无模型 smoke 不能代替 L3。

## 贡献

[CONTRIBUTING.md](../CONTRIBUTING.md)、[模板规范](../docs/template-spec.md)、[Issue 58](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/58)。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。Server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。部署 CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 Python 代码：[Apache-2.0](../LICENSE)。FFmpeg 与 libx264 保留各自许可证及已安装的 Debian copyright 文件。Debian FFmpeg 启用了包括 libx264 的 GPL 组件，不能改标 Apache-2.0。参见[上游许可证](https://ffmpeg.org/legal.html)、[精确 Debian 源码包](https://packages.debian.org/source/trixie/ffmpeg)及镜像 `/usr/share/doc/ffmpeg/copyright`。smoke 音频由模板原创生成。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
