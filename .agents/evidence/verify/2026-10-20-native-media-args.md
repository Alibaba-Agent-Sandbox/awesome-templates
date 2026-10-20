# Verification: native media argv and exact server source

- Date:2026-10-20
- Result:PARTIAL
- Scope: Media1.1 implementation, native codecs/HTTP and SDK-source integrity.
- SDK dependency: [PR78](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/78),
  explicit immutable commit in media-tools/server-sdk.commit.

## Actual local checks

Native FFmpeg7.1.5-0+deb13u1:58cases PASS. With the changed actual server/client,
59native/authenticated HTTP cases PASS10.12seconds. Native odd-sized YUV420/H.264
fails with actual nonzero exit and stderr, without publishing its output. Successful
argv conversion preserves spaced input and independently verified FLAC bytes.
Wrong/mixed array types fail400before invocation. Original presets remain covered.

Initial image/archive pin regressions35PASS; full step/source checks are rerun on
the committed source because safe archive materialization requires matching Git
bytes. One initially invalid fixture appended RUN after USER; it was corrected to
keep the real supported profile, without weakening the final USER invariant.
Local Markdown150documents/0failures; template strict checker0failures. The full
56spec-tools cases passed after moving historical1.0provider rows outside the
current1.1Verified section. This is metadata honesty, not new provider acceptance.

## Commands

`python -m pytest -q media-tools/test_commands.py media-tools/test_http.py` with the
actual changed SDK packages; image/archive/step pytest suites;
`python scripts/test_spec_tools.py`; `python scripts/check_template.py --all --strict`;
`python scripts/check_docs.py`. No model-generated work runs on the operator host.

## Pending gates

Current-head CI/image and actual SDK-created Express step/image, full HTTP,
separate native CLI/SDK array workflow and independent owned cleanup remain
pending. Version1.1tested_onis empty. Original1.0cloud receipts remain historical.
The borrowing array controller never destroys a caller sandbox; the outer harness
owns sandbox/template/registry deletion and independent absence checks.
