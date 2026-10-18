# Verification: Source-runtime engine socket isolation

- Date: 2026-10-16
- Scope: one startup socket assignment in `scripts/express_runtime_e2e.py`,
  `scripts/test_express_runtime_socket.py`, and this engineering record.
- Result: PASS for local diagnostic isolation; original Droid cloud/model
  acceptance remains unpassed until a separate rerun.
- Environment: Python 3.13 on Linux; SDK source
  `fbe506349693f9bb26c1755aa3d13ce855e1ab69`. No credentials supplied.

## Observed failure and ownership

The earlier Droid source-runtime run observed E2009 for OWNED_SANDBOX while
polling a background installation with a configured 900-second remote TTL.
Inspection of the SDK engine shows no 80-second session expiry: sessions are
removed by explicit release/kill or disappear when the owning process exits.

Two native execs here exposed the same PID and selected the same PID-only socket.
The second process had an empty local SESSIONS map yet successfully called the
first process's synthetic session through the actual gRPC Unix engine. After the
first process exited, the borrower restarted an empty engine and deterministically
received E2009. All six negative-control checks passed. No remote sandbox was
created, and OWNED_SANDBOX is a synthetic marker, not a resource ID.

The older Droid run did not record engine ownership, so this proves the harness
bug and failure mechanism without claiming its exact historical exit sequence was
instrumented. No SDK source patch was made to mask the diagnostic collision.

## Patch and validation

The socket name now adds a per-run 12-hex-character random nonce from the existing
`secrets` import. No runtime choices, credentials, provider configuration or cloud
cleanup logic were changed.

| Check | Result |
| --- | --- |
| `python3 scripts/test_express_runtime_socket.py` before patch | Expected FAIL: two isolation assertions failed, path-length assertion passed |
| Same three tests after patch | PASS: 3 tests |
| Native exec actual gRPC shared-socket negative control | PASS: 6 checks demonstrate attach, owner exit and E2009 |
| Native exec actual gRPC patched-expression positive control | PASS: 5 checks; equal PIDs select distinct sockets and the second process's session survives the first process exiting |
| `python3 scripts/test_spec_tools.py` | PASS: 20 tests in 15.678 seconds |

Both native proofs used synthetic sessions and made no platform HTTP/WS calls.
Only their recorded local sockets were removed after the processes exited. No
arbitrary cloud resources, templates, sockets or process groups were cleaned up.

## Limitations

This is a local real-component concurrency verification, not Dockerfile L1,
template-deploy L2, Droid model acceptance or a provider TTL test. Existing failed
Droid runtime evidence remains failed; no `tested_on`, Verified table or catalog
acceptance was changed by this patch. A separate source-runtime rerun is needed
before claiming the original Droid workflow succeeds.

## Tracking

- [Harness issue 84](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/84) owns this fix.
- [SDK issue 35 investigation](https://github.com/Alibaba-Agent-Sandbox/python-sdk/issues/35#issuecomment-6207082564) records the corrected ownership and the historical-run limitation.
- Scoped diff and configured-secret scans passed before handoff.
