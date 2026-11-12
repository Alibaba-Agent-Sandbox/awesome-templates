# Decision: Give local identifier patterns strict cross-language end boundaries

Status: proposed

## Problem

Actual Python jsonschema accepted a template name ending in a single LF because Python's
regular-expression dollar anchor matches before that final newline. Actual Node22/AJV8 and
native JavaScript already rejected the same input. Identical shared schemas therefore gave
different admission results at a local resource identity boundary.

## Decision

Replace the terminal dollar anchor with the portable strict `(?![\s\S])` boundary only for
existing ASCII identifier patterns: resource/Registry names, Provider IDs, service/resource/
profile keys, local references and environment-variable names. Retain their current lengths.
Native template.reference and image values retain Provider-owned identity length/semantics.
Expressions, JSON Pointers, relative paths and volume paths are not swept into this change.

## Alternatives considered

Trim input silently: changes identity. Depend on each consumer to repeat local-name parsing:
keeps cross-language disagreement. Use language-specific fullmatch or regex flags: makes the
shared JSON schema mean different things. Apply an ASCII rule to every string: rejects valid
paths, native IDs and expressions beyond the demonstrated defect.

## Dependencies

Independent CLI and parent review confirmed the semantic identifier scope. Tracker:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309. Consumers synchronize
the new producer after their ongoing full checks; no source copies change concurrently.

## Test Strategy

Shared LF/CRLF negative vectors cover all changed identifier classes. Actual AJV and Python
jsonschema must produce identical complete outputs. A positive long native reference proves
this does not impose a63/128-character limit on platform IDs; resource name63 remains valid.

## Risks and Limitations

This corrects literal identifier admission, not arbitrary native API validation. Node was
already rejecting the reproduced root-name case; no new Node vulnerability is claimed.

## Rollback Plan

Revert the isolated schema/vector change with coordinated locks. Never normalize an invalid
identity by trimming it or rewrite previous provider acceptance receipts.
