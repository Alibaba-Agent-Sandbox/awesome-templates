# document-tools

## Purpose

Implement the first Pandoc text slice of [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55). An uploaded Markdown document becomes a meaningful DOCX/TXT artifact that callers can independently parse. No model/account or special hardware is needed.

## Capabilities

GFM Markdown input; DOCX or plain-text output; buffered named commands; ordinary shared server shell/files/code/ports. Headings, bold, lists and Unicode are tested. HTML input, images, PDF, slides, LibreOffice, arbitrary argv and GUI conversion are not delivered in this slice. The Issue remains open for its broader acceptance criteria.

## Exposed API

- `document_version() -> str`: exact `pandoc --version` check.
- `document_setup_check() -> dict`: read-only fixed executable availability.
- `convert(input_path: str, output_name: str, output_format: str="docx", command_timeout: int=30) -> dict`: fixed sandbox GFM → JSON parser, application AST validation, fixed DOCX/TXT writer. Output is one path, format, byte count and complete SHA256. Parameters/bounds are in [the command reference](../../document-tools/README.md#command-reference).
- `document_smoke() -> str`: create original Markdown, actually convert both formats, independently inspect XML/text markers, remove owned files.

No public SDK/server API changes are made. The new template narrows the survey's general conversion proposal to explicit text-only input/output modes.

## How to build

[Dockerfile](../../document-tools/Dockerfile) uses the Alibaba base, exact `pandoc=3.1.11.1+ds-2` and `pandoc-data=3.1.11.1-3`, preserved distribution notices and standard generation 2 serve/healthcheck. Server source fallback is immutable `e2cb27e24fde0a67112f82b8d44af463445a5d1a`, while an injected wheel wins. Non-root `user` owns `/home/user/app`. No office daemon, PDF engine or private source artifact is installed. Package identities were checked through official Debian metadata and actually executed extracted Debian packages, not inferred from a survey.

## Express feasibility

Feasible: slice

Limiting factor: this implementation covers only Pandoc Markdown → DOCX/TXT; the wider Issue's LibreOffice/PDF/HTML/slides require their own implementation and acceptance.

The implemented slice runs under 2 vCPU / 2048 MB with no nested Docker, KVM, display or extra capabilities. Native address space is capped at 1 GiB with a 256 MiB Haskell heap and two runtime capabilities, 30/31-second CPU limits and caller-bounded shared wall deadline. Input is at most 1 MiB, output at most 8 MiB, and one conversion is active per server.

## Risks

Descriptor walks refuse symlinks/traversal/devices and create a private regular-file snapshot. Atomic `link` publication never overwrites existing files. Sandbox parsing runs before an AST gate that rejects images, raw nodes, non-web/mail/fragment links, excessive node count/depth and removes metadata. TXT writing remains sandboxed. Actual Debian Pandoc cannot write DOCX under `--sandbox` because its data is not embedded; the fixed DOCX writer therefore receives only that validated image/raw-free AST and may read installed package data. No filters, custom templates, include options or PDF engines are accepted. This is an application IO boundary, not a claim of operating-system network confinement of the writer. General authenticated shell/files APIs retain their existing authority.

Native children receive no cloud/model credentials, use bounded diagnostics and allocator arenas, and their owned groups are killed before leader reap. Deliberately detached sessions and server SIGKILL are outside that cleanup guarantee. Ordinary artifacts accumulate until the caller removes them. Dependency GPL notices are preserved separately from the Apache-2.0 template code.

## Test plan

L0: checker; actual pinned Pandoc regression suite; actual authenticated Python SDK; required-engine HTTP E2E. Independent controllers create nonce/Unicode Markdown, upload/download through files APIs, verify full bytes/hashes and parse DOCX XML heading/bold/content plus TXT. Original input remains unchanged. Negative cases include path/URI/argv attempts, symlinks/FIFO/oversized/binary/empty inputs, images/raw/non-web links, no-clobber outputs, invalid limits/formats, concurrent work, bounded diagnostics, secret-environment exclusion, and real native descendant cleanup for success/failure/timeout. Missing source files during smoke failure must not prevent cleanup of other owned artifacts.

L1: actual Docker build must show the exact installed package/version and run non-root `document_version`/`document_smoke`. L2: actual canonical `scripts/express_e2e.py document-tools` must deploy with the real CLI and run both smoke commands externally via CLI/SDK with strict owned resource cleanup. L3: N/A; no model/agent claim. L4: no additional provider verified.
