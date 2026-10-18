# Aider independent verifier — 2026-10-16

Result: PARTIAL. Tested base `9bcc1a1efac0e60520bf9b3b039ac9d0ca4b1360`;
only HTTP controller, regression fixtures, bilingual/design documentation and
repository records change. Runtime commands, Dockerfile, template YAML, catalog,
existing acceptance files and tested_on remain unchanged.

## Reproduced defect

PASS (reproduction): the original controller reported zero failed coding checks
with actual shlex/direct-exec subprocess exits `[0, 1, 0, 0]` (git setup, expected
baseline failure, original tests and skipped held-out process). Target source
handled only the original three inputs; its separate held-out import printed the
static expected text then exited zero. HTTP/model responses were synthetic. This
is not a real model result and does not invalidate the genuine historical model
run; it demonstrates a missing acceptance guard.

## Corrected local checks

PASS: paired review Python `python -m pytest -q aider/test_e2e_protocol.py
 aider/test_commands.py`: 72 tests, 14.28 seconds. New actual-process negative
cases include static-marker sys.exit, flushed marker then os._exit, exit before
original-test execution with fake test count, all original tests skipped and a
valid unchecked-hash cache hiding incorrect actual source. The cache control
first proves legacy import loads the good cache. Existing shadowed stdlib and
sitecustomize, missing marker, modified original tests and held-out failures remain
covered. No credentials/model/cloud are used by these regression fixtures.

## Pending

Strict/docs/normal remote checks and corrected actual-image model execution are
recorded after execution. Earlier 21 real model checks and exact image/source
provenance remain in the parent PR's evidence. They do not establish this new
verifier gate. Full canonical abx template deploy is NOT RUN and remains blocking;
no express receipt or tested provider claim is created.

PASS: strict Aider template checker, 20 local link targets and git diff whitespace.
The original exact static-exit reproduction rerun against the corrected controller
now fails held-out verification (one failed coding check, exit sequence0/1/0/1).
