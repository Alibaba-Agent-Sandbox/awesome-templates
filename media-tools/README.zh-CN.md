# Media tools

[English](README.md)

## 做什么

检查上传的音视频文件，生成有大小和时长限制的 MP4/H.264、WAV 或 FLAC 产物。命令实际执行固定版本的 `ffmpeg` 和 `ffprobe`，无需模型、GPU、外部账号或显示器。产物保留在工作目录，直到调用方删除或销毁沙箱。

## 技术栈

沙箱服务固定使用已发布的 `agent-sandbox-server==0.4.0a6`，由 Dockerfile 直接安装。

- 阿里云基础镜像 `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`，通常替换为 `cn-hangzhou` / `v0.0.49`。
- Debian 13 [FFmpeg `7:7.1.5-0+deb13u1`](https://packages.debian.org/trixie/ffmpeg)，FFmpeg ABI 库也固定相同版本；其他系统依赖由 Debian 仓库解析。
- 非 root 用户 `user`，可写目录 `/home/user/app`，generation 2 标准 serve/healthcheck，端口 9000。

## 解决的问题

为媒体工作流提供可预测的 CPU 转码和独立产物核验。1.1版在三个既有 preset 之外增加原生 JSON 参数列表，两种入口都限定为下述离线 CPU 子集。MP4 保留第一路视频及可选第一路音频，按比例缩放至宽 640、偶数高度，生成 24 fps H.264/yuv420p 与双声道 48 kHz AAC。WAV/FLAC 保留第一路音频，转换为单声道 16 kHz PCM16/无损 FLAC。

## 快速开始（CLI）

CLI、SDK、HTTP 是调用同一个应用的三种选法，任选一种完成任务。示例可能写入文件、创建项目或启动服务；不要在未清理前对同一实例重复执行整段示例。

先按[使用指南](../docs/using-templates.zh-CN.md#安装)安装 CLI/Python SDK，并完成所选平台配置。平台 API Key 用于创建沙箱，`ABX_SERVER_TOKEN` 是独立的模板应用访问口令。以下命令在自己的终端执行，不需要克隆本仓库。

本模板的这些命令不需要模型、模型 endpoint 或模型 API Key。

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//media-tools --sandbox-timeout 1800 --yes
# 将启动输出中的沙箱 ID 填到这里
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

在本机准备输入文件后上传：

`sample.wav` 使用自己的短音频，或在本机用 Python 标准库生成一秒静音：

```python
import wave
with wave.open("sample.wav", "wb") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(16000)
    f.writeframes(b"\x00\x00" * 16000)
```

```bash
abx upload "$SANDBOX_ID" ./sample.wav /home/user/app/sample.wav
```

```bash
abx run "$SANDBOX_ID" transcode --json-args '{"input_path":"sample.wav","output_name":"sample.flac","preset":"flac","max_seconds":5,"command_timeout":60}'
```

返回转码后 FLAC 的 `output_path`、时长、流信息、`bytes` 和 `sha256`。

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
            await sb.files.write('/home/user/app/sample.wav', Path('sample.wav').read_bytes())
            result = await client.commands.run('transcode', input_path='sample.wav', output_name='sample.flac', preset='flac', max_seconds=5, command_timeout=60)
            print(result)
            Path('sample.flac').write_bytes(await sb.files.read_bytes(result['output_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

SDK 返回命令的原始结果；HTTP 的 `result` 外层由客户端解包。关闭连接不会删除沙箱。

## 快速开始（HTTP POST）

按[HTTP 调用示例](../docs/using-templates.zh-CN.md#clisdk-与-http)解析同一实例的 9000 端口，保留网关头、URL 路径和查询，再添加独立应用认证。

`POST /commands/transcode`

```json
{
  "input_path": "sample.wav",
  "output_name": "sample.flac",
  "preset": "flac",
  "max_seconds": 5,
  "command_timeout": 60
}
```

请求头包括 `Content-Type: application/json` 和按共享指南设置的应用认证；请求体是参数对象本身，不套 `args`。成功响应为 `{"result": ...}`，其中结果含义同上。 HTTP 等待时间设为 450 秒；它独立于命令内部的执行时限。结果为缓冲响应，不是事件流。400 为参数错误，401 为认证失败，404 为命令不存在，500 为执行错误。

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

### 原生 argv 接口

需要显式 `args: list[str]` 参数向量而非命名预设时，使用 `transcode_args`。
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

使用已上传的 `sample.wav`：

```bash
abx run "$SANDBOX_ID" transcode_args --json-args '{"args":["-i","sample.wav","-c:a","flac","argv-result.flac"],"max_seconds":5}'
```

```json
{"args":["-i","sample.wav","-c:a","flac","argv-result.flac"],"max_seconds":5}
```

将此对象直接 POST 到 `/commands/transcode_args`。已接受的 FFmpeg 原生失败返回
HTTP200和实际非零 `exit_code`、有限的 `stdout`/`stderr`，不发布部分产物。
路径、探测、时间和输出限制失败仍返回500；错误参数类型和缺少 args 返回400。
preset 转码在 FFmpeg 失败时返回执行错误。成功时同时返回实际进程结果和产物字段，
下载后由调用者清理产物。无模型自检命令为 `media_args_smoke`。

## 配置

| 名称 | 必需 | 默认 | 用途 |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | 是 | 空 | 模板启动前必须导出独立应用令牌；与模型及网关凭据分开 |
| `ABX_SERVER_PORT` | 否 | `9000` | 本地直接启动的端口。 |
| `WORKSPACE` | 否 | `/home/user/app` | 已存在且属于运行用户的输入/输出目录。 |

进程配置需在启动前生效。预热的命令 server 可能先于 create-time shell 环境启动；参见[客户端配置说明](../docs/python-client-installation.md)。命名命令路径限制不会限制其他已授权 shell/files API。

工作目录为 `/home/user/app`。产物保存在沙箱磁盘，释放实例前导出需要保留的文件。不要删除原始模板目录；只清理自己的实例和启动回执列出的自有模板/镜像。

```bash
# 把 <returned-path> 换成结果中的 output_path
abx download "$SANDBOX_ID" '<returned-path>' ./sample.flac
abx kill "$SANDBOX_ID"
```

`abx kill` 删除沙箱，不表示复用模板和镜像也被删除；按[清理指南](../docs/using-templates.zh-CN.md#clisdk-与-http)清理启动时由你创建的资源。

## 资源

| 资源 | 数值 |
|---|---|
| CPU | 2 vCPU，编解码/滤镜各限制两线程 |
| 内存 | 沙箱 2048 MB，原生工具地址空间上限 1 GiB |
| 端口 | 9000 |
| 磁盘 | 平台 rootfs，输入及每个产物限 64 MiB；调用方删除保留产物 |


## 贡献

改进模板请阅读[贡献指南](../CONTRIBUTING.zh-CN.md)、[模板规范](../docs/template-spec.zh-CN.md)和[设计说明](../docs/design/media-tools.md)。

## 问题反馈

模板：[awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues)。Server/client：[python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues)。部署 CLI：[agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues)。

## 许可证

模板 Python 代码：[Apache-2.0](../LICENSE)。FFmpeg 与 libx264 保留各自许可证及已安装的 Debian copyright 文件。Debian FFmpeg 启用了包括 libx264 的 GPL 组件，不能改标 Apache-2.0。参见[上游许可证](https://ffmpeg.org/legal.html)、[精确 Debian 源码包](https://packages.debian.org/source/trixie/ffmpeg)及镜像 `/usr/share/doc/ffmpeg/copyright`。smoke 音频由模板原创生成。

CLI 安装、SDK 源码安装、HTTP 认证与资源所有权见[模板使用指南](../docs/using-templates.zh-CN.md)。
