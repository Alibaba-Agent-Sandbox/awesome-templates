# Verification: native Media argv final runtime

- Date:2026-10-20
- Result:PASS for the runtime/source/actual Express scope; final current-head CI must pass before merge.
- Runtime source:64de1c909659f880f79f69db42614277bfdf1257; Media1.1.0.
- Server source:fd72d3210b85079d93dcf08e19bfded73643162b; SDK foundation
  [PR78](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/78) merged as
  a1217af7e69c30557e5c8204002a23ac7c25727c, Issues76/77closed.

## Actual provider results

[Native steps](../../../media-tools/evidence/full-http-steps-2026-10-20T131812Z.json):
official READY, actual Python Sandbox.create, CLI/SDK smoke,28HTTP PASS/0FAIL/0SKIP,
exact source/pin/input hashes and independent owned template/sandbox absence.
The separate[step argv controller](../../../media-tools/evidence/native-argv-steps-2026-10-20T131812Z.json)
passes actual CLI JSON-array FLAC conversion, SDK array WAV decoding, independently
read artifact SHA256,16000random PCM sample equality, unchanged original spaced-name
upload and independent own-file absence. It borrows the sandbox; the outer receipt
owns cloud cleanup.

[Actual immutable image](../../../media-tools/evidence/express-2026-10-20T133417Z.json)
from[explicit export run39428636878](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39428636878),
artifact12267047668, passed actual SDK creation, CLI/SDK smoke and all28HTTP checks.
The[separate image argv workflow](../../../media-tools/evidence/native-argv-image-2026-10-20T133417Z.json)
passes the same independent byte/sample/cleanup conditions. Registry visibility,
pre/post-runtime tag digest and independently confirmed sandbox/template/registry
cleanup are preserved in the[image proof](../../../media-tools/evidence/image-http-2026-10-20T133417Z.json).
No old1.0receipt is promoted to1.1and no model is required.

## Source and CI

59actual native/authenticated HTTP cases PASS;55image/archive/step pin regressions
PASS;56spec-tools cases PASS; strict whole-catalog checker and150Markdown documents
pass. The original PR head's full L1 image matrix passed. Its single actual local
smoke failure reproduced array-to-string metadata because that job still installed
the historical common server. Only the local verifier SDK checkout is updated to
the merged immutable array implementation; existing image runtime pins remain
unchanged for every other template. The actual local Media runner then passes all
28HTTP assertions with the new server. The final current-head complete CI matrix
remains required before ready/merge; no assertion is relaxed.

## Commands and limits

`python -m pytest -q media-tools/test_commands.py media-tools/test_http.py`;
image/archive/step pytest suites; `python scripts/test_spec_tools.py`;
`python scripts/check_template.py --all --strict`; `python scripts/check_docs.py`;
actual SDK-created image and full native step controllers. Exact transcripts
exclude credentials; failures and original1.0history stay in their own records.

The offline argv option subset and additive transcode_args name preserve the
existing preset API. stdout/stderr/nonzero results are real FFmpeg output;
validation/probe/deadline failures retain errors. Outputs remain bounded and
no-clobber; arbitrary flags, network/device inputs and arbitrary paths are refused.
