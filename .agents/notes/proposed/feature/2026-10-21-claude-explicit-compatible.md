# Original Claude explicit compatible text/tool transport

Status: proposed

## Problem
Issue15 lacks current original-CLI/model acceptance; approved Chat/Responses credential cannot be sent to an unapproved vendor. Actual approved Messages route404. Existing legacy command API must remain compatible.

## Decision
Add claude_byok alongside unchanged legacy claude API. Use original integrity-locked2.0.76 tool/planning engine with narrow authored Messages/Chat text/tool adapter. Explicit approved base/key/model only, isolated bounded owned per-call state and minimal child environment. No upstream vendor support/Claude model/subscription claim. Preserve original artifact terms.

## API Design
Three scalar args prompt/cwd/command_timeout, bounded nonempty text/contained existing project/integer1..600seconds. Return validated native success/final/actual counts and identity, no transcript/private data. Presence and original hash/help checks. Existing six-argument claude JSON-string interface remains.

## Alternatives considered
Direct approved Messages route404; forwarding existing key to default vendor violates origin scope. Replacing native CLI planner/tools is not upstream acceptance. Full translation of thinking/images/delegation/MCP is outside this bounded text/tool profile and fails closed.

## Dependencies
Official npm2.0.76/SHA512 lock/original cli.js SHA256; upstream restrictive terms and bundled attribution; Alibaba baseNode20; server34e7e011c5569f77b7f605e65313be7498f6cf02; explicitly approved Chat model. No new Python dependency.

## Test Strategy
Fixed metadata protocol and authored subprocess fixtures locally; original native synthetic and actual coding only on fresh owned Express; native SDK lifecycle/named commands, original tests/held-outs and exact artifacts after return, independently confirmed own cleanup, image and strict/spec/docs/latest CI.

## Acceptance criteria
Current original source/image/SDK native Express HTTP/model and cleanup pass without skip, bilingual contracts/design/records agree, immutable failures retained, latest reviewed head CI passes and normal pinned merge/Issue criteria read back. Until then current1.2.0 stays unqualified.
