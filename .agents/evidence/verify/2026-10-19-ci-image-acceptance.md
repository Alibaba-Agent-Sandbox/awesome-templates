# Verification: CI image acceptance

Date: 2026-10-19. Result: PARTIAL.

PASS: 54 targeted source/provenance/archive/cleanup tests plus18 subtests using
pytest on test_ci_image, test_ci_image_archive, test_express_cleanup and
test_prepare_steps. Synthetic registration fixtures do not establish cloud success.
Actual private-registry scratch preflight proved temporary RAM-only credential
inheritance, push, digest readback, private repository state and independently
confirmed owned tag/repository absence. It was not a template image acceptance.

Genuine exact-source exported OCR image verification is in progress. Full template
cloud outcomes and image-backed model acceptance are not inferred from these checks.

PASS:37 specification/controller tests, strict23-template plus skeleton conformance,
and116 current documentation links. HTTP verifier subprocesses use unreaped-leader
process-group cleanup on success and timeout. Hosted checks remain pending.

Fresh real OCR image transfer and native template create executed, but official
state ERROR rejected the original2vCPU/1024MB manifest ratio before any sandbox.
Independent owned template absence and both ACR tags/repository absence PASS.
The failed attempt is separate and OCR profile correction is PR130. Image
resource preflight now rejects this pair before artifact download/mutation.

Hosted CI exposed an existing SWE cleanup-test procfs race: /proc PID disappeared
between opening stat and reading it, raising ProcessLookupError. Treat that
confirmed disappearance like FileNotFoundError; the live/zombie checks remain.
No runtime/SWE image source change; actual cleanup regressions rerun.
