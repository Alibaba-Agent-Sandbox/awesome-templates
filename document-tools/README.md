# Document tools

Offline text conversion with Pandoc and headless Writer. [中文说明](README.zh-CN.md).

## What it does

Convert UTF-8 Markdown or bounded text HTML workspace files to actual DOCX, TXT, PPTX or native headless Writer PDF artifacts. The server returns the path, byte count and SHA256; callers download the file using the files API. No model, external account, display, GPU or privileged daemon is required.

## Stack

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Exact Debian 13 `pandoc=3.1.11.1+ds-2`, `pandoc-data=3.1.11.1-3`; their different version strings are intentional. Other OS libraries resolve from Debian repositories.
- Headless LibreOffice writer/core/common `4:25.2.3-2+deb13u8`, DejaVu `2.37-8` and Noto CJK `1:20240730+repack1-1`.
- Injected server wheel or immutable python-sdk source `e2cb27e24fde0a67112f82b8d44af463445a5d1a`.
- Non-root `user`, writable `/home/user/app`, generation 2 standard serve/healthcheck, port 9000.

## Problem solved

Deliver the bounded text conversion requested by [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55): Markdown/HTML headings, emphasis, lists and Unicode become independently verifiable office documents, slides and PDF. Version 1.1 implements HTML/PPTX/Writer PDF alongside the original DOCX/TXT API; images, arbitrary native options and interactive GUI work remain outside this profile.

## Quick start (CLI)

