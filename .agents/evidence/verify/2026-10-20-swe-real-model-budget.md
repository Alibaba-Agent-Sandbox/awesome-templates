# SWE controller operating budget verification

Status: PARTIAL; canonical corrected-controller rerun pending.

Actual owned Express diagnostic: mini2.4.6 exit0, Submitted after25 model calls. Independent evaluator:60 passed,0 failed/errors/skips, exact1 FAIL_TO_PASS and59 PASS_TO_PASS identities, resolved_slice true and official_benchmark_score false. Owned run-workspace cleanup and independent sandbox/template/registry cleanup confirmed. The diagnostic pipeline deliberately reported FAIL/not acceptance; it does not certify the corrected public controller.

A new HTTP-controller regression first failed against the old implicit12-step/300-second request, then the corrected protocol suite passed12 cases. The original key/explicit-off/false-green/identity checks remain. Runtime/Docker/manifest bytes are unchanged, so the reviewed exact image is revalidated and reused; actual public-controller/model acceptance follows separately. No local generated-shell attempt is promoted: an erroneously selected host replay was interrupted and its launcher disabled; real generated-shell testing remains in freshly owned cloud sandboxes.

## Native protocol correction

FAIL retained: strict budget-only repeat on1.0.1 still returned8 PASS/1 FAIL/0 SKIP before Submitted; independent sandbox/template/registry cleanup all true. The final trajectory was not captured, so its exact failure reason is unknown. A separate successful diagnostic contained5 format recoveries, motivating support for the actual upstream2.4.6 native protocol without treating that as the last failure's diagnosis.

PASS regression: an actual installed mini2.4.6 with an authored deterministic local HTTP tool-call fixture failed before the native-protocol change, then advertised the real bash tool, executed the literal submit action and submitted in one call after it. This is local protocol evidence, with no generated shell or real-model call on the operator host. Actual upstream Unicode/stdout/stderr/nonzero and fatal-timeout/owned-child controls also PASS. All34 command/protocol source cases PASS. Runtime1.1.0 requires a fresh image and genuine owned-cloud model acceptance; no old image qualification is carried forward.

Final source negatives also verify invalid protocol refuses before workspace mutation and text-only profile cannot pass native-model acceptance.36 command/protocol cases, strict25 catalog templates plus skeleton,126 document links/0 failures and whitespace PASS.

## Genuine current-version acceptance

PASS: fresh1.1.0 image artifact12252206363 from successful exact-source workflow39396296009 at0f44f638e8046291d4d19da8b7b6ca1cc1627462. Actual archive/config/runtime/context hashes, official native registration READY, Python SDK Sandbox.create and CLI/SDK smoke verified. Actual mini2.4.6 native bash-tool calls with compatible qwen3.8-flash completed strict14 PASS/0 FAIL/0 SKIP: genuine original1-failure/59-pass baseline, real source edit/Submitted, fresh independent60 PASS exact original identities, patch/report retrieval and owned run cleanup. Sandbox/template/registry cleanup and post-runtime digest independently true. Model controller2843a09f3e40032350e9756af21ca16819f5350610aabd216e761040910ad518; runtime commands e813fcf1ab3f424e5907cc7fb07d96c877f781bd0c2e6ea27e9fb6647a88a796. No official benchmark score/full official Docker harness claim. Earlier failed1.0.1 budget repeat and local disk-space preflights remain failures. No resource intent was created by the latter; false cleanup flags are not changed into passes. Normal current-main integration preserved both note/index entries and historical evidence; final-head CI/merge still required.
