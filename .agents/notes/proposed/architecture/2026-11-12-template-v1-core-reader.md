# Decision: Share a JSON-compatible YAML1.2 Core source boundary

Status: proposed

## Problem

The actual Node reader accepted unquoted on/date text as strings while Python SafeLoader
constructed booleans/dates from the same v1 document. That changes values or rejects a
valid source depending on the consumer. Replacing Python with a safe ruamel1.2 loader alone
still constructed dates and legacy numeric forms in actual probes.

## Decision

Add pure parseYamlV1/parse_yaml_v1 plus MAX_YAML_BYTES in the existing canonical modules.
Use actual Node yaml2.9.1 Core and Python PyYAML6.0.3+yamlcore0.1.1 scalar rules. The shared
policy bounds input to1MiB strict UTF-8, rejects raw control characters, aliases, duplicate
keys, unsupported tags, non-string map keys, nonfinite/unsafe numbers and multiple documents.
Allow no YAML version directive or explicit1.2 only. Unused anchors are harmless. Plain
merge-looking keys stay literal. Explicit str may fix a string; other scalar tags cannot
force a different implicit Core kind, matching the current Node warning/rejection boundary.

The wrapper does not replace scalar resolvers or evaluate Devs expressions. Python uses a
local CoreLoader subclass only to enforce alias/directive/explicit-kind policy through its
existing token and resolver APIs; existing SafeLoader behavior remains unchanged. File IO
belongs to callers, which read at most MAX+1 bytes. Parser errors never echo source text.

## Alternatives considered

Keep SafeLoader or patch its global resolver: retains mismatches or changes unrelated YAML
uses. Hand-maintain scalar regexes in three repositories: duplicates a standard and source
ownership. A bare ruamel safe1.2 swap: actual probes still turn dates and1_000/0b101/0x1_f into
date/numbers, unlike Node Core. yamlcore0.1.1 supplies the existing parser's proper Core rules
in a6055-byte MIT-licensed wheel, avoiding an alternate full parsing stack.

## Dependencies

The Python dependency is pinned in the owner's existing checker requirements. The Node test
lock pins the same actual yaml2.9.1 package already used by the CLI. Consumers synchronize
normalizer/schema/contract and yaml-fixtures.json from this exact producer commit. Only
public v1 template/Registry/catalog intake changes; other PyYAML consumers remain independent.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Run both real parsers over shared raw-text/byte vectors and compare complete results. Include
ambiguous scalars, quoted/explicit strings, Unicode/multiline/native expression text, duplicate
keys, tags, aliases, directives, unsafe keys/numbers, invalid UTF-8 and byte bounds. Test that
SafeLoader's unrelated behavior is unchanged and rendered exception context is source-free.
Keep all existing schema/default/private-compilation vectors active.

## Risks and Limitations

This is the v1 JSON-compatible Core subset, not every YAML tag conversion. Source parsing and
native Devs evaluation are different phases: a consumer must preserve input string types
when serializing its private project to the actual Devs parser. No runtime, cloud or native
API acceptance follows from source-reader parity. Existing Server/Guest image receipts remain
historical; this parser-only change does not alter their compiled-JSON runtime path.

## Rollback Plan

Revert with coordinated consumer source locks. Do not silently restore per-consumer scalar
conversion or rewrite old acceptance. Keep original mismatch evidence and source vectors.
