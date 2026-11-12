# Decision: Validate Provider runtime inputs only after native resolution

Status: proposed

## Problem

Real Provider descriptors validate actual typed runtime inputs. Calling them during authored
intent normalization rejects valid native numeric expressions and can trigger discovery work
before the native parser has produced execution values.

## Decision

Invoke optional Provider prepare/create validation callbacks only at the resolved stage in
both canonical normalizers. Keep actual canonical schema and semantic intent checks active.
Unknown plugins still require an actual descriptor for resolved execution.

## Alternatives considered

Teach each runtime descriptor a second expression syntax: duplicates native Devs parsing.
Drop runtime validation entirely: permits unsupported executable inputs. Change only CLI
call sites: leaves Python and other contract consumers with inconsistent meaning.

## Dependencies

Independent CLI and SDK review confirms this boundary. Consumers synchronize this producer
revision. Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Shared vectors prove expression intent bypasses a rejecting runtime descriptor. A focused
regression records zero callback invocations at intent and an actual rejected invocation at
resolved stage. Existing successful real-schema fixture, unknown-plugin rejection,
asynchronous-callback and error-redaction checks remain.

## Risks and Limitations

Intent validity is not Provider acceptance. The CLI must still resolve native expressions
and execute selected runtime validation before any external effect. No cloud calls performed.

## Rollback Plan

Revert this isolated producer change and synchronize consumer locks; do not change historical
acceptance or pretend expression intent has become a literal execution configuration.
