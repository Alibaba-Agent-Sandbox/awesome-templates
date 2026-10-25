# Media tools

Offline CPU media conversion with FFmpeg. [中文说明](README.zh-CN.md).

## What it does

Inspect uploaded audio/video files and create bounded MP4/H.264, WAV or FLAC artifacts. Commands execute the actual pinned `ffmpeg` and `ffprobe` programs. No model, GPU, external account or display is required. Outputs remain in the workspace until callers remove them or destroy the sandbox.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a2`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Debian 13 [FFmpeg `7:7.1.5-0+deb13u1`](https://packages.debian.org/trixie/ffmpeg), including the same exact version of its FFmpeg ABI libraries; other operating-system dependencies resolve from Debian repositories.
- Injected server wheel or python-sdk source pin `fd72d3210b85079d93dcf08e19bfded73643162b`.
- Non-root `user`; writable `/home/user/app`; generation 2 `agent-sandbox-server serve` / `healthcheck`, port 9000.

## Problem solved

Give media workflows a small, predictable CPU conversion interface with independent artifact checks. Version1.1 adds a native JSON argv list alongside the existing three presets. Both interfaces restrict operations to the documented offline CPU subset. MP4 keeps the first video and optional first audio stream, scales to width 640 with an even proportional height, and produces 24 fps H.264/yuv420p plus stereo 48 kHz AAC. WAV and FLAC keep the first audio stream as mono 16 kHz PCM16 or lossless FLAC.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./media-tools --yes
abx run <sandbox-id> media_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('media_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/media_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "FFmpeg 7.1.5-0+deb13u1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Direct local server startup port. |
| `WORKSPACE` | no | `/home/user/app` | Existing input/output directory owned by the runtime user. |

Set server process configuration before startup. A prewarmed command server may already be running before create-time shell environment is applied; see [the process-start configuration guide](../docs/python-client-installation.md). The named-command path policy does not constrain other authenticated shell/files APIs.

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU, two codec/filter threads |
| Memory | 2048 MB sandbox; 1 GiB native address-space limit |
| Port | 9000 |
| Disk | Platform rootfs; 64 MiB input and per-output limits; remove retained artifacts |


### Native argv interface

Use `transcode_args` for the survey's `args: list[str]` API while retaining the
published `transcode(input_path, output_name, preset, ...)` contract.
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

Using the `client` bound in the Python quick start above:

```python
result = await client.commands.run("transcode_args", args=["-i", "literal file.wav", "-c:a", "flac", "result.flac"])
assert result["exit_code"] == 0
```

```json
{"args":["-i","uploaded.wav","-c:a","flac","result.flac"],"max_seconds":5}
```

POST that direct object to `/commands/transcode_args`. Accepted FFmpeg failures
return200 with its actual nonzero `exit_code`, bounded `stdout` and `stderr`,
and no published partial artifact. Guard, probe, timeout and output-limit
failures remain500; invalid argument types/missing args return400. Preset
conversion keeps its existing failure behavior. Successful argv calls return
artifact fields alongside actual native process results. Remove outputs after
download. The model-free native smoke is `media_args_smoke`.

The published server package preserves native string-array arguments. Rebuild the image after changing its declared server dependency.

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical1.0 verification

Additional exact-version real steps passed on2026-10-20 using actual Python `Sandbox.create`, CLI/SDK named smoke and independently confirmed sandbox/template cleanup: [SDK-created step receipt](evidence/express-2026-10-20.json). This separately establishes the creation route; the complete workflow receipts below keep their original scope.


| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |
| alicloud-express | complete media HTTP21 assertions, actual steps READY/CLI/SDK and independent cleanup | [full run](evidence/full-http-steps-2026-10-19T184323Z.json), [provenance](evidence/steps-full-http-2026-10-19T184323Z.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

## Secondary development

Read [the design](../docs/design/media-tools.md), run `python3 scripts/check_template.py media-tools`, `python3 -m pytest -q media-tools/test_commands.py media-tools/test_http.py`, and the repository local E2E runner. The codec regressions require the actual pinned Debian tools and do not mock native execution. `E2E_REQUIRE_MEDIA=1` makes the HTTP suite fail if the pinned engine is unavailable; otherwise absence is explicitly SKIP and does not prove media functionality. It uploads random PCM, downloads converted artifacts, checks full hashes, independently parses the WAV roundtrip and compares every sample, then deletes its own files.

The Linux process runner uses `waitid(WNOWAIT)` to keep its owned group identity until group kill and leader reap, including successful and nonzero leaders with redirected descendants. A deliberately detached `setsid` process or server SIGKILL is outside this cleanup guarantee; destroying the sandbox is the final isolation boundary.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py media-tools` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [template specification](../docs/template-spec.md), [Issue 58](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/58).

## Issues

Template integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template Python code: [Apache-2.0](../LICENSE). FFmpeg and libx264 keep their own licenses and installed Debian copyright files. The Debian FFmpeg build enables GPL components, including libx264; it is not relabeled Apache-2.0. See [upstream license information](https://ffmpeg.org/legal.html), the [exact Debian source package](https://packages.debian.org/source/trixie/ffmpeg), and `/usr/share/doc/ffmpeg/copyright` in the image. Synthetic smoke audio is generated by this template.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
