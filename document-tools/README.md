# Document tools

Offline Markdown conversion with Pandoc. [中文说明](README.zh-CN.md).

## What it does

Convert a UTF-8 Markdown workspace file to a real DOCX or plain-text artifact. The server returns the path, byte count and SHA256; callers download the file using the files API. No model, external account, display, GPU or privileged daemon is required.

## Stack

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Exact Debian 13 `pandoc=3.1.11.1+ds-2`, `pandoc-data=3.1.11.1-3`; their different version strings are intentional. Other OS libraries resolve from Debian repositories.
- Injected server wheel or immutable python-sdk source `e2cb27e24fde0a67112f82b8d44af463445a5d1a`.
- Non-root `user`, writable `/home/user/app`, generation 2 standard serve/healthcheck, port 9000.

## Problem solved

Deliver the text-first Pandoc slice of [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55): headings, emphasis, lists and Unicode text become independently verifiable documents. The interface accepts GFM Markdown and outputs DOCX/TXT. HTML input, images, PDF, slides and LibreOffice are future work and are not implied by this template name.

## Quick start (CLI)

```bash
abx template deploy ./document-tools -y --generation 2
abx create --template <template-id> -y
abx run <sandbox-id> document_smoke
abx run <sandbox-id> convert --arg input_path=report.md --arg output_name=report.docx
abx kill <sandbox-id> -y
abx template delete <template-id> -y
```

Upload `report.md` to `/home/user/app` first. `document_smoke` creates original Markdown, converts it, independently inspects DOCX XML and TXT content, and deletes only its owned files. Ordinary conversion artifacts remain until callers delete them or destroy the sandbox.

## Quick start (Python SDK)

Install `agent-sandbox-client` following [the client installation guide](../docs/python-client-installation.md); import `agent_sandbox`.

```python
import asyncio
from agent_sandbox import Sandbox

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

## Command reference

| Command | Parameters | Returns | Description |
|---|---|---|---|
| `document_version` | none | string | Actual pinned `pandoc 3.1.11.1`. |
| `document_setup_check` | none | object | Pinned executable availability; no document processing. |
| `convert` | required strings `input_path`, `output_name`; `output_format`: `docx` (default) or `txt`; integer `command_timeout`: default 30, range 1–60 | object | Path, format, bytes and SHA256 of a new artifact. |
| `document_smoke` | none | string | Actual owned Markdown → DOCX/TXT, independent content inspection and cleanup. |

Input is one nonempty UTF-8 file, at most 1 MiB, identified by a relative path inside `WORKSPACE`. No parent traversal, absolute paths, symlink components, devices or FIFOs are allowed. A descriptor-based read creates a private snapshot. Output uses a plain ASCII filename beginning with a letter/digit, followed by at most 119 letters/digits/underscores/dots/hyphens, and the selected extension; existing files or symlinks are never overwritten.

The first fixed Pandoc stage reads GFM with `--sandbox` into a bounded JSON AST. Validation rejects Image/Raw nodes, non-web/non-mail/non-fragment links, excessive complexity/depth, and removes metadata. The fixed TXT writer runs sandboxed. Debian's non-embedded-data Pandoc cannot produce DOCX with `--sandbox` because its internal templates live on disk; only the validated image/raw-free AST reaches the fixed DOCX writer, which may read the installed package data. No filter, include flag, custom template, PDF engine or caller-provided argv is accepted. This is an explicit application boundary, not an operating-system network sandbox for the whole writer.

One conversion runs at a time. Each native process has 1 GiB address space, 256 MiB Haskell heap, two runtime capabilities, 30/31-second CPU soft/hard limits, 8 MiB per-file limit, no core dumps, and a shared operation wall deadline. Only HOME/PATH/optional library path, fixed locale/thread/allocator settings and the operator-selected package data path are forwarded. Each diagnostic/AST output stream is capped at 1 MiB; native diagnostics are omitted from errors. DOCX ZIP entry counts, total expanded size and document XML are checked before no-clobber publication.

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
| Memory | 2048 MB sandbox, 1 GiB native address-space limit, 256 MiB heap |
| Port | 9000 |
| Disk | Platform rootfs; 1 MiB input, 8 MiB output; callers remove retained artifacts |

## Verified

No provider has a passing run recorded for this template.

See [source verification and pending gates](../.agents/evidence/verify/2026-10-18-document-tools-runtime.md). Local native/SDK/HTTP results do not establish Docker L1 or canonical provider L2. Status remains experimental with empty `tested_on`.

## Secondary development

Read [the design](../docs/design/document-tools.md), then run `python3 scripts/check_template.py document-tools`, `python3 -m pytest -q document-tools/test_commands.py document-tools/test_http.py`, and the local E2E runner. Tests require the actual pinned Debian engine/data. `E2E_REQUIRE_DOCUMENT=1` makes missing native dependencies fail instead of recording SKIP. The external controller uploads fresh nonce/Unicode Markdown, downloads full artifacts, verifies hashes and independently parses DOCX heading/bold/content plus TXT before cleanup.

Native cleanup keeps the leader unreaped via `waitid(WNOWAIT)` until killing its owned group, including success/nonzero leaders and redirected descendants. Deliberate `setsid` escapes and server SIGKILL are outside that guarantee. Sandbox destruction remains the final isolation boundary.

## Contributing

[CONTRIBUTING.md](../CONTRIBUTING.md), [template specification](../docs/template-spec.md), [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55).

## Issues

Template integration: [awesome-templates](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues). Server/client contracts: [python-sdk](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues). Deployment CLI: [agent-sandbox](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/issues).

## License

Template Python code: [Apache-2.0](../LICENSE). [Pandoc](https://pandoc.org/) retains GPL-2.0-or-later and installed Debian copyright notices; it is not relabeled as template Apache-2.0 code. Exact distribution source: [Debian pandoc](https://packages.debian.org/source/trixie/pandoc) and [pandoc-data](https://packages.debian.org/source/trixie/pandoc-data). Smoke Markdown is original generated text.
