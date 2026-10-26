# OCR

[中文](README.zh-CN.md)

## What it does

`ocr(image_path)` recognizes one workspace PNG or JPEG and returns text, image dimensions, word count, and private TXT/TSV artifact paths with SHA256 hashes. It runs the actual Tesseract engine; no model, API key or network request is needed. Blank images legitimately return no words. English is the installed recognition language; bilingual documentation does not imply Chinese recognition support.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`; deployment defaults are `cn-hangzhou` / `v0.0.49`.
- Debian 13 Tesseract / libtesseract `5.5.0-1+b1`, English and orientation data `1:4.1.0-2`, Leptonica `1.84.1-4`. Other OS libraries resolve through the base's Debian repositories.
- Pillow `11.3.0`, downloaded against the committed SHA256 wheel allowlist, then installed offline with --no-index/--no-deps; source distributions are disabled.
- Non-root `user`, `/home/user/app`, generation 2 canonical server startup, port 9000. Original `HOME` is preserved.

## Problem solved

Extract searchable English text and word coordinates from an uploaded image without a GPU or remote OCR service. The first slice handles one image per request with a fixed page segmentation mode; PDF, archives, batch processing, handwritten text and additional language packs are outside this interface.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//ocr --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

```bash
abx run "$SANDBOX_ID" ocr --json-args '{"image_path":"fixtures/sample.png"}'
```

Recognizes the bundled sample; `text` contains SANDBOX, OCR and 314159. Returns TXT/TSV paths and hashes for export.

For your own image, upload it with `abx upload "$SANDBOX_ID" ./scan.png /home/user/app/scan.png`, then change `image_path` to `scan.png`. Only English `eng` data is bundled; this is not a multimodal model or a claim of Chinese OCR support.

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
            result = await client.commands.run('ocr', image_path='fixtures/sample.png')
            print(result)
            Path('recognized.txt').write_bytes(await sb.files.read_bytes(result['text_path']))
        finally:
            await client.aclose()
    finally:
        await sb.close()

asyncio.run(main())
```

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/ocr`

```json
{
  "image_path": "fixtures/sample.png"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

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
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Direct local startup port. |
| `WORKSPACE` | no | `/home/user/app` | Existing runtime-user-owned input/output root. |
| `OCR_TESSERACT_BINARY` | no | `/usr/bin/tesseract` | Operator-only absolute executable path; version remains checked. |
| `OCR_TESSDATA_DIR` | no | `/usr/share/tesseract-ocr/5/tessdata` | Operator-only absolute data directory containing `eng.traineddata`. |

The last two settings support native diagnostics; they are not command parameters. The child receives only original HOME/PATH/optional library path and fixed locale/thread settings. No cloud or model credentials are forwarded. Keep untrusted callers away from general server shell/files APIs and operator configuration.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with text_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./recognized.txt
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

| Resource | Value |
|---|---|
| CPU | 1 vCPU; engine uses one OpenMP thread |
| Memory | 1024 MB sandbox; native engine address space capped at 512 MiB |
| Port | 9000 |
| Disk | Platform rootfs; callers must remove retained result directories |

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/ocr.md).

## Issues

Template/OCR integration: [awesome-templates issues](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk issues](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox issues](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template code and the original generated fixture: [Apache-2.0](../LICENSE). Official [Tesseract 5.5.0](https://github.com/tesseract-ocr/tesseract/tree/5.5.0) is Apache-2.0; Debian package copyright/attribution files remain installed. Pillow retains its distribution license. No font binary is redistributed; the committed image contains rendered original text. Dependency licenses remain their respective upstream licenses.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
