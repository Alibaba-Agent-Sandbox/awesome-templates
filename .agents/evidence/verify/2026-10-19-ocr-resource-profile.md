# Verification: OCR Express resources

Result: PARTIAL. Actual prior image transfer/digest/private-registry verification passed; native template create returned an ID but official state ERROR before sandbox create. Provider reason was CPU2/memory1024MB ratio0.5, below minimum1. Independent template absence and both registry tags/repository absence were confirmed. Failed receipt is retained. Source changes CPU to1 and retains memory1024MB; cloud rerun and CI remain pending.

The checker now rejects the actual2-core/1GiB counterexample, out-of-range
ratios and non64MiB memory. Correct1-core/1GiB and2-core/2GiB controls pass.
This implements the official FC CreateFunction resource contract.

## Corrected actual Express result

PASS: original successful exact-source CI artifact12206998177/checkoutbb0f625f1325c07c1897fa725bff67bbb97efec5 revalidated, transferred using RAM-only temporary auth to nonce-owned private ACR. Actual1vCPU/1024MB native registration reached official READY, genuine CLI and SDK OCR smoke PASS, full external HTTP19 PASS/0 SKIP. Independent randomized pixels, TXT/TSV/hash/confidence/pixel bounds, original encoded bytes and blank negative control verified. Both tag digest readbacks match. Owned controller artifacts, sandbox/template and both registry tags/repository absence independently confirmed. Canonical and full HTTP receipts are in ocr/evidence. Failed resource and local-controller attempts remain distinct. Current-head CI and ordinary merge remain required.

Contract publication correction: the resource change must increment patch
version under the accepted project standard. Manifest is now1.0.1; provider
qualification is cleared pending its own genuine run. Prior1.0.0 candidate
receipts remain unchanged and historical, never relabeled. Fresh exact-source
image export and current-version cloud acceptance are required before merge.
