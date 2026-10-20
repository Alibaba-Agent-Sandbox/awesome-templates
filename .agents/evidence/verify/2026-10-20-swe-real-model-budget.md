# SWE controller operating budget verification

Status: PARTIAL; canonical corrected-controller rerun pending.

Actual owned Express diagnostic: mini2.4.6 exit0, Submitted after25 model calls. Independent evaluator:60 passed,0 failed/errors/skips, exact1 FAIL_TO_PASS and59 PASS_TO_PASS identities, resolved_slice true and official_benchmark_score false. Owned run-workspace cleanup and independent sandbox/template/registry cleanup confirmed. The diagnostic pipeline deliberately reported FAIL/not acceptance; it does not certify the corrected public controller.

A new HTTP-controller regression first failed against the old implicit12-step/300-second request, then the corrected protocol suite passed12 cases. The original key/explicit-off/false-green/identity checks remain. Runtime/Docker/manifest bytes are unchanged, so the reviewed exact image is revalidated and reused; actual public-controller/model acceptance follows separately. No local generated-shell attempt is promoted: an erroneously selected host replay was interrupted and its launcher disabled; real generated-shell testing remains in freshly owned cloud sandboxes.
