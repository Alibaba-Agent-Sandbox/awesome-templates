# Verification: OCR Express resources

Result: PARTIAL. Actual prior image transfer/digest/private-registry verification passed; native template create returned an ID but official state ERROR before sandbox create. Provider reason was CPU2/memory1024MB ratio0.5, below minimum1. Independent template absence and both registry tags/repository absence were confirmed. Failed receipt is retained. Source changes CPU to1 and retains memory1024MB; cloud rerun and CI remain pending.

The checker now rejects the actual2-core/1GiB counterexample, out-of-range
ratios and non64MiB memory. Correct1-core/1GiB and2-core/2GiB controls pass.
This implements the official FC CreateFunction resource contract.
