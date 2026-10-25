# Current runtime, command and documentation verification

Date: 2026-10-25
Result: PARTIAL; required image/cloud gates pending
Base: 26d6e24e8b29b6c73b364d954dc0279d22a6f9d5
Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221
Dependency: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/224

## Public packages and runtime inventory

The SDK owner reported public a3 publishing run 40209677091 SUCCESS. Independently created a fresh Python3.13 venv and installed client/server==0.4.0a3 from https://pypi.org/simple. Both importlib.metadata versions are 0.4.0a3; imports and pip check PASS. No source checkout or old package fallback entered that environment.

Inventory enumerated catalog source manifests plus _skeleton and every manifest build_profiles Dockerfile: 47 runtime manifests and 48 recipes, including python-hello/Dockerfile.portable. Each manifest increments its prior patch by one. All declared recipes now install published server a3 from the official index. Current docs/tool fixtures/CI host dependencies use the same package. No image or cloud pass is inferred from this static inventory.

## Canonical command boundaries

Calling search included --hidden and excluded Git internals and historical evidence/engineering notes. Four project wrappers were explicit old-name forwards and absent from manifest smoke: opencode to the opencode_run executor, amp to amp_execute's executor, codex to codex_exec, and gateway to OpenClaw's four lifecycle commands. Current discovery/controller expectations and bilingual API tables were updated. The distinct codex-agent-api named one-shot command and qwen-code Python run command remain, with misleading compatibility comments removed.

The actual HTTP regression starts each real command module on an owned loopback port under the installed public a3 server, uses a synthetic application token, checks canonical discovery, rejects the retired name in discovery/POST with404, and exercises canonical prompt validation (400) or gateway_status (200). It never calls a model or an upstream CLI. All four cases PASS as part of the 26-test current HTTP harness suite. The same four tests against unchanged main command files are recorded separately as expected failures; these are local HTTP/API regressions, not provider/model acceptance.

Before the a3 switch, focused canonical/privacy/process unit suites passed independently: Amp13; Codex11 plus27 subtests; OpenClaw31; OpenCode15. The first combined invocation collected duplicate test_commands module filenames and ran no tests; they were then run as independent processes. Fresh a3 current-head reruns are recorded below when executed.

## Current Node SDK source

Compared immutable old90b5187dca84fca78d75d3045896482540641c72 with reviewed current63d7cd8ece221b9f968eef51eeb932ea334c90d3: server-client runtime changes preserve binding prefix/query, refuse redirects/authority collisions and redact connection error details, in addition to configuration documentation changes. QM adapters actually call this ServerClient transport. The current official npm package remains unavailable, so there is no npm replacement or fallback.

Downloaded the exact current codeload archive:42302bytes, SHA2566fe5ad0e27ca024eed2c2db29e6a2ecf310336505423de6802719baa3137b598 (controller-measured, not upstream-published). Both template provenance files and bounded installers now match. Original SDK package.json/package-lock.json match committed copies byte-for-byte; license/notice and declared source identities were measured. The package still identifies itself as0.1.0; source SHA, not an invented version, distinguishes this reviewed input. SDK build and genuine HTTP adapter fixture results are recorded below after execution; they do not prove the original QM model or cloud workload.

## Current documentation

Removed contradicting current Git-server/wheel-injection claims from README stacks, extension instructions and design/build requirements. Current spec5 instructions no longer advertise obsolete v4/CLI0.4.17 migration steps. Historic receipts remain unchanged; README prose about old injected images is explicitly historical. Provider-owned base resolution and valid vendor semantics remain. Manual source-runtime diagnostic retirement remains pending user judgement and is not folded into this change.

PASS so far: catalog47 conformant; document links222/0; diff whitespace check clean. Required real L1 build, actual public CLI0.5.4 typed-cleanup/native/OpenSandbox matrices and real-model/vendor tasks remain unrun at this checkpoint. Local Docker is absent. No GitHub secrets were uploaded and no cloud resources were created by this follow-up's local checks.


## Executed current a3 local checks

- Fresh a3 command-module HTTP suite:26 PASS. The same four retired-name cases against unchanged main26d6e24 command files produced4 expected FAIL (old names still discovered), while the changed modules pass all four. No model/upstream process was started by those four regressions.
- Current native/privacy/controller suites, each in an independent pytest process: Amp13 command tests +14 protocol tests; Codex11 +27 subtests; OpenCode15 command +42 protocol tests; OpenClaw31 command tests. All PASS under the fresh public a3 venv.
- Exact current Node SDK source was fetched by the existing preparation tool, original metadata verified, npm ci/build passed; the real SDK HTTP adapter fixtures passed8/8 with0skip. QM/QM-Sandbox authored wrapper/runtime/terminal tests passed51. This is genuine source-bound local HTTP transport evidence; no original QM/cloud/model pass is implied.
- Spec tools38 PASS; catalog47 conformant; document links222/0. Whitespace checks PASS.

The initial broad local harness suite reported7 FAIL/209 PASS/18 subtests: the Node-source transport allowlist still held the previous reviewed hash, two negative fixture versions collapsed when updating current pins, and uncommitted changed Codex source could not fit the native15,000-byte wire budget or fetch unchanged bytes at the old HEAD. The allowlist was updated to the actually measured current archive, negative tests keep genuinely distinct package identities, and large source preparation will be rerun after the real scoped commit so immutable source matches. The provider wire cap is not relaxed, and no old wheel fallback is restored. The now-unused native `COPY *.whl` skip is removed and remains rejected by the general explicit-COPY guard. Subsequent exact-head results will be appended rather than deleting these initial failures.
