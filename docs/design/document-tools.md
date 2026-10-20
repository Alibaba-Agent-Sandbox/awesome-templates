# document-tools

## Purpose

Implement the first Pandoc text slice of [Issue 55](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/55). An uploaded Markdown document becomes a meaningful DOCX/TXT artifact that callers can independently parse. No model/account or special hardware is needed.

## Capabilities

GFM Markdown input; DOCX or plain-text output; buffered named commands; ordinary shared server shell/files/code/ports. Headings, bold, lists and Unicode are tested. Version1.1 adds guarded text HTML input, native Pandoc PPTX and headless LibreOffice Writer PDF. Images, arbitrary argv and GUI conversion remain excluded; actual1.1image/Express acceptance is pending.

## Exposed API

- `document_version() -> str`: exact `pandoc --version` check.
- `document_setup_check() -> dict`: read-only fixed executable availability.
- `convert(input_path: str, output_name: str, output_format: str="docx", command_timeout: int=30, input_format: str="markdown") -> dict`: fixed sandbox GFM → JSON parser, application AST validation, fixed DOCX/TXT writer. Output is one path, format, byte count and complete SHA256. Parameters/bounds are in [the command reference](../../document-tools/README.md#command-reference).
- `document_smoke() -> str`: create original Markdown, actually convert both formats, independently inspect XML/text markers, remove owned files.

No public SDK/server API changes are made. The new template narrows the survey's general conversion proposal to explicit text-only input/output modes.

## How to build

[Dockerfile](../../document-tools/Dockerfile) uses the Alibaba base, exact `pandoc=3.1.11.1+ds-2` and `pandoc-data=3.1.11.1-3`, preserved distribution notices and standard generation 2 serve/healthcheck. Server source fallback is immutable `e2cb27e24fde0a67112f82b8d44af463445a5d1a`, while an injected wheel wins. Non-root `user` owns `/home/user/app`. Headless writer-nogui/core-nogui/common are pinned to4:25.2.3-2+deb13u8with DejaVu/Noto fonts. Each conversion gets a fresh private profile; only generated validated DOCX reaches Writer. There is no persistent office daemon. Pandoc package identities and actual extracted programs were verified. Writer package availability is checked against official Debian metadata; its required native CI/image/Express execution remains pending.

## Express feasibility

Feasible: yes for the bounded CPU text profile; new image/Express validation pending

Limiting factor: actual pinned native PDF/image/provider acceptance remains required; no display/GPU/KVM is needed.

The implemented slice runs under 2 vCPU / 4096 MB with no nested Docker, KVM, display or extra capabilities. Native address space is capped at 1 GiB with a 256 MiB Haskell heap and two runtime capabilities, 30/31-second CPU limits and caller-bounded shared wall deadline. Input is at most 1 MiB, output at most 8 MiB, and one conversion is active per server.

## Risks

Descriptor walks refuse symlinks/traversal/devices and create a private regular-file snapshot. Atomic `link` publication never overwrites existing files. Sandbox parsing runs before an AST gate that rejects images, raw nodes, non-web/mail/fragment links, excessive node count/depth and removes metadata. TXT writing remains sandboxed. Actual Debian Pandoc cannot write DOCX under `--sandbox` because its data is not embedded; the fixed DOCX writer therefore receives only that validated image/raw-free AST and may read installed package data. PDF uses the sole fixed Writer stage; arbitrary filters/templates/includes/native options are excluded. This is an application IO boundary, not a claim of operating-system network confinement of the writer. General authenticated shell/files APIs retain their existing authority.

Native children receive no cloud/model credentials, use bounded diagnostics and allocator arenas, and their owned groups are killed before leader reap. Deliberately detached sessions and server SIGKILL are outside that cleanup guarantee. Ordinary artifacts accumulate until the caller removes them. Dependency GPL notices are preserved separately from the Apache-2.0 template code.

## Test plan

L0: checker; actual pinned Pandoc regression suite; actual authenticated Python SDK; required-engine HTTP E2E. Independent controllers create nonce/Unicode Markdown, upload/download through files APIs, verify full bytes/hashes and parse DOCX XML heading/bold/content plus TXT. Original input remains unchanged. Negative cases include path/URI/argv attempts, symlinks/FIFO/oversized/binary/empty inputs, images/raw/non-web links, no-clobber outputs, invalid limits/formats, concurrent work, bounded diagnostics, secret-environment exclusion, and real native descendant cleanup for success/failure/timeout. Missing source files during smoke failure must not prevent cleanup of other owned artifacts.

L1: actual Docker build must show the exact installed package/version and run non-root `document_version`/`document_smoke`. L2: actual canonical `scripts/express_e2e.py document-tools` must deploy with the real CLI and run both smoke commands externally via CLI/SDK with strict owned resource cleanup. L3: N/A; no model/agent claim. L4: no additional provider verified.


## Version1.1implementation and independent acceptance

An explicit HTML text parser rejects resource-bearing tags/attributes before
sandboxed Pandoc input. Existing AST validation/removal of metadata remains.
PPTX is generated by the native writer and its slide XML is bounded/validated.
PDF first validates generated DOCX, then executes the actual pinned headless
Writer with unique HOME/XDG/temp/UserInstallation directories. The direct binary
avoids launcher adoption of a caller's office profile. Office gets2GiB native
address space and60/61second CPU guards; the shared wall deadline, process-group
cleanup and8MiB/no-clobber artifact contract remain.

Local pinned native Pandoc tests independently parse HTML/DOCX/TXT/PPTX and fresh
markers; PDF is explicitly skipped when headless Writer is absent on the operator.
The required native Debian CI installs the exact engine and pypdf6.21.1and cannot
skip. The external full HTTP controller independently downloads and parses actual
PDF pages/text/nonce, PPTX slides and DOCX styling, verifies complete hashes and
original inputs, then deletes only owned files. Old1.0provider receipts never
qualify1.1. See the new dated engineering record for exact current results.
