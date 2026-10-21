# Decision: pinned original Cursor Agent native template

Status: proposed

## Problem
Issue63 predates an immutable official installer version and requires a real original CLI program/API path, not just package presence. Current vendor credentials are unavailable; authentication-dependent model success cannot be inferred.

## Decision
Implement a standalone template using unchanged official2026.10.19-6bbf2c4 Linuxx64 archive with exact controller-measured SHA256, original bundled Node/launcher and third-party notices. Bound named-command arguments/output/processes, contain workspaces, use private per-call state/minimal environment, disable updates/project configuration through verified original flags, and require explicit permission opt-in for native automatic tools. Preserve absent-credential and vendor authentication failures.

## API Design
Typed scalar agent(prompt,cwd,command_timeout,allow_unsafe_tools,model), agent_version, agent_native_check and presence-only agent_setup_check. Original native owns inference and tool execution; no replacement agent or compatible-model fallback. No cloud/operator key inherited by the native program. Missing CURSOR_API_KEY fails before interactive login.

## Alternatives considered
Piping the mutable installer to a shell is not reproducible. The versioned official archive is183733394bytes/SHA256cf80cc18d8b33bf33e762353977ca1868cfc45290c92c0ffdcef83bb8b37b44f. This digest is controller-measured, not a vendor-published checksum. Initial Python-UA download/guessed checksum sidecars403 do not prove absence; the official installer's normal curl client downloads successfully, and its User-Agent/Range probe is206. Bypassing authentication or substituting another planner would not validate original Cursor.

## Dependencies
Original official immutable archive, original per-file hashes/notices, pinned public server SDK34e7e011c5569f77b7f605e65313be7498f6cf02, owned Express and optional vendor CURSOR_API_KEY. No key is available for authenticated coding tests. Cursor vendor terms apply separately from Apache-2.0 authored template code.

## Test Strategy
Authored argument/metadata/process/HTTP fixtures locally; original native only in an owned cloud research run first. Then published-source native steps, real SDK create/named API including original invalid-credential path, full HTTP, actual non-root image, exact pins/size and independent owned cleanup. Real-model source edit/original tests/report/nonce/held-outs only with a genuine vendor credential, otherwise explicitly NOT_RUN.

## Acceptance criteria
Complete standalone source, fixed hashes/notices, bilingual14-section docs/design/catalog, tests and scoped records. Required local/image/current native steps/actual program/API/cleanup/latest-head CI/review/normal merge pass. No account/model/other-provider claim from missing credentials, mocks, version output or research alone.
