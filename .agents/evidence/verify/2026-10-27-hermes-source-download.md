# Hermes bounded immutable source download

Result: PARTIAL (local source/integrity regressions pass; actual reruns pending)

Date2026-10-27. Original source46b7c1ccc01eae9cf41292dde89ab32411ed5f79 failed
before sandbox creation: Docker build history confirms curl HTTP429 and incomplete
tar input. One image intent has no ID. Independent exact local absence/registry404,
no sandbox entries/active build/workload recorded in SHA-bound supplement; original
launch remains FAIL. No new model/business calls for cleanup reconciliation.

A bounded readonly official download obtained83225459 bytes with measured SHA256
fbd55e510b49592635429aa451a7c2b9fb4061cddbbab09f52504226f4338fcf. Exact Git blobs:
pyproject.toml5145f275d14a0ab119802821c715a33123b15551;
uv.lock765bf23d7c90461d60497e268932f518d880ea47;
scripts/write_install_stamp.py0a2745297bf4f18706a6a06c38dc024a6fe88850.
Fixed upstream297552a9d646119871391d202509822cd86330df. Not an upstream checksum.

Hermes download/command/protocol/canonical tests:110 PASS. Additional source-cache
compatibility PASS. Real HTTP tests cover429 recovery/count bound,403 rejection,
wrong checksum/partial removal/caller destination preservation and cached parity.
Spec39 PASS; all-template checker PASS;224-document links PASS. Runtime package,
Python3.14.6/uv0.12.3, upstream lock and licensing remain unchanged.
Secret/diff, final-head CI, fresh full actual Express/OpenSandbox public methods,
model tasks, literal CLI/full SDK/HTTP and independent cleanup are required before
current-source Registry qualification. No partial/build-only pass is inferred.
