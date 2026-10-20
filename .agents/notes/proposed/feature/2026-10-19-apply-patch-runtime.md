# Decision: Use the official pinned native Codex apply_patch entry
Status: proposed

## Problem

Issue60 requires real Codex patch syntax and a reproducible upstream reference without shell interpolation or a heavyweight in-sandbox Rust build.

## Decision

Use the official npm0.162.1 prebuilt native package with locked integrity and verified version. Its upstream tag points to source092d3acd6bec3e3a14bdc7e7a2810ab628ab759d. Dispatch the supported apply_patch argv0 alias with private file stdin. Keep upstream license/metadata.

## API Design

Structured upstream stdout/stderr/nonzero exit_code, relative selected WORKSPACE directory, full path preflight, bounded patch/output/process group lifecycle. Additional version and actual byte smoke commands require no model.

## Alternatives considered

A floating source commit or shell replacement is irreproducible. Compiling Rust consumes build budget without changing the official shipped parser. A Python reimplementation would silently differ from upstream. Official prebuilt provenance is identified honestly, without claiming a local source rebuild.

## Dependencies

Locked official packages and native architecture asset, SDK/server and PR121 source-step adapter. No new SDK contract or model account. Issue60 remains open until actual cloud/image/merge gates pass.

## Test Strategy

Actual local native parser/HTTP/files bytes; path/symlink rejection and real process descendant/timeout/output bounds; exact image version; actual Express deployment and external HTTP, owned cleanup.

## Acceptance criteria

Complete bilingual contract/design/licenses; actual source/image/provider acceptance; current-head CI and ordinary verified merge. Retain failures; no inference/model claims.