The examples use the current Express CLI: `abx create <template-id> --detach` prints the sandbox ID; `abx kill <sandbox-id>` cleans it up. Named commands use `abx run`. See the [entry comparison](../docs/using-templates.md#client-entry-compatibility).

```bash
abx template deploy ./document-tools -y --generation 2
abx create <template-id> --detach
abx run <sandbox-id> document_smoke
abx run <sandbox-id> convert --arg input_path=report.md --arg output_name=report.docx
abx kill <sandbox-id>
abx template delete <template-id> -y
```

Upload `report.md` to `/home/user/app` first. `document_smoke` creates original Markdown, converts it, independently inspects DOCX XML and TXT content, and deletes only its owned files. Ordinary conversion artifacts remain until callers delete them or destroy the sandbox.

## Quick start (Python SDK)

Use `agent-sandbox-client` with its paired `agent-sandbox-server`; follow [the pinned source installation recipe](../docs/python-client-installation.md).

Install the paired source packages using [the pinned SDK installation recipe](../docs/python-client-installation.md). The Python import is `agent_sandbox`.

```python
import asyncio
from agent_sandbox.api.sandbox import Sandbox

async def main():
    sb = await Sandbox.create(template="<template-id>", timeout=300)
    try:
        print(await sb.run("document_smoke"))
        # After uploading report.md into /home/user/app:
        result = await sb.run("convert", input_path="report.md", output_name="report.docx", timeout=90)
        print(result["output_path"], result["sha256"])
    finally:
        await sb.kill()

asyncio.run(main())
```

`sb.run` invokes a named command; `sb.commands.run` invokes the shared server shell. Use the files API to upload/download artifacts. `timeout` above is the HTTP timeout; the named command's deadline parameter is `command_timeout`.

## Quick start (HTTP POST)

Use the sandbox's port-9000 URL and the provider's required gateway access header. Supply a separate bearer token when the running server has `ABX_SERVER_TOKEN` configured.

```bash
curl --fail-with-body --max-time 90 --request POST "$ABX_SERVER_URL/commands/convert" \
  --header "Authorization: Bearer $ABX_SERVER_TOKEN" \
  --header 'Content-Type: application/json' \
  --data '{"input_path":"report.md","output_name":"report.docx","output_format":"docx","command_timeout":30}'
```

Arguments are direct JSON parameters. HTTP 200 returns `{"result":{"output_path":"/home/user/app/report.docx","output_format":"docx","bytes":12345,"sha256":"<64 hex characters>"}}`, with size/hash depending on content. Missing/mistyped arguments return 400; failed authentication 401; unknown commands 404; invalid paths, document content, limits or execution errors 500 with `error` and `type`. Results are buffered. A client timeout or disconnection does not guarantee cancellation.

### Version 1.1 text-document profile

The existing `convert` command keeps its required paths and default Markdown/DOCX
behavior. Add `input_format="html"` for balanced text HTML and choose
`output_format="docx"|"txt"|"pptx"|"pdf"`. The extra parameter is optional;
existing callers remain compatible. A plain output filename must match its format.

```bash
abx run <sandbox-id> convert --arg input_path=uploaded.html --arg input_format=html --arg output_name=document.pdf --arg output_format=pdf --arg command_timeout=60
abx run <sandbox-id> convert --arg input_path=uploaded.md --arg output_name=slides.pptx --arg output_format=pptx
```

```python
result = await sb.run("convert", input_path="uploaded.html", input_format="html", output_name="document.pdf", output_format="pdf", command_timeout=60, timeout=90)
```

The direct HTTP body is `{"input_path":"uploaded.html","input_format":"html","output_name":"document.pdf","output_format":"pdf","command_timeout":60}`.
Successful calls return the existing output path/format/bytes/SHA256 fields.
`office_version` verifies actual headless Writer and its exact Debian package;
`document_extended_smoke` creates HTML/DOCX, native PPTX and Writer PDF and removes
its own files. Its PDF signature is supplemented by independent external pypdf
page/text/nonce verification in the full HTTP controller.

Pandoc remains at `3.1.11.1` with its distinct pinned Debian data package. PDF uses only
DOCX generated from validated, metadata-free, image/raw-free Pandoc AST, then
actual LibreOffice Writer. Pin writer-nogui/core-nogui/common to
`4:25.2.3-2+deb13u8`, DejaVu `2.37-8` and Noto CJK `1:20240730+repack1-1`;
Debian resolves unrelated libraries. No uploaded DOCX/macros are accepted.
Each document conversion uses a fresh private HOME/XDG/temp/profile and the official
soffice launcher with `-env:UserInstallation`, headless/no-default-document flags.
The caller's profile is never reused. No GUI/display, daemon, GPU or model is needed.

HTML accepts explicit balanced text tags, headings, lists, tables, emphasis,
code and web/mail/fragment links. Reject resource/script/style/event attributes,
images/iframes/objects and arbitrary tags before the sandboxed reader. At most
20,000 tags and depth 100; AST bounds still apply. PPTX uses native Pandoc slide level 2
and validates 1–100 slide XML entries. PDF and all artifacts remain at most 8 MiB;
inputs remain 1 MiB/UTF-8. Shared deadlines and no-clobber publication remain.
Office has 2 GiB address-space/60–61second CPU guards; Pandoc keeps 1 GiB address
space/256 MiB Haskell heap and 30–31 second CPU guards. The sandbox profile is now
2 vCPU/4 GiB. A deliberately detached child or abrupt server loss still requires
final sandbox destruction.

For independent PDF verification, install the public controller dependency
`pypdf==6.21.1`; the image does not require that Python library. Native LibreOffice,
font and Pandoc licenses remain in installed Debian copyright files; template
code retains Apache-2.0. See [LibreOffice package](https://packages.debian.org/trixie/libreoffice-writer-nogui)
and [official profile/headless/conversion parameters](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html).

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
| `ABX_SERVER_TOKEN` | no | empty | Configure authentication before the server process starts. |
| `ABX_SERVER_PORT` | no | `9000` | Port for direct local startup. |
| `WORKSPACE` | no | `/home/user/app` | Existing runtime-user-owned input/output directory. |
| `DOCUMENT_PANDOC_BINARY` | no | `/usr/bin/pandoc` | Operator-only absolute executable path, still version checked. |
| `DOCUMENT_PANDOC_DATA_DIR` | no | `/usr/share/pandoc` | Operator-only installed package data root, forwarded through Debian's `pandoc_datadir`. |

Prewarmed servers read their process-start configuration before subsequent shell environment changes. The named path policy does not constrain the shared authenticated shell/files APIs. Native source diagnostics can use the final two settings; they are not command parameters.

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU; two Haskell runtime capabilities |
| Memory |4096MB sandbox; Pandoc1GiB address space/256 MiB heap; Office2GiB address space |
| Port | 9000 |
| Disk | Platform rootfs; 1 MiB input, 8 MiB output; callers remove retained artifacts |

## Verified

No project-recognized receipt certifies the current workflow manifest. Historical acceptance records retain only their original input and call-path scope; see [workflow verification](../docs/workflows.md).

## Historical 1.0 verification


| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This run uses the pinned e2cb27e server-source override matching existing image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

<details>
<summary>Earlier checkpoint text (historical; current steps result is above)</summary>

No provider has a passing run recorded for this template.

Actual image L1 and dedicated native/SDK/HTTP CI passed on the recorded runtime source; see [the CI confirmation](../.agents/evidence/verify/2026-10-18-document-tools-ci-confirmation.md). Local preparation and initial remote failures remain in [the original record](../.agents/evidence/verify/2026-10-18-document-tools-runtime.md). Canonical provider L2 has not run. Status remains experimental with empty `tested_on`.

</details>

## Secondary development

Read [the design](../docs/design/document-tools.md), then run `python3 scripts/check_template.py document-tools`, `python3 -m pytest -q document-tools/test_commands.py document-tools/test_http.py`, and the local E2E runner. Tests require the actual pinned Debian engine/data. `E2E_REQUIRE_DOCUMENT=1` makes missing native dependencies fail instead of recording SKIP. The external controller uploads fresh nonce/Unicode Markdown, downloads full artifacts, verifies hashes and independently parses DOCX heading/bold/content plus TXT before cleanup.

Native cleanup keeps the leader unreaped via `waitid(WNOWAIT)` until killing its owned group, including success/nonzero leaders and redirected descendants. Deliberate `setsid` escapes and server SIGKILL are outside that guarantee. Sandbox destruction remains the final isolation boundary.

The runtime workspace must permit hardlinks for atomic no-clobber publication. Some managed source mounts reject this syscall; run a byte-identical local test context on an ordinary writable Linux filesystem, or set an appropriate process-start workspace before startup. A rejected hardlink fails conversion and does not fall back to overwriting files.

### Agent Sandbox platform steps

From a repository checkout, `python scripts/run_steps_e2e.py document-tools` builds and verifies this template through real Express platform steps. See [preparation, credentials, exact build provenance and cleanup](../docs/platform-steps.md). A model-free step smoke does not establish L3.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [template specification](../docs/template-spec.md), [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55).

## Issues

Template integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template Python code: [Apache-2.0](../LICENSE). LibreOffice is distributed under [MPL-2.0 and its bundled component licenses](https://www.libreoffice.org/licenses/); the exact [Debian LibreOffice source](https://packages.debian.org/source/trixie/libreoffice) and installed copyright notices remain authoritative. Font copyright/license files are retained. [Pandoc](https://pandoc.org/) retains GPL-2.0-or-later and installed Debian copyright notices; it is not relabeled as template Apache-2.0 code. Exact distribution source: [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) and [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data). Smoke Markdown is original generated text.

For CLI setup, SDK installation, HTTP authentication and resource ownership, see [Using templates](../docs/using-templates.md).
