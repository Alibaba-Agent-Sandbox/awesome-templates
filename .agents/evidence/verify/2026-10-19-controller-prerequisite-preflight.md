# Verification: Controller prerequisite preflight

Result: PARTIAL.24 targeted tag/archive/controller tests PASS, including a real missing-import discovery and a guard proving artifact/cloud transfer is not called. Original corrected OCR run reached official READY and actual CLI ocr_smoke PASS, but its local controller could not import PIL and ran0 external assertions. It remains a failed attempt; template/sandbox and registry were independently cleaned. Pillow11.3.0 is now installed locally; original verified CI archive is revalidated for a distinct rerun. No new provider PASS claimed from that preparation.

Merged baseline image flow has genuine Hermes acceptance: CLI/SDK,9 HTTP checks/1 explicit model skip, separate17 strict model checks/0 skips, and independently confirmed sandbox/template/registry absence. Public exact receipts in PR132. This fix preserves that workflow and records cleanup independently of controller status. New actual OCR/secondary-port checks and latest-head CI remain pending.

Combined source/tag/archive/cleanup/step regressions57 PASS plus18 subtests;
120 current-document links PASS. Additional changing-tag-after-runtime negative
control forbids evidence even when resource cleanup succeeds.
