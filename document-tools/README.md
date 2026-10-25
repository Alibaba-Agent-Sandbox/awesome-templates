# Document tools

Offline text conversion with Pandoc and headless Writer. [中文说明](README.zh-CN.md).

## What it does

Convert UTF-8 Markdown or bounded text HTML workspace files to actual DOCX, TXT, PPTX or native headless Writer PDF artifacts. The server returns the path, byte count and SHA256; callers download the file using the files API. No model, external account, display, GPU or privileged daemon is required.

## Stack

Runtime server: published `agent-sandbox-server==0.4.0a4`, installed directly by the Dockerfile.

- Alibaba base `fc-e2b-registry.<region>.cr.aliyuncs.com/runtime/base:<tag>`, normally `cn-hangzhou` / `v0.0.49`.
- Exact Debian 13 `pandoc=3.1.11.1+ds-2`, `pandoc-data=3.1.11.1-3`; their different version strings are intentional. Other OS libraries resolve from Debian repositories.
- Headless LibreOffice writer/core/common `4:25.2.3-2+deb13u8`, DejaVu `2.37-8` and Noto CJK `1:20240730+repack1-1`.
- Non-root `user`, writable `/home/user/app`, generation 2 standard serve/healthcheck, port 9000.

## Problem solved

Deliver the bounded text conversion requested by [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55): Markdown/HTML headings, emphasis, lists and Unicode become independently verifiable office documents, slides and PDF. Version 1.1 implements HTML/PPTX/Writer PDF alongside the original DOCX/TXT API; images, arbitrary native options and interactive GUI work remain outside this profile.

## Quick start (CLI)

Follow the [usage guide](../docs/using-templates.md#installation) to install the clients, configure the provider and set an independent `ABX_SERVER_TOKEN`. From this repository's root, launch the application and retain its sandbox ID. Replace `<sandbox-id>` below with that ID.

```bash
export ABX_PROVIDER=alicloud-express
abx template launch ./document-tools --yes
abx run <sandbox-id> document_version --json-args '{}'
```

`template launch` prepares and starts this instance's application. For OpenSandbox, set `ABX_PROVIDER=opensandbox` above and use `provider="opensandbox"` in Python. See the [complete calling flow](../docs/using-templates.md#cli-sdk-and-http) for OpenSandbox configuration, provider selection on every call and owned-resource cleanup. The next examples reuse the same running instance.

## Quick start (Python SDK)

Install `agent-sandbox-client` and follow the [Python connection example](../docs/using-templates.md#cli-sdk-and-http), using `ProviderSandbox.connect` and `application_client` with the independent application token. Replace the command call inside that example's `try` block with:

```python
print(await client.commands.run('document_version'))
```

Keep the guide's connection and close steps. `sb.commands.run` executes a process; `client.commands.run` calls this template's named commands. Business commands, arguments and limits are listed in the command reference below.

## Quick start (HTTP POST)

Follow the [HTTP example](../docs/using-templates.md#cli-sdk-and-http) to resolve the endpoint, preserve gateway headers, path and query parameters, and set the independent application token. Change the request to `POST /commands/document_version`, with `Content-Type: application/json` and this direct argument object:

```json
{}
```

Expected response for this check:

```json
{"result": "pandoc 3.1.11.1"}
```

`result` is buffered, not an event stream. Missing or mistyped arguments return 400, failed authentication 401, unknown commands 404, and execution errors 500. Set the HTTP wait and command deadline separately; a client timeout does not guarantee cancellation.

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

## Resources

| Resource | Value |
|---|---|
| CPU | 2 vCPU; two Haskell runtime capabilities |
| Memory |4096MB sandbox; Pandoc1GiB address space/256 MiB heap; Office2GiB address space |
| Port | 9000 |
| Disk | Platform rootfs; 1 MiB input, 8 MiB output; callers remove retained artifacts |

## Verified

See [test results and scope](../docs/using-templates.md#evidence-and-providers). The dated records below identify the tested input and entry point.

## Historical 1.0 verification


| Provider | Executed scope | Evidence |
| --- | --- | --- |
| alicloud-express | steps build, official READY, CLI + SDK smoke, independent owned cleanup readback | [2026-10-19](evidence/express-2026-10-19.json) |

This historical run used the pinned e2cb27e server-source override matching the then-current image CI injection; the receipt records exact versions, input hashes and build mode. Only verification metadata changes here; the template stays experimental. Dockerfile L1, full product and real-model acceptance are assessed by their separate records and cannot be inferred from basic smoke.

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
