# OCR

CPU English image recognition with official Tesseract. See [中文说明](README.zh-CN.md).

## What it does

`ocr(image_path)` recognizes one workspace PNG or JPEG and returns text, image dimensions, word count, and private TXT/TSV artifact paths with SHA256 hashes. It runs the actual Tesseract engine; no model, API key or network request is needed. Blank images legitimately return no words. English is the installed recognition language; bilingual documentation does not imply Chinese recognition support.

## Stack

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`; deployment defaults are `cn-hangzhou` / `v0.0.49`.
- Debian 13 Tesseract / libtesseract `5.5.0-1+b1`, English and orientation data `1:4.1.0-2`, Leptonica `1.84.1-4`. Other OS libraries resolve through the base's Debian repositories.
- Pillow `11.3.0`, installed from the committed SHA256 wheel allowlist; source distributions are disabled.
- Server from an injected source-built wheel or python-sdk commit `e2cb27e24fde0a67112f82b8d44af463445a5d1a`.
- Non-root `user`, `/home/user/app`, generation 2 canonical server startup, port 9000. Original `HOME` is preserved.

## Problem solved

Extract searchable English text and word coordinates from an uploaded image without a GPU or remote OCR service. The first slice handles one image per request with a fixed page segmentation mode; PDF, archives, batch processing, handwritten text and additional language packs are outside this interface.

## Quick start (CLI)

```bash
abx template deploy ./ocr -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> ocr_smoke
abx run <sandbox-id> ocr --arg image_path=/home/user/app/fixtures/sample.png
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Upload custom images through the SDK files API into the workspace before calling `ocr`. Successful artifacts remain in the returned `.ocr-<random>/` directory until you remove them or destroy the sandbox. The smoke command removes only its own image and results.

## Quick start (Python SDK)

Install `agent-sandbox-client`; the import is `agent_sandbox`.

```python
import asyncio
from agent_sandbox import Sandbox

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

`sb.run` invokes a named command; `sb.commands.run` invokes the server's shell API. The template retains the shared server's shell/files/code/ports capabilities. OCR path checks constrain this named command and do not sandbox other authenticated server APIs.

## Quick start (HTTP POST)

Use the sandbox's port-9000 URL and the configured server bearer token. Allow at least 90 seconds for bounded processing and cleanup.

```bash
curl --fail-with-body --request POST --max-time 90 "$ABX_SERVER_URL/commands/ocr" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"image_path":"/home/user/app/fixtures/sample.png"}'
```

HTTP 200 wraps the result in `{"result": ...}`. Missing or mistyped arguments return 400; failed authentication returns 401. Invalid image content, rejected paths or execution failures return 500 with `error` and `type`. Results are buffered. Client disconnection does not guarantee cancellation.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `ocr_version` | none | string | Actual fixed CLI version, `tesseract 5.5.0`. |
| `ocr_setup_check` | none | object | Availability, engine/Pillow versions and `eng`; no image processing. |
| `ocr` | `image_path`: required string | object | Text, word count, normalized dimensions, language, engine version, artifact directory, TXT/TSV paths and hashes. |
| `ocr_smoke` | none | string | Real packaged pixels → text/TSV, independently checked and cleaned. |

Input may be relative to `WORKSPACE` or an absolute path beneath it. No `..`, symlink components, devices, directories or FIFOs are accepted. The workspace must belong to the runtime user. Encoded input is at most 10 MiB, each side at most 8192 pixels, and total pixels at most 16 million. Only single-frame PNG/JPEG is decoded. EXIF orientation is applied; metadata is stripped and transparency is flattened onto white in a private temporary PNG. The original remains unchanged.

One OCR job runs at a time; another request fails promptly. The actual argv is `tesseract <private-input.png> <private-output-base> --tessdata-dir <fixed-dir> -l eng --psm 6 --dpi 300 txt tsv`. It uses no shell or caller-provided flags. The engine has a 45-second wall deadline, 30/31-second CPU soft/hard limits, 512 MiB address-space limit, 4 MiB per-file limit, no core dumps, and one OpenMP thread. Version probes have a 5-second deadline. TXT is limited to 1 MiB, TSV to 4 MiB, and each diagnostic stream to 1 MiB. Normalized private PNG is limited to 64 MiB. Artifact directories are mode 0700 and files 0600.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | no | empty | Set on sandbox creation; clients send a bearer token. |
| `ABX_SERVER_PORT` | no | `9000` | Direct local startup port. |
| `WORKSPACE` | no | `/home/user/app` | Existing runtime-user-owned input/output root. |
| `OCR_TESSERACT_BINARY` | no | `/usr/bin/tesseract` | Operator-only absolute executable path; version remains checked. |
| `OCR_TESSDATA_DIR` | no | `/usr/share/tesseract-ocr/5/tessdata` | Operator-only absolute data directory containing `eng.traineddata`. |

The last two settings support native diagnostics; they are not command parameters. The child receives only original HOME/PATH/optional library path and fixed locale/thread settings. No cloud or model credentials are forwarded. Keep untrusted callers away from general server shell/files APIs and operator configuration.

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU; engine uses one OpenMP thread |
| Memory | 1024 MB sandbox; native engine address space capped at 512 MiB |
| Port | 9000 |
| Disk | Platform rootfs; callers must remove retained result directories |

## Verified

Source tests: 27 passed with actual Tesseract 5.5.0 / Pillow 11.3.0. Source HTTP verification: 19 passed, zero failed, zero skipped, including a newly generated random-digit image, independently downloaded TXT/TSV, confidence/bounds checks and a blank-image negative control. These are source-runtime results. Actual image L1 and supplemental changed-image Express verification are pending; canonical `abx template deploy` / `scripts/express_e2e.py` L2 is not run. `tested_on` stays empty and catalog status remains experimental. See [verification](../.agents/evidence/verify/2026-10-16-ocr-runtime.md).

## Secondary development

Run `python3 scripts/check_template.py ocr --strict`, the scoped pytest files and `ocr/e2e_test.py`. Set `E2E_REQUIRE_OCR=1` for real acceptance so unavailable native dependencies fail rather than skip. `OCR_TEST_REAL=1` enables the real-engine pytest case. Keep artifact verification independent of the command result, and retain the original input/blank control. Additional languages, batch/PDF and alternative segmentation modes require their own explicit contracts and tests. See [design](../docs/design/ocr.md).

The Linux runner keeps its process leader unreaped with `waitid(WNOWAIT)`, drains bounded pipes, then stops the owned process group before reaping on success, nonzero exit, timeout or Python cancellation. Deliberate `setsid` escapes are outside that group boundary; killing the server with SIGKILL cannot execute Python cleanup. Sandbox destruction remains the final isolation boundary.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [template specification](../docs/template-spec.md), [Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57).

## Issues

Template/OCR integration: [awesome-templates issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template code and the original generated fixture: [Apache-2.0](../LICENSE). Official [Tesseract 5.5.0](https://github.com/tesseract-ocr/tesseract/tree/5.5.0) is Apache-2.0; Debian package copyright/attribution files remain installed. Pillow retains its distribution license. No font binary is redistributed; the committed image contains rendered original text. Dependency licenses remain their respective upstream licenses.
