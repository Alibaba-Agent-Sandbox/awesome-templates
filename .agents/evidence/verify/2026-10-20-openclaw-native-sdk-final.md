# Verification: native OpenClaw2.1 SDK gateway on Express

Date:2026-10-20. Result:PASS for gateway-only current runtime; current-head CI/normal merge still required. No model/channel or nested sandbox claim.

## Exact scope

Runtime/source9b51db92d63a3149d614eff96db340512da1e9bc, OpenClaw2026.10.4, Node24.16.0 and servere2cb27e24fde0a67112f82b8d44af463445a5d1a. commands SHA25686978657c80885c1d57f8aa000a4f0df3a83d1f5bb283490f6278e376c83050b; actual SDK controller SHA2561785e65ae1c0b6028fd866359ea1c60c31bdca14a375c25ba55f376a53e36723. Final source integration only adds records/qualification and already merged main; runtime/controller hashes stay unchanged.

## Actual native steps

[Basic CLI/SDK + native preparation provenance](../../../openclaw/evidence/express-2026-10-20T153536Z.json) and [full actual SDK gateway](../../../openclaw/evidence/sdk-gateway-steps-2026-10-20T153536Z.json):PASS. Actual Python Sandbox.create, not a CLI-create label; stopped baseline, native authenticated start/health RPC, persistence after response, independent SDK-forwarded HTTP200 healthz ok=true and readyz ready=true, SDK stop/stopped status. Own9010/9012/18789 listeners and private gateway state independently absent. Owned outer sandbox/template cleanup readback PASS.

## Exact CI image

[Export39447908449](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39447908449), artifact12277283296, exact9b51source. GitHub ZIP size503363793bytes/digest verified before extraction. Complete Docker archive1401786368bytes, SHA2560413ba29115008f75b82907a08d9c57e0f47ae2e7b7b502ac59c0cb6094b6a32; actual non-root config/commands/context/server pin matched. Transfer used private same-account registry; before-registration and post-runtime tag digest readbacks matched. [Image proof](../../../openclaw/evidence/image-http-2026-10-20T163034Z.json), [SDK-created CLI/SDK smoke](../../../openclaw/evidence/express-2026-10-20.json), [full native SDK gateway](../../../openclaw/evidence/sdk-gateway-image-2026-10-20T163034Z.json):PASS, including the same useful lifecycle/external probes and independent own state/listener/sandbox/template/registry cleanup. Generic HTTP suite is deliberately empty; it does not stand in for the separately executed full SDK gateway controller. Generic model NOT_RUN is not L3; gateway-only model acceptance is NOT_APPLICABLE_GATEWAY_ONLY.

## Explicit transport configuration

An owned nonce-protected naturally exiting9012 probe observed a global IPv4 kernel peer. The test explicitly configured its exact/32; product defaults stay unchanged and never derive trust from forwarded headers. No peer address, token, cloud identifier, private endpoint or raw model/provider log is published. The borrowed controller owns only its servers/probe/state, never kills the caller sandbox. Auth token remains mandatory. User-configured production proxy addresses must come from an independently known operator trust source.

## Preserved failures and operator maintenance

Four prior2.0.1steps diagnostics remain failed/unqualified: readiness schema mismatch; corrected readiness403; incomplete one-request forwarding probe; probe-port reuse. Outer sandbox/template absence was independently confirmed; first two also confirmed controller state/listener absence. The2.1image attempt16:13failed the unchanged extraction disk guard before any registry/template/sandbox creation. Its default cleanup_verified=false flags are not orphan evidence or a passing run: no cloud resource had been created. After safe checkpoint cache/worktree retirement, a fresh attempt streamed the actual GitHub ZIP into bounded anonymous RAM, validated its real GitHub digest, then ran unchanged archive/source/non-root/real-disk-budget checks on the complete tar. No reserve/hash/budget gate was reduced. Final image pipeline automatically removed its local archive only after successful owned cloud cleanup.

## Local and delivery gates

Source/process/controller43PASS in16.84seconds before cloud; prior strict/doc/snippet gates passed. Final spec/docs/record checks and current-head CI are recorded at delivery. The issue requires gateway/ports/headless SDK use, all exercised here; model calls are outside that gateway contract. [Issue20](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/20), [PR155](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/155). Merge and Issue closure are not claimed by this pre-merge record.

Final local integration checks: `python scripts/check_template.py --all --strict`:0violations; `python scripts/check_docs.py`:153Markdown documents,0local-link failures. Actual installed native Python client source is d4d93e8cbb986f33a8868f7a4139ed0edb49eaba, normal noneditable local-source installation; its installed340Python files were byte-matched to that source in the operator provenance record. Package version0.3.0 alone does not establish client provenance.
