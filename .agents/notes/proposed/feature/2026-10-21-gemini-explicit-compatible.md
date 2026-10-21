# Original Gemini explicit compatible text/tool transport

Status: proposed

## Problem
Issue30 has no current real-model acceptance for original Gemini CLI. Existing approved Chat/Responses key cannot be forwarded to unapproved Google default. Keep public legacy API compatible.

## Decision
Add explicitly configured gemini_byok with original npm0.64.0 planner/tools and authored GenerateContent-to-Chat text/function transport. Preserve original449file identity and notices; private per-call launch/settings/tool environment/RPC lifecycle. No hosted model/account/vendor endorsement or full feature claim.

## API Design
Scalar prompt/cwd/command_timeout; bounded nonempty/contained existing/integer1..600. Return validated original final, package identity, actual positive completed transport/tool results and no raw transcript. Add native/check and BYOK presence-only setup alongside unchanged legacy calls.

## Alternatives considered
A Chat base alone is not native Google wire. Sending root key to default vendor violates origin scope; replacing original planner/tools would not verify original runtime. Full image/thinking/MCP/delegation compatibility is outside this bounded text/tool slice and is rejected.

## Dependencies
Official npm0.64.0 SHA512 lock/449file original SHA256 inventory, original Apache/bundled notices, baseNode20, pinned server34e7e011..., explicitly approved Chat model and stdlib adapter/process controls. No new Python dependency.

## Test Strategy
Fixed metadata protocol and authored subprocess fixtures only locally; preserve existing legacy tests. Original native synthetic then real source-edit/original tests/report/nonce/held-outs/freshACK on owned cloud only. Exact published steps/image/SDK/HTTP/cleanup and latest CI/review.

## Acceptance criteria
Current original source/native SDK Express/fullHTTP/actual model/independent cleanup/image pass, bilingual docs/contracts/records agree, immutable historical failures retained, latest-head checks/review and normal pinned merge. Until then current2.1.0 stays unqualified and Issue30open.
