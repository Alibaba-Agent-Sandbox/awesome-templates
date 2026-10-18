# Amp read-only inspection verification — 2026-10-16

Result: PARTIAL

Scope: amp commands, settings, image inputs, verifier, regression tests, bilingual README/design, catalog/CI and the Amp branch of the Express source runner. Changed version: 1.2.0. Python 3.13, actual Amp 0.0.1792022479-ge66e24 on Express. Issue #83 and PR #82 remain open.

## Executed checks

- PASS: `python -m pytest amp/test_commands.py amp/test_e2e_protocol.py -q`: 12 regressions. Real subprocess descendant cleanup, configuration bytes/mode preservation, explicit permission selection, missing-key guard, secret redaction and remote credential/disable decisions.
- PASS: `python scripts/check_template.py amp` and `python scripts/check_template.py --all`: zero v2 violations at the time of this run.
- PASS: `python scripts/test_spec_tools.py`: 20 tests.
- PASS: local HTTP suite: initial 8 checks before remote-disable correction; later full-catalog run includes the corrected verifier (model disabled separately).
- PASS: real Express source-runtime: version/configuration through SDK, settings bytes independently unchanged, 7 external HTTP checks, 1 explicit model skip; owned sandbox cleanup passed. [JSON](../../../amp/evidence/runtime-express-2026-10-16-readonly.json), [HTTP log](../../../amp/evidence/runtime-express-2026-10-16-readonly.log).
- PASS: clean server wheel SHA-256 `a09a4846fef8b49f3a059d1c65e38d283986aa4fbf879dd09192100c30039fc9`; all 56 Python modules matched clean SDK source `bb7881dc703ccdc3b97ff5ad67bcb129c4ea80ea` when built.

## Initial failures and review corrections

The first cloud run found an invalid `files.read(format=...)` diagnostic call; corrected to the real `read_bytes` API. A subsequent dependency installation RPC ended with UNAVAILABLE / Stream removed (Socket closed). Both runs destroyed their owned sandboxes. The runner now polls a bounded background installation with short RPCs; the resulting real run passed. No network or permission settings changed.

Independent OpenCode-agent review found controller/server credential confusion and a stale design argv. Both were corrected; regression tests explicitly reject a model request under forced-off verification and use remote key presence.

## Remaining gates

BLOCKED: no Docker daemon for L1/new image L2. No authorized Amp credential for real coding/model acceptance. The current version stays experimental with empty tested_on; unchanged 1.1.0 evidence is historical. The source-runtime success is not a provider image-acceptance qualification.
