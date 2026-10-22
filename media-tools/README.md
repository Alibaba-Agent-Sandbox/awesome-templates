# Media tools

Offline CPU media conversion with FFmpeg. [中文说明](README.zh-CN.md).

## What it does

Inspect uploaded audio/video files and create bounded MP4/H.264, WAV or FLAC artifacts. Commands execute the actual pinned `ffmpeg` and `ffprobe` programs. No model, GPU, external account or display is required. Outputs remain in the workspace until callers remove them or destroy the sandbox.

## Stack

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Debian 13 [FFmpeg `7:7.1.5-0+deb13u1`](https://packages.debian.org/trixie/ffmpeg), including the same exact version of its FFmpeg ABI libraries; other operating-system dependencies resolve from Debian repositories.
- Injected server wheel or python-sdk source pin `fd72d3210b85079d93dcf08e19bfded73643162b`.
- Non-root `user`; writable `/home/user/app`; generation 2 `agent-sandbox-server serve` / `healthcheck`, port 9000.

## Problem solved

Give media workflows a small, predictable CPU conversion interface with independent artifact checks. Version1.1 adds a native JSON argv list alongside the existing three presets. Both interfaces restrict operations to the documented offline CPU subset. MP4 keeps the first video and optional first audio stream, scales to width 640 with an even proportional height, and produces 24 fps H.264/yuv420p plus stereo 48 kHz AAC. WAV and FLAC keep the first audio stream as mono 16 kHz PCM16 or lossless FLAC.

## Quick start (CLI)

Check the installed entry with `abx create --help`. The complete example below uses native CLI syntax. If help lists `--detach`, use the standard Express entry: create with `abx create <template-id> --detach` and clean up with `abx kill <sandbox-id>` without `-y`; named commands through `abx run` are unchanged. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

```bash
abx template deploy ./media-tools -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> media_smoke
abx run <sandbox-id> transcode --arg input_path=uploaded.mkv --arg output_name=preview.mp4
abx run <sandbox-id> transcode_args --json-args '{"args":["-i","uploaded.mkv","-vn","-c:a","flac","audio.flac"],"max_seconds":5}'
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Upload `uploaded.mkv` into `/home/user/app` through the files API first. `media_smoke` needs no upload: it creates its own audio, converts it, independently decodes every sample, and removes its owned files. The template contains its generation/start/readiness settings.

## Quick start (Python SDK)

Install the `agent-sandbox-client` distribution using [the verified client installation instructions](../docs/python-client-installation.md). Import `agent_sandbox`.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("media_smoke"))
        # After an upload into /home/user/app:
        result = await sb.run("transcode", input_path="uploaded.mkv", output_name="preview.mp4", timeout=150)
        print(result["output_path"], result["sha256"])
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` invokes named commands; `sb.commands.run` invokes the shared server shell API. Download artifacts through the files API. `timeout` above is the client HTTP timeout; `command_timeout` below controls the server operation deadline.

## Quick start (HTTP POST)

Use the sandbox port-9000 URL. Send the provider's required gateway access header as well as any server authentication. When `ABX_SERVER_TOKEN` is configured on the running server, the bearer token below is required.

```bash
curl --fail-with-body --max-time 150 --request POST "$ABX_SERVER_URL/commands/transcode" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"input_path":"uploaded.mkv","output_name":"preview.mp4","preset":"mp4","max_seconds":5,"command_timeout":60}'
```

Arguments are the direct JSON object. HTTP 200 returns `{"result":{"output_path":"/home/user/app/preview.mp4","bytes":12345,"sha256":"<64 hex characters>","duration_s":5.0,"format":"mov,mp4,m4a,3gp,3g2,mj2","streams":[...]}}`; numeric values depend on the input. Missing or mistyped arguments return 400; failed authentication 401; unknown commands 404; rejected paths/content/limits or tool failures 500 with `error` and `type`. Results are buffered. A client timeout or disconnection does not guarantee server cancellation.

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
| `ABX_SERVER_TOKEN` | no | empty | Process-start server authentication. |
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

```python
result = await sb.run("transcode_args", args=["-i", "literal file.wav", "-c:a", "flac", "result.flac"])
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

`server-sdk.commit` explicitly opts this template into the immutable string-array
server source; it must match the Dockerfile fallback. Image CI checks out that
exact commit, and archive/proof validation checks it again. Existing templates
without that opt-in retain the historical common injected SDK pin. Rebuild a1.0
image before using native arrays; an old server can turn `list[str]` into string.

## Verified


### Current image acceptance — 2026-10-22

| Provider | Current version and scope | Evidence |
| --- | --- | --- |
| alicloud-express | 1.1.0; regular image, actual CLI/SDK, complete HTTP 28 PASS / 0 FAIL / 0 SKIP, independent sandbox/template/private-registry cleanup | [Runtime and HTTP receipt](evidence/image-http-2026-10-20T133417Z.json) |
| opensandbox | 1.1.0; original Docker backend, every CLI/SDK named smoke, complete HTTP 28 PASS / 0 FAIL / 0 SKIP, independent SDK/container/process cleanup | [Native source image receipt](evidence/opensandbox-2026-10-22T112438Z.json) |

OpenSandbox CLI smoke uses actual `abx exec` into the guest named HTTP API. Generic `run_code` remains unsupported and `template launch` capability checks still apply. Missing model/vendor-account checks remain explicit skips in the receipts and do not establish model acceptance. [Reproduction and scope](../docs/source-image-acceptance.md).

<details>
<summary>Earlier acceptance records (original dates and scope retained)</summary>

Version1.1passed actual SDK-created Express image and native step builds on2026-10-20,
CLI/SDK smoke,28full HTTP assertions, independent native CLI/SDK argv conversion,
full random PCM equality and owned artifact/process/cloud cleanup.

| Provider | Scope | Evidence |
| --- | --- | --- |
| alicloud-express | SDK-created image/CLI/SDK and independently checked registry cleanup | [image receipt](evidence/express-2026-10-20T133417Z.json), [full HTTP](evidence/image-http-2026-10-20T133417Z.json), [native argv](evidence/native-argv-image-2026-10-20T133417Z.json) |
| alicloud-express | Native steps, actual SDK creation,28HTTP assertions, native CLI/SDK argv | [step receipt](evidence/express-2026-10-20T131812Z.json), [full proof](evidence/full-http-steps-2026-10-20T131812Z.json), [native argv](evidence/native-argv-steps-2026-10-20T131812Z.json) |

These exact1.1results use runtime source64de1c909659f880f79f69db42614277bfdf1257
and pinned server fd72d3210b85079d93dcf08e19bfded73643162b. The SDK
[foundation PR78](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/78)
is merged. The template remains experimental; no model is required by this CPU interface.

</details>

## Historical1.0 verification

Additional exact-version real steps passed on2026-10-20 using actual Python `Sandbox.create`, CLI/SDK named smoke and independently confirmed sandbox/template cleanup: [SDK-created step receipt](evidence/express-2026-10-20.json). This separately establishes the creation route; the complete workflow receipts below keep their original scope.


| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |
| alicloud-express | complete media HTTP21 assertions, actual steps READY/CLI/SDK and independent cleanup | [full run](evidence/full-http-steps-2026-10-19T184323Z.json), [provenance](evidence/steps-full-http-2026-10-19T184323Z.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing run recorded for this template.

Actual image L1, 43 native/SDK regressions and 21 HTTP assertions passed on the recorded source; see [the CI confirmation](../.agents/evidence/verify/2026-10-18-media-tools-ci-confirmation.md). Failed attempts and local preparation remain in [the original evidence](../.agents/evidence/verify/2026-10-18-media-tools-runtime.md). Canonical L2 provider acceptance has not run. Catalog status is experimental and `tested_on` is empty.

</details>

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
