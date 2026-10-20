# Decision: official xAI Grok Build native coding

Status: proposed

## Problem

[Issue40](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/40) needs reproducible official native CLI, SDK/Express/steps/real coding evidence and complete bilingual docs. Old mutable installer survey is not current proof. Same-name community CLI is not the requested product.

## Decision

Pin actual official npm @xai-official/grok1.0.62 with full integrity lock and native SHA256, retain license/third-party notices, directly execute reviewed Rust native binary. Use supported custom model alias/env_key/chat_completions with an explicit approved base and separate model key. No vendor credential substitution or default endpoint fallback.

## API Design

Version/setup/grok(prompt,cwd='',command_timeout=300), scalar schema, bounded UTF8/path/time/output, actual exit retained. Fixed native headless JSON/coding tools/no-subagent/no-web/no-plan/sandbox-off, anonymous stdin via /dev/stdin; private HOME/config/session cleaned on every path. Argument containment is not tool authority confinement. Whole group/nonce/pidfd ownership and serialized calls prevent lifecycle replacement.

## Alternatives considered

Mutable curl installer cannot establish reproducibility; grok-dev is another project; marker-only or chat-only imitation is not native acceptance. Existing approved compatible endpoint can exercise genuine native model/tools without claiming xAI-hosted model qualification. No model-generated code on operator.

## Dependencies

Official1.0.62 npm integrity metadata/native binary SHA256; Node24.16.0; servere2cb27e. Public source snapshot2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 documents contracts but is not claimed as binary build1474f9cbdd91. Apache2.0/official third-party notices retained.

## Test Strategy

26local authored boundary/process/TOML/SDK serialization/terminal JSON controls, strict/docs/spec. Keyless native version/help provenance only. Actual L1 image and current SDK-created canonical native steps/full HTTP/model source/artifacts/preserved complete original tests/held-out post-return ACKs and all own cleanup before provider qualification/Issue closure.

## Acceptance criteria

Mandatory actual image/Express/native model/independent cleanup and latest-head CI/review/normal merge remain pending. Both language usage and immutable receipts must match runtime source. No unsupported hosted/subscription/desktop/provider claims.
