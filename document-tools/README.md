# Document tools

[中文](README.zh-CN.md)

## What it does

Convert UTF-8 Markdown or bounded text HTML workspace files to actual DOCX, TXT, PPTX or native headless Writer PDF artifacts. The server returns the path, byte count and SHA256; callers download the file using the files API. No model, external account, display, GPU or privileged daemon is required.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a6`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Exact Debian 13 `pandoc=3.1.11.1+ds-2`, `pandoc-data=3.1.11.1-3`; their different version strings are intentional. Other OS libraries resolve from Debian repositories.
- Headless LibreOffice writer/core/common `4:25.2.3-2+deb13u8`, DejaVu `2.37-8` and Noto CJK `1:20240730+repack1-1`.
- Non-root `user`, writable `/home/user/app`, generation 2 standard serve/healthcheck, port 9000.

## Problem solved

Deliver the bounded text conversion requested by [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55): Markdown/HTML headings, emphasis, lists and Unicode become independently verifiable office documents, slides and PDF. Version 1.1 implements HTML/PPTX/Writer PDF alongside the original DOCX/TXT API; images, arbitrary native options and interactive GUI work remain outside this profile.

## Quick start (CLI)

CLI, SDK and HTTP are alternative ways to use the same application. Choose one for the task. Examples may write files, create projects or start services; do not repeat the full example on the same instance without cleaning its previous outputs.

Install the CLI/Python SDK and configure your platform with the [usage guide](../docs/using-templates.md#installation). The platform API key creates sandboxes; `ABX_SERVER_TOKEN` independently protects this template application. Run the following in your own terminal; cloning this repository is unnecessary.

These template commands require no model, model endpoint or model API key.

```bash
export ABX_PROVIDER=alicloud-express
export ABX_SERVER_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ABX_HTTP_TIMEOUT=450
abx template launch Alibaba-Agent-Sandbox/awesome-templates//document-tools --sandbox-timeout 1800 --yes
# Paste the sandbox ID from the launch output
export SANDBOX_ID='paste-id-from-launch-output'
abx sandbox command list "$SANDBOX_ID"
```

Prepare the input locally and upload it:

```bash
printf '# Quarterly report\n\nRevenue: 51.30.\n' > report.md
```

```bash
abx upload "$SANDBOX_ID" ./report.md /home/user/app/report.md
```

```bash
abx run "$SANDBOX_ID" convert --json-args '{"input_path":"report.md","output_name":"report.docx","output_format":"docx"}'
```

Returns `output_path`, `output_format: docx`, `bytes` and `sha256`. The DOCX is retained for download.

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

The SDK returns the command value; it unwraps the HTTP `result` envelope. Closing the client does not delete the sandbox.

## Quick start (HTTP POST)

Resolve port 9000 on the same instance with the [HTTP calling example](../docs/using-templates.md#cli-sdk-and-http). Preserve gateway headers, URL path and query before adding the independent application authentication.

`POST /commands/convert`

```json
{
  "input_path": "report.md",
  "output_name": "report.docx",
  "output_format": "docx"
}
```

Use `Content-Type: application/json` and application authentication as described in the shared guide. The request body is the direct argument object, without an `args` wrapper. Success returns `{"result": ...}` with the value described above. Set the HTTP client wait to 450 seconds, separately from the command execution deadline. Responses are buffered, not event streams. Errors: 400 invalid arguments, 401 authentication, 404 unknown command, 500 execution failure.

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `document_version` | none | string | Actual pinned `pandoc 3.1.11.1`. |
| `document_setup_check` | none | object | Pinned executable availability; no document processing. |
| `convert` | required strings `input_path`, `output_name`; `output_format`: `docx` (default), `txt`, `pptx` or `pdf`; `input_format`: `markdown` (default) or `html`; integer `command_timeout`: default 30, range 1–60 | object | Path, format, bytes and SHA256 of a new artifact. |
| `document_smoke` | none | string | Actual owned Markdown → DOCX/TXT, independent content inspection and cleanup. |
| `office_version` | none | string | Verify the exact Debian Writer package and actual native version. |
| `document_extended_smoke` | none | string | Actual HTML/DOCX, PPTX and headless PDF creation, container checks and owned cleanup. |

Input is one nonempty UTF-8 file, at most 1 MiB, identified by a relative path inside `WORKSPACE`. No parent traversal, absolute paths, symlink components, devices or FIFOs are allowed. A descriptor-based read creates a private snapshot. Output uses a plain ASCII filename beginning with a letter/digit, followed by at most 119 letters/digits/underscores/dots/hyphens, and the selected extension; existing files or symlinks are never overwritten.

The first fixed Pandoc stage reads GFM with `--sandbox` into a bounded JSON AST. Validation rejects Image/Raw nodes, non-web/non-mail/non-fragment links, excessive complexity/depth, and removes metadata. The fixed TXT writer runs sandboxed. Debian's non-embedded-data Pandoc cannot produce DOCX with `--sandbox` because its internal templates live on disk; only the validated image/raw-free AST reaches the fixed DOCX writer, which may read the installed package data. PDF uses the sole fixed, isolated Writer stage. Conversion options are the documented formats and deadline; arbitrary filters/includes/templates/argv are excluded. This is an explicit application boundary, not an operating-system network sandbox for the whole writer.

One conversion runs at a time. Pandoc has 1 GiB address space, a 256 MiB Haskell heap, two runtime capabilities and 30/31-second CPU soft/hard limits. Writer has 2 GiB address space and 60/61-second CPU limits. Both retain the 8 MiB per-file limit, disabled core dumps and shared operation wall deadline. Only HOME/PATH/optional library path, fixed locale/thread/allocator settings and the operator-selected package data path are forwarded; Writer substitutes its owned HOME/XDG/temp directories. Each diagnostic/AST output stream is capped at 1 MiB; native diagnostics are omitted from errors. OOXML entry counts, expanded size and required XML are checked before no-clobber publication.

## Configuration

| Name | Required | Default | Purpose |
|---|---|---|---|
| `ABX_SERVER_TOKEN` | yes | empty | Export an independent application token before the template launch; separate from model and gateway credentials |
| `ABX_SERVER_PORT` | no | `9000` | Port for direct local startup. |
| `WORKSPACE` | no | `/home/user/app` | Existing runtime-user-owned input/output directory. |
| `DOCUMENT_PANDOC_BINARY` | no | `/usr/bin/pandoc` | Operator-only absolute executable path, still version checked. |
| `DOCUMENT_PANDOC_DATA_DIR` | no | `/usr/share/pandoc` | Operator-only installed package data root, forwarded through Debian's `pandoc_datadir`. |

Prewarmed servers read their process-start configuration before subsequent shell environment changes. The named path policy does not constrain the shared authenticated shell/files APIs. Native source diagnostics can use the final two settings; they are not command parameters.

The working directory is `/home/user/app`. Artifacts remain on the sandbox disk; export anything needed before deleting the instance. Delete only your own instance and the prepared template/image identified by its launch receipt.

```bash
# Replace <returned-path> with output_path from the result
abx download "$SANDBOX_ID" '<returned-path>' ./report.docx
abx kill "$SANDBOX_ID"
```

`abx kill` deletes the sandbox, not reusable prepared templates or images. Follow the [cleanup guide](../docs/using-templates.md#cli-sdk-and-http) for resources created by your launch.

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU; two Haskell runtime capabilities |
| Memory |4096MB sandbox; Pandoc1GiB address space/256 MiB heap; Office2GiB address space |
| Port | 9000 |
| Disk | Platform rootfs; 1 MiB input, 8 MiB output; callers remove retained artifacts |

## Contributing

To improve this template, see the [contribution guide](../CONTRIBUTING.md), [template specification](../docs/template-spec.md) and [design notes](../docs/design/document-tools.md).

## Issues

Template integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template Python code: [Apache-2.0](../LICENSE). LibreOffice is distributed under [MPL-2.0 and its bundled component licenses](https://www.libreoffice.org/licenses/); the exact [Debian LibreOffice source](https://packages.debian.org/source/trixie/libreoffice) and installed copyright notices remain authoritative. Font copyright/license files are retained. [Pandoc](https://pandoc.org/) retains GPL-2.0-or-later and installed Debian copyright notices; it is not relabeled as template Apache-2.0 code. Exact distribution source: [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) and [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data). Smoke Markdown is original generated text.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
