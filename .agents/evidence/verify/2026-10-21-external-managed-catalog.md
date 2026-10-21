# External managed catalog verification

Status: PASS for catalog/client-contract delivery; NOT_VERIFIED for live E2Bdesktop/OpenSandbox interpreter.

[Source/test provenance](2026-10-21-external-managed-source-tests.json), [actual SDK negative-path proof](2026-10-21-external-managed-sdk-negative.json). Published provider9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d extracted read-only into an isolated fixture; pre-existing dirty provider checkout was preserved. Initial exploratory tests there do not certify the published revision. Exact published rerun: OpenSandbox51PASS0FAIL0SKIP; E2B14PASS0FAIL0SKIP with actual E2B2.55.0SDK against authored localHTTP, npm-locked. No vendor/account/model endpoint was called. Original source pins/files/digests retained; no original image or binary committed.

Actual paired Agent SandboxSDK34e7e011c5569f77b7f605e65313be7498f6cf02: missing provider-specific E2B credential rejects before engine/network despite a fixed synthetic generic Express key; unsupported OpenSandbox native interpreter rejects before transport. BothPASS. The first pytest fixture used unavailable pytest-asyncio and failed2before running checks; replaced with stdlib asyncio.run, then2PASS2.46seconds without adding dependencies. This is test-harness correction, not a product failure or backend pass.

No independent E2B account is available; generic E2Bkey equals Express alias and was not forwarded. No configured usable OpenSandbox server; dated [default local HTTP probes](2026-10-21-other-provider-prerequisites.json) returned RemoteProtocolError despite TCPaccept. No cloud resources created by these client/mock contracts. No cleanup acknowledgement is fabricated; managed unverified receipts remain passed:false/cleanup_verified:false/native_interpreter_verified:false.

Reproduce after checking out the exact public provider commit to a separate fixture (do not use a dirty checkout):

```bash
E2E_PROVIDER_SOURCE=/path/to/pinned-provider-fixture python -m pytest -q docs/managed/tests/test_external_provider_contract.py
node /path/to/pinned-provider-fixture/opensandbox/tests/run.mjs
npm ci --prefix scripts/managed-contract-sdk --ignore-scripts --no-audit --no-fund
E2B_TEMPLATE_SDK_MODULE="file://$PWD/scripts/managed-contract-sdk/node_modules/e2b/dist/index.mjs" node /path/to/pinned-provider-fixture/e2b/tests/run.mjs
python scripts/check_managed_catalog.py
python -m pytest -q scripts/test_managed_catalog.py
```

The actual source/capability tests instantiate SDK objects and enforce refusal before transport; loopback fixtures exercise protocol behavior only. Source-template image/steps and native GUI/interpreter acceptance remain separate. New catalog checker regressions validate false-qualification/identity/cleanup/README/state and managed IDs excluded from source image dispatch. Final local spec/strict/document/AST checks and exact-head CI/review/merge recorded after execution. Issue34 real-backend gate remains open; a usable server was requested asynchronously while other work continues.

Executed local verificationPASS: managed checker0violations across4entries, managed/schema/image-selection43testsPASS3.38seconds (14managed-specific testsPASS2.25seconds);57specPASS36.089seconds;45existing source templates strict0violations;212public/3owner Markdown0link failures;4bilingual SDK examples AST syntaxPASS. Actual pairedSDK negative tests2PASS2.46seconds; published OpenSandbox51/0/0 and actual-E2BSDK14/0/0. No source runtime changed. Final diff/configured-secret scan and latest-head CI/review/merge remain required.
