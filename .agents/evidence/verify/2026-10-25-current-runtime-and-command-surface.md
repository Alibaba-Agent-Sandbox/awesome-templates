# Current runtime, command and documentation verification

Date: 2026-10-25
Result: PARTIAL; required image/cloud gates pending
Base: 26d6e24e8b29b6c73b364d954dc0279d22a6f9d5
Tracking: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/221
Dependency: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/224

## Initial public a3 packages and inventory (historical candidate)

The SDK owner reported public a3 publishing run 40209677091 SUCCESS. Independently created a fresh Python3.13 venv and installed client/server==0.4.0a3 from https://pypi.org/simple. Both importlib.metadata versions are 0.4.0a3; imports and pip check PASS. No source checkout or old package fallback entered that environment.

Inventory enumerated catalog source manifests plus _skeleton and every manifest build_profiles Dockerfile: 47 runtime manifests and 48 recipes, including python-hello/Dockerfile.portable. Each manifest increments its prior patch by one. At that initial candidate, all declared recipes installed published server a3 from the official index, and its docs/tool fixtures/CI host dependencies used the same package. The final a4 candidate is recorded below. No image or cloud pass is inferred from this static inventory.

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


After the scoped source commit cbef1cde59e760f7fbae4482cc03b23f636dc569, the complete applicable preparation/image/archive/native-process/asset/HTTP/batch/managed/launch-contract suite passed217 tests plus18 subtests in12.21seconds. Exact source bytes now match the immutable commit for native archive preparation, including Codex and both QM profiles. The15,000-byte wire cap and unreviewed-asset negatives remain enforced. No cloud execution was used to obtain this local pass.

Reproducible commands, inside a fresh Python3.13 venv with the public a3 packages:

```bash
python -m pip install --index-url https://pypi.org/simple agent-sandbox-client==0.4.0a3 agent-sandbox-server==0.4.0a3 pytest==9.1.1 PyYAML==6.0.3 httpx==0.28.1 jsonschema==4.26.0 Pillow==11.3.0 pypdf==6.21.1
python -m pip check
python -m pytest -q scripts/test_template_http_acceptance.py
python -m pytest -q scripts/test_prepare_steps.py scripts/test_ci_image.py scripts/test_ci_image_archive.py scripts/test_express_cleanup.py scripts/test_steps_http.py scripts/test_step_assets.py scripts/test_step_asset_cache.py scripts/test_cursor_assets.py scripts/test_devin_assets.py scripts/test_template_http_acceptance.py scripts/test_image_e2e_batch.py scripts/test_managed_catalog.py scripts/test_template_launch_contract.py
python -m pytest -q qm-sandbox/test_commands.py qm-sandbox/test_runtime.py qm/test_terminal.py
python qm-sandbox/prepare_sdk_tests.py /tmp/fresh-owned-qm-sdk
ABX_QM_TEST_SDK_ENTRY=/tmp/fresh-owned-qm-sdk/dist/index.js node --test qm-sandbox/test_adapter.mjs
python scripts/test_spec_tools.py
python scripts/check_template.py --all
python scripts/check_docs.py
```

The four canonical template unit suites and the Amp/OpenCode controller protocol suites run in separate pytest processes because their test_commands.py module filenames are shared. Test logs retain the initial filename-collection and uncommitted-source failures; no past receipt is upgraded into a current pass.

## Public a4 preparation

The SDK owner subsequently published the documentation-only a4 patch at https://github.com/Alibaba-Agent-Sandbox/python-sdk/commit/100da4661809f91a5d50e2722d1f4a8d4da3b131. The official publisher https://github.com/Alibaba-Agent-Sandbox/python-sdk/actions/runs/40215483508 completed successfully on attempt 2; its initial metadata-propagation failure remains historical. The final candidate now pins public 0.4.0a4 in all 48 declared Docker recipes and current installation documentation. The 47 unmerged template patches remain one increment above public main; a replaced draft pin does not receive another template version.

Independent local official-index installation upgraded the isolated verification environment from a3 to exact client/server 0.4.0a4; pip check and both public imports passed. All four public provider-sandbox docstrings were read back and no longer list removed parameter aliases. An initial ad-hoc check incorrectly matched `api_key:` inside the canonical `sandbox_api_key:` spelling; the corrected anchored parameter-line check passed. This was a check error, not a package defect. The earlier a3 local and 54-check CI results above preserve their original scope and do not certify the a4 image. At that preparation checkpoint CLI 0.5.4 was not yet publicly installed here; its later readback is recorded below. Fresh two-provider runtime matrices remain pending.

A4 preparation local checks passed: `python scripts/test_spec_tools.py` ran 58 tests successfully; `python scripts/check_template.py --all` reported all 47 manifests conformant; `python scripts/check_docs.py` checked 222 Markdown documents with zero failures. The same maintained prepare/image/archive/cleanup/HTTP/assets/cache/batch/managed/launch-contract suite listed above passed 217 tests and 18 subtests against installed public a4 in 12.71 seconds. The four real command-module HTTP regressions are included; no cloud provider or model was invoked by these local checks. Current-head remote a4 image CI is not yet run.

The published GitHub CLI 0.5.4 Linux x64 binary was subsequently independently checked against its official 135400640-byte artifact and SHA256 1efd92cd7d9dcf2dc9ee593fb39b730060fc5c0b5caefb48b3a80446f52d0088. Its actual help passed the maintained launch/native prepare/delete/from-image contract test in an empty HOME. The source selection still has no workflow or sandbox-create selector. PR224 separately records genuine native acceptance using this public binary, host a4 and its inherited a2 guest; it is not the final a4-template matrix. Npm publication and fresh current-head image/provider acceptance remain separate requirements.

The official CLI npm publisher https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/actions/runs/40218523980 subsequently completed successfully. An independent nonce readback from the official npm version endpoint returned @agent-sandbox/cli 0.5.4 and its public tarball https://registry.npmjs.org/@agent-sandbox/cli/-/cli-0.5.4.tgz with SHA512 integrity aDkVigf0A8peNxNqL7lmd2vqIgl6ZCFzFvwd3LhDbH0q75cRtpt1zqLQeexkz+BpgK0Z3YujAcSFV/MJgmSnBw==. Current install commands and actual-help CI now pin 0.5.4; dated older receipts retain their original inputs. This metadata readback is distinct from the actual GitHub-binary installation/help/native-cleanup verification. Final remote image and public-source two-provider runs are still pending.
