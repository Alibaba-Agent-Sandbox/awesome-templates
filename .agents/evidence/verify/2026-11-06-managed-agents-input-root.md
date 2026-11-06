# Managed coding example attachment-root regression

Date: 2026-11-06
Result: PARTIAL

## Verified defect and boundary

The new existing-source example at `ce09b53c89fdd780a6cdc9c0e1d26a14726be10d`
used `/workspace/agents-api-demo/input/sales.csv` as the Gateway attachment target.
The managed Gateway contract accepts paths under its configured workspace's
`input/` directory; this profile fixes the workspace at `/workspace`. The example
would therefore be rejected before model execution.

An independent runtime reviewer confirmed the supported contract. A real local
ManagedService admission probe, using temporary explicit SQLite state and no
Worker/Provider/model, observed:

| Submitted attachment path | Actual result |
| --- | --- |
| `/workspace/agents-api-demo/input/sales.csv` | HTTP400, `invalid_path` |
| `/workspace/input/sales.csv` | HTTP201 with a submission receipt |

The temporary local state was removed. This is an actual admission-path check,
not an FC or model business result.

## Correction and regression

Template0.1.2 sends the attachment to `/workspace/input/sales.csv` and names that
same input in both Agent turns. Existing source and original tests remain under
`/workspace/agents-api-demo`; the runtime allowlist is unchanged. Both README
languages explain the supported input location. Seed-source/original-test bytes
and the independent checker hashes are unchanged.

The regression asserts the outgoing attachment and both turn prompts against the
supported Gateway path. Added to the original smoke, it failed on the actual
nested path; after the correction all7 smoke tests pass. Independent current
manifest/schema tests52, checker48 directories, documentation232 and focused local
managed/legacy startup checks pass in the accompanying integration record.

Fresh public-package image, actual FC/model task and full independent cleanup
remain required. No cloud resource or model task was created by this regression.
