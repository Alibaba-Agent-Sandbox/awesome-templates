# OCR source verification — 2026-10-16

Result: PARTIAL — source checks pass; actual image/cloud/canonical gates remain pending.

Scope: independent OCR branch based on Pi commit `a361f490555ead0ff67081ffb4874abf292a1b2f`; [Issue 57](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/57). No OSWorld/Aider runtime changes are included. This is source evidence, not an image/provider acceptance claim.

## Actual dependency observations

Official tagged Tesseract 5.5.0 README/manual confirm the CLI syntax and simultaneous `txt tsv` output. Signed Debian 13 package metadata identifies Tesseract/libtesseract `5.5.0-1+b1`, eng/osd `1:4.1.0-2`, and Leptonica `1.84.1-4`. A private native prefix used SHA256-verified distribution packages extracted without host apt installation. Initial version execution failed because additional libarchive/libgif runtime dependencies were absent; that failure is retained as dependency discovery, not a pass. With those official dependencies extracted, actual `--version` returned Tesseract 5.5.0 / Leptonica 1.84.1 and actual `--list-langs` reported eng/osd. Seven packages totaled 7,901,708 bytes. Pillow 11.3.0 binary installation used the committed official PyPI wheel hash list; no shared dependency was replaced.

## Results

| Check | Actual result |
|---|---|
| OCR scoped pytest with OCR_TEST_REAL=1 and private real engine | 27 passed in 7.36 seconds |
| Source HTTP with E2E_REQUIRE_OCR=1 | 19 passed, 0 failed, 0 skipped |
| First scoped pytest attempt | 24 passed / 2 failed: synthetic executable fixture Python newline escaping, not OCR engine failure |
| Corrected fixture rerun before final UTF-8/resource coverage | 26 passed |
| All-template strict checker | 19 conformant directories (18 products plus scaffold), zero failures |
| Spec tools | 22 tests passed; mocked deploy/error cases are spec-unit controls, not cloud runs |
| Scoped relative links, JSON/fixture SHA256, diff whitespace | Passed |
| Actual image L1 | Pending remote CI; no local Docker |
| Supplemental changed-image Express | Not run |
| Canonical abx template deploy / express_e2e L2 | Not run |

The final real-engine pytest command sets OCR_TEST_REAL=1, operator binary/data paths to the private extracted engine and its library path; pytest runs only `ocr/test_commands.py ocr/test_http.py`. All subprocess cleanup regressions use actual owned processes and descendants, including success/nonzero leaders with redirected pipes, deadline TERM ignorers, Python cancellation and a foreign-group survival control. Synthetic executable tests observe private argv/environment and actual inherited rlimits, overflow/error handling and artifact permissions; they do not count as OCR acceptance.

Source HTTP starts the actual shared SDK server with original HOME, a disposable user-owned workspace and synthetic authentication, then invokes `ocr/e2e_test.py` with native OCR required. It checks real version/Pillow, packaged smoke, fresh high-contrast random-digit PNG recognition, exact recognized words, independently downloaded TXT/TSV bytes/hashes/confidence/geometry, unchanged original image, zero-word blank image and owned artifact deletion. A literal result marker alone cannot pass. The fixed fixture image is original rendered text, accompanied by its SHA256/generator manifest; no font binary is redistributed.

## Boundaries

Runtime is English-only, one image per request, fixed PSM 6, with no OCR network/model use. Original input/HOME are preserved. Input/output/process bounds and intentional retained result artifacts are documented in both READMEs and design. General authenticated shared-server APIs remain broader than the named OCR path checks. Deliberate setsid escapes and abrupt server SIGKILL are not claimed to be cleaned by Python finally. Docker/image pins must be observed in an actual non-root L1 run; source-native success is not that evidence. Keep tested_on empty, catalog experimental and the PR draft while canonical deployment gates remain incomplete.

No credentials, private cloud identifiers, signed URLs or raw native diagnostics are stored in this record.

Commands: `python scripts/check_template.py --all --strict`; `python scripts/test_spec_tools.py`; `OCR_TEST_REAL=1 python -m pytest -q ocr/test_commands.py ocr/test_http.py` with private native dependency configuration; source HTTP controller launches `ocr/e2e_test.py` with `E2E_REQUIRE_OCR=1`. First strict/spec execution reported README heading/explicit-POST and pip-pin readability violations; translated headings, explicit POST and explicit Pillow pin now pass without changing the checker.
