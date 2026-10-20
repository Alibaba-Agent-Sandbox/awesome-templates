# OCR 1.0.1 actual platform-step acceptance

Status: PASS for the executed cloud scope; publication checks follow below.

The source was b232ed7bb1d516154ec15e3b8ec8669c164a7f8b. Genuine native Express steps reached official READY. Both CLI and SDK ran `ocr_smoke` successfully. The unchanged controller SHA256 is 76012220e1d8e98b32295cc072e0dcf8edada48a297b803ed3dab84d29ac7de7.

- [Canonical step receipt](../../../ocr/evidence/express-2026-10-20T061143Z.json): exact input hashes, base, source commit and separately recorded server override.
- [Full external HTTP receipt](../../../ocr/evidence/full-http-steps-2026-10-20T061143Z.json): 19 PASS, 0 FAIL, 0 SKIP, exit 0 and independently verified sandbox/template absence.

Executed procedure: call `prepare_steps.prepare` with the recorded source/server commit, stage its manifest and proof privately, and invoke `express_e2e.execute` in steps mode with a unique owned alias and 1200-second readiness deadline. The SDK callback then resolves port 9000 with `Sandbox.network.get_url` and runs `python ocr/e2e_test.py` with `E2E_BASE_URL`, `E2E_BASE_DIR=/home/user/app`, `E2E_WORKSPACE=/home/user/app`, `E2E_RUN_LLM=0`, `E2E_REQUIRE_CLI=1` and `E2E_REQUIRE_OCR=1`. A nonzero controller exit or any skip fails this operation. Only after the canonical harness independently confirms cleanup are receipts published. Private logs, resource identifiers and credentials are excluded.

The public `python scripts/run_steps_e2e.py ocr --timeout 1200 --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a` reproduces step construction and CLI/SDK fixture smoke; it does not itself invoke the full HTTP controller. Its scope is documented explicitly rather than extending a passed receipt to an unexecuted operation.

Assertions cover random-digit image pixels, independently downloaded TXT/TSV contents and hashes, meaningful words, confidence/bounds, unchanged input, blank-image negative control and owned artifact deletion. No model/network OCR service is substituted. Prior merged image acceptance and failed step attempts remain immutable history.

Publication validation: strict25 catalog templates plus skeleton PASS;126 local Markdown documents,0 broken links; OCR strict check and git diff whitespace check PASS. No runtime/image rebuild is required for this evidence-only change. Latest-head CI remains a separate merge gate.
