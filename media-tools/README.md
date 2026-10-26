# Media tools

[中文](README.zh-CN.md)

## What it does

Inspect uploaded audio/video files and create bounded MP4/H.264, WAV or FLAC artifacts. Commands execute the actual pinned `ffmpeg` and `ffprobe` programs. No model, GPU, external account or display is required. Outputs remain in the workspace until callers remove them or destroy the sandbox.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Debian 13 [FFmpeg `7:7.1.5-0+deb13u1`](https://packages.debian.org/trixie/ffmpeg), including the same exact version of its FFmpeg ABI libraries; other operating-system dependencies resolve from Debian repositories.
- Non-root `user`; writable `/home/user/app`; generation 2 `agent-sandbox-server serve` / `healthcheck`, port 9000.

## Problem solved

Give media workflows a small, predictable CPU conversion interface with independent artifact checks. Version1.1 adds a native JSON argv list alongside the existing three presets. Both interfaces restrict operations to the documented offline CPU subset. MP4 keeps the first video and optional first audio stream, scales to width 640 with an even proportional height, and produces 24 fps H.264/yuv420p plus stereo 48 kHz AAC. WAV and FLAC keep the first audio stream as mono 16 kHz PCM16 or lossless FLAC.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//media-tools --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

Prepare the input locally and upload it:

Use your own short `sample.wav`, or generate one second of silence locally with the Python standard library:

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

Returns `output_path`, duration, streams, `bytes` and `sha256` for the converted FLAC.

`--sandbox-timeout 1800` gives the instance a 30-minute lifetime for the task and artifact export. `ABX_HTTP_TIMEOUT` controls local HTTP waiting and does not extend that lifetime. Delete the instance when finished.

For OpenSandbox, set `ABX_PROVIDER=opensandbox` and configure its [provider guide](https://github.com/Alibaba-Agent-Sandbox/awesome-providers/blob/main/opensandbox/docs/README.md). Keep the same provider selected for subsequent CLI and Python calls.

## Quick start (Python SDK)

In your virtual environment, run `python -m pip install agent-sandbox-client==0.4.0a6`.

After launching above and setting `SANDBOX_ID`, save this as `use_template.py` and run `python3 use_template.py`. It connects to the same instance instead of creating another sandbox. Prepare any input file locally as shown above.

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

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

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

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `media_version` | none | string | Exact installed FFmpeg and ffprobe pin. |
| `media_setup_check` | none | object | Pin availability; no media input or network. |
| `media_probe` | required `input_path`: string; `command_timeout`: integer, default 30, range 1–120 | object | Duration, format, streams and input byte count. |
| `transcode` | required `input_path`, `output_name`: strings; `preset`: `mp4` (default), `wav` or `flac`; `max_seconds`: integer, default 5, range 1–30; `command_timeout`: integer, default 60, range 1–120 | object | Artifact path, size, SHA256, duration, format and streams. |
| `transcode_args` | required `args`: native list of strings; `max_seconds`: integer5(1–30); `command_timeout`: integer60(1–120) | object | Actual `stdout`, `stderr`, `exit_code`; successful output also includes independent artifact metadata. |
| `media_args_smoke` | none | string | Actual argv conversion and full PCM equality with owned cleanup. |
| `media_smoke` | none | string | Owned synthetic WAV → actual FLAC → independent PCM decode and exact sample equality, with cleanup. |
| `media_video_smoke` | none | string | Owned synthetic MPEG4 → actual H.264 MP4 with independently checked dimensions/duration, then cleanup. |

Inputs are regular files of at most 64 MiB with relative paths beneath `WORKSPACE`; parent traversal, absolute paths, symlink components, devices and FIFOs are rejected. A descriptor-based read creates a private input snapshot. Accepted demuxers are MOV/MP4, Matroska/WebM, WAV, FLAC, MP3, Ogg and AVI, with only `file` protocol enabled. Content must have 1–8 audio/video streams, a finite duration up to 600 seconds, video up to 4096×2160, audio up to 8 channels and 192 kHz. Playlists, subtitles, attachments and network inputs are rejected.

Outputs use a plain filename beginning with an ASCII letter/digit, followed by at most 119 letters/digits/underscores/dots/hyphens, and the preset extension. Existing files and symlinks are never overwritten. Output metadata/chapters are stripped; the size must be below 64 MiB. One conversion/probe runs at a time; a concurrent request fails promptly. Native children receive only HOME/PATH/optional library path plus fixed locale/thread settings, have 1 GiB address space, CPU soft/hard limits of 120/121 seconds, 64 MiB per-file output limits and no core dumps. Diagnostics are capped at 1 MiB per stream and omitted from failure messages. The operation shares one wall deadline across probe, conversion and output probe, with cleanup afterward.

### Native argv interface

Use `transcode_args` when you need an explicit `args: list[str]` vector rather than a named preset.
The list starts with `-i`, one relative workspace input, then output options,
and ends with one plain `.mp4`, `.wav` or `.flac` filename. It contains3–64
nonempty strings and at most8192 UTF-8 bytes. Strings containing spaces stay
single arguments. A JSON-encoded string is refused with400 before execution.

Allowed output options are `-an`, `-vn`, `-c:v libx264`, `-c:a aac|pcm_s16le|flac`,
`-preset ultrafast|superfast|veryfast|faster|fast|medium`, `-pix_fmt yuv420p`,
`-map 0:v:0|0:v:0?|0:a:0|0:a:0?`, `-movflags +faststart`, `-t` (positive and
at most `max_seconds`), `-ss` (positive, at most600), `-r` (positive, at most60),
`-ac` (integer1–2), `-ar` (integer1–48000), and `-vf scale=W:H` (W1–1920;
H1–1080 or native proportional `-2`). Each paired option requires its own value.
Unlisted flags, extra inputs, arbitrary filters, protocols and output paths are
refused. Final thread/duration/size/no-overwrite/metadata limits are enforced
by the wrapper and cannot be replaced with user flags.

Using the uploaded `sample.wav`:

```bash
abx run "$SANDBOX_ID" transcode_args --json-args '{"args":["-i","sample.wav","-c:a","flac","argv-result.flac"],"max_seconds":5}'
```

```json
{"args":["-i","sample.wav","-c:a","flac","argv-result.flac"],"max_seconds":5}
```

POST that direct object to `/commands/transcode_args`. Accepted FFmpeg failures
return200 with its actual nonzero `exit_code`, bounded `stdout` and `stderr`,
and no published partial artifact. Guard, probe, timeout and output-limit
failures remain500; invalid argument types/missing args return400. Preset conversion raises an execution error on FFmpeg failure. Successful argv calls return
artifact fields alongside actual native process results. Remove outputs after
download. The model-free native smoke is `media_args_smoke`.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Direct local server startup port. |
| `WORKSPACE` | no | `/home/user/app` | Existing input/output directory owned by the runtime user. |

Set server process configuration before startup. A prewarmed command server may already be running before create-time shell environment is applied; see [the process-start configuration guide](../docs/python-client-installation.md). The named-command path policy does not constrain other authenticated shell/files APIs.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with output_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./sample.flac
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU, two codec/filter threads |
| Memory | 2048 MB sandbox; 1 GiB native address-space limit |
| Port | 9000 |
| Disk | Platform rootfs; 64 MiB input and per-output limits; remove retained artifacts |


## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/media-tools.md).

## Issues

Template integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template Python code: [Apache-2.0](../LICENSE). FFmpeg and libx264 keep their own licenses and installed Debian copyright files. The Debian FFmpeg build enables GPL components, including libx264; it is not relabeled Apache-2.0. See [upstream license information](https://ffmpeg.org/legal.html), the [exact Debian source package](https://packages.debian.org/source/trixie/ffmpeg), and `/usr/share/doc/ffmpeg/copyright` in the image. Synthetic smoke audio is generated by this template.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
