# AppWorld immutable upstream research

Status: PARTIAL. Date:2026-10-20. Issue https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70.

Verified primary upstream tagv0.1.3.post1 resolves66ad8099e12188ece0d3fe45e661dbc01880813b; its README documents direct Python execution, in-process native APIs and optional Docker. PyPI publishes matching0.1.3.post1, requires Python>=3.11,<4.0 and supplies the actual wheel hash/size recorded in the decision. Downloaded the exact official original34,280,074-byte encrypted dataset and measured its SHA256; no benchmark/agent/model code installed or executed locally.

Inspected original AppWorld, task loading, native evaluator, install/download, paper baseline agents and license. The historical plain baseline modules contain interface assumptions requiring separate qualification; no baseline success is claimed. Protected app/task/data content has an encrypted-public-redistribution requirement, so public images/records must preserve that boundary.

Native runtime compatibility, complete implementation, L0/L1/actual Express/model/evaluator and cleanup gates NOT RUN. No cloud resources created by this research. Retain public metadata/source snippets and original encrypted bundle until active acceptance ends; never publish decrypted protected content.

Initial implementation scope: original published native AppWorld runtime plus an explicitly authored model API bridge; protected bundles remain encrypted in image and result artifacts. Authored wrapper/cache tests33PASS2.04seconds; missing lifecycle file was caught by actual synthetic stdin/process regression and corrected, then22wrapper testsPASS0.13seconds. Source-only HTTP7PASS/0FAIL with native SKIP/model NOT RUN. Template conformance PASS; public Markdown179documents0link failures; both new records2documents0link failures; actual bilingual Python snippets syntax PASS. Full frozen hash lock resolved84packages. Initial strict parser rejected an unsupported inline pip --only-binary flag; equivalent scoped PIP_ONLY_BINARY environment retains wheel-only install and all hashes without weakening the checker. Native image/Express/model/evaluator still NOT RUN.

Full specification57PASS13.249seconds; strict all-template0violations; complete wrapper/archive/cache/wire regressions60PASS35.96seconds at preparation ca04fb13a489401bf365d1d87c7a2dc438cdae25. Runtime bootstrap invokes the original private-package installer in a separate interpreter before first engine import, preserving original app discovery semantics. No native/runtime pass is inferred.
