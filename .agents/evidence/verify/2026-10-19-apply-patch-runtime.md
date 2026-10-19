# Verification: native apply_patch runtime

Result: PARTIAL. Actual official @openai/codex0.162.1 native argv0 entry accepted stdin and created exact proof42 bytes; upstream annotated rust-v0.162.1 tag resolves to092d3acd6bec3e3a14bdc7e7a2810ab628ab759d. Upstream Apache LICENSE SHA256d17f227e4df5da1600391338865ce0f3055211760a36688f816941d58232d8dc retained.

Real local HTTP L0 PASS: exact native version, add/update/move/delete/literal content, remote bytes via files API, malformed nonzero result, missing/undeclared/unknown/path escape rejection, owned file deletion/absence. Initial verifier incorrectly assumed SDK string arguments reject JSON numbers; official SDK intentionally uses str(value). Replaced that invalid assumption with actual missing/undeclared rejection, preserving upstream malformed-patch nonzero checks. No SDK bug/change claimed.

Actual image/Express/full external HTTP/current-head CI and merge remain pending. Local success is not provider evidence.

PASS:10 real parser/path/Unicode/descendant/deadline/output-limit regressions.
Strict target conformance and Markdown links117 documents/0 failures. Initial
uncommitted inline step payload exceeded15KB preflight and did not call cloud;
preparation after publishing exact source will hash-check immutable COPY input.
