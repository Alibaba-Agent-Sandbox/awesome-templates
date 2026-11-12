# Verification: final Server image and local real-model workflow

Date: 2026-11-12. Template product tree:7b0ef9c63cd971949e1a024b37f9f1b0877d1cbe.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.
This independent supplement preserves the prior c550 Server/Guest image baseline and owner
source-reader evidence. It changes engineering records only; no recipe, dependency or runtime
configuration changes accompany it. Results below are attributed to the runtime owner and
parent's actual retained executions, independently read by this template owner.

## Final local Server image

PASS: the unchanged final Server Dockerfile SHA256
f13427c5c0bac4f04799775823f0c1ed09e35bfe26d8ceed4a566b3a52c16145 installs the immutable
SDK b988d2a76057b6202d836ec329cc0bd90a572b26 archive with SHA256
abefcb1f16d7c87089d9d560d4f8ebd5787a140351553b84f970a171fdd18f68. Actual cached Docker
build exits0 in17.87 seconds and produces image
sha256:e6bfd49db465de1282a37829f82e68f4dd93f2528dd6dfc21c24003ab7239413.

PASS: an actual non-root, network-disabled container checks source provenance, instance TTL
and private env handling, actual yamlcore0.1.1 with13 positive/25 negative raw cases, and
native payload mapping through explicitly in-process infrastructure fixtures. Actual
authenticated loopback HTTP and temporary SQLite exercise Session create/get/list: public
timestamps use integer epoch seconds, true required_actions/vault_ids arrays are present,
and stored clock precision stays unchanged. A separate offline container runs pip check.
The probe is not a real FC or native cloud infrastructure call. See the self-contained
[final Server result](2026-11-12-agents-api-final-server-image.json).

## Two-turn real Qwen task on the unchanged Guest

PASS within local scope: one controlled95.36-second Docker invocation uses the previously
built Guest image sha256:331c2b4d31dbea9e1b827fab9defa3eacae7681cb3e9c6fb1b55e48390ab9df3,
Qwen Code0.23.0 and the existing real Chat endpoint/model qwen3-coder-flash. This reuses the
Guest; no new Guest image or package change is implied. Both authenticated private-bridge
turns complete with stop confirmation,12 and10 terminal-turn tool items, and zero artifact
capture errors. The parser's mcp_call label identifies Qwen tools, not generic Gateway MCP.

Turn1 repairs the supplied Decimal CSV program and produces totals30.00/10.00. Turn2 reads
the prior summary and adds shares0.7500/0.2500. The first summary hash remains unchanged;
continuity.json records that hash and the40.00 aggregate. Both downloaded program versions
run independently in a separate network-none container, reproduce fixed-input totals, and
the final version reproduces shares/continuity. A subsequent independent network-none
verifier runs the original three unmodified tests against each downloaded code version:
3+3 pass. Test-source SHA256 is6572f0585e3be203aa51a624834b4da96cf0ccc7532de3c00bdf2638e3d81270.

These are the same bridge Session/workspace; Qwen's native CLI resume identifier was not
independently captured. Second-turn wire event counts contain replayed first-turn history;
tool counts come from each terminal Turn's items and are not replay counts. See the
[typed business, artifact-hash and independent-test results](2026-11-12-agents-api-local-qwen-two-turns.json).
Raw model request/response, credentials, model stderr and one-off execution drivers are not
copied into this repository. Result-file hashes identify the retained original typed sources.

## Source acquisition and canonical identity

PASS: actual built CLI f26f789e98ab84ab1aa2504dce62cd996cf2197b executes template init from
the exact public7b0ef9c source. All14 source files match byte for byte, resource is present,
and publication metadata is optional. Exit0 in2.07 seconds. This only obtains source; it
runs no build, deployment or model. See [source acquisition](2026-11-12-agents-api-v1-source-acquisition.json).
Canonical schema/normalizer/requirements bytes remain identical to ef695803cb78bf82b8473195fcb37b3e6357a363,
as separately checked and recorded in [owner consumer/merge evidence](2026-11-12-template-v1-reader-consumers.md).

## Cleanup, boundaries and owner record checks

PASS: final Server probe/pip containers and all three model/output/original-test verifier
containers use --rm with finally cleanup; independent task-label listings report none remain.
The existing Guest and final Server images remain for this one parent task. No ACR push,
new cloud Sandbox, FC deployment, RDS, Codex attempt, retry matrix or global Docker change
was performed for these checks.

This is actual local Docker plus real-model evidence, not joint final Server-to-Guest FC/cloud
E2E. Final application credential routing, FC ingress and permissions, upgrade/old-session
routing, concurrency, SSE, every API method and other models/providers remain outside this
record. It does not grant current-template/provider qualification or announce a package
release. Source distribution metadata still says0.4.0a7. The image/runtime and source-reader
results do not replace the latest remote CI gate.

Owner record-only checks: `python scripts/check_docs.py`, `git diff --check`, JSON decode and
retained-artifact hash/provenance consistency checks. Full product suites are not rerun for
this evidence-only increment; their exact prior results remain in the owner consumer record.
