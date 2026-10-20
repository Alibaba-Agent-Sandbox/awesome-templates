# Decision: Official Goose CPU CLI with explicit compatible-provider tools
Status: proposed

## Problem

Issue49 needs the actual AAIF/Block terminal agent with reproducible Linux assets,
headless calls, preserved operator config and genuine Express/model proof.

## Decision

Pin official1.54.0 CPU GNU assets by release byte count/SHA256 and exact source
cd643d2126fffab4c6a6186905211ba868d6a657. Use official stdin/no-session/no-profile
flags, private Goose/HOME/XDG state, compatible OpenAI provider, default chat with
no tools and explicit developer-tool enablement. Retain license and non-root app.

## API Design

Version/setup/goose commands. Typed bounded stdin/cwd/tools/timeout; explicit
model config at process startup, no prewarm create-env assumptions. Return native
stdout/stderr/nonzero status;256KiB per stream,20 turns, owned unreaped group
cleanup. Operator-selected model settings alone enter native child environment.

## Alternatives considered

Floating installers and secondhand argv are unsuitable. The old survey's GNU
byte count differs from the official current asset80909320; record the official
release digest and verify downloaded bytes. The unchanged binary reports plain
1.54.0, without a goose prefix. Default auto tools would exceed intended readonly
behavior. Default chat really advertises no tools in the native protocol fixture.

## Dependencies

Official release/source and license, FC base, pinned SDK/server, compatible model
account. No desktop, GPU, KVM or Docker daemon. No new SDK/CLI contract.

## Test Strategy

Actual native CLI plus local HTTP fixture (not a real model), source/API type and
isolation/process regressions, exact image assets/non-root workspace, actual
Express and strict real-model artifact/original-test/held-out workflow. No source
or fixture result qualifies a provider. Preserve independent owned cleanup.

## Acceptance criteria

Complete template/catalog/bilingual/design/license/records, relevant local and
current-head CI, genuine Express and required real model with exact hashes and
owned cleanup, normal verified merge before Issue49 closure.
