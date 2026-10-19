# Decision: Pinned polyglot compilation runtime
Status: proposed

## Problem

[Issue62](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/62) requires missing compilers under the Express rootfs limit.

## Decision

Install one verified official Go, Rust and Temurin distribution per architecture. Actual three-language compilation and artifact cleanup are canonical smoke; enforce8GiB actual used-rootfs budget.

## API Design

Parameterless toolchain_versions and toolchain_smoke return structured actual results. No caller shell/code input. No public SDK contract changes.

## Alternatives considered

Runtime downloads make agent turns unpredictable. Rustup/multiple versions waste rootfs. A fake version string or shell-only probe cannot certify compilers. Keep all three only after actual space and compile acceptance.

## Dependencies

Official upstream pinned hashes and licenses, gcc system linker, shared server SDK; source steps preparation from PR121. Tracking Issue62 remains open until merge and genuine Express receipt.

## Test Strategy

Keyless L0; true image pins; actual compiler outputs and owned cleanup in Express. No model needed. Each failed cloud attempt remains separate.

## Acceptance criteria

Spec/docs/local checks, actual three-language image/Express compile, disk budget, receipt, current-head CI and ordinary verified merge.
