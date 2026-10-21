# Deferred products and implemented slices

[中文](backlog.zh-CN.md).

[Template specification](template-spec.md) and current template-local receipts govern acceptance. Dated research and earlier failure records remain history; a fixed version, directory or merged PR alone does not establish provider/model success. Source templates and provider-managed IDs have separate build and runtime contracts.

## Implemented slices

| Product | Current authoritative implementation | Limits |
| --- | --- | --- |
| SWE | [Original task and independent evaluator](../swe/README.md) | A documented non-Docker task slice; no full SWE-bench leaderboard claim |
| OSWorld | [Real non-privileged desktop and original evaluators](../osworld/README.md) | Selected native desktop/browser task; full VM/application benchmark remains separate |
| Pi | [Pinned original coding CLI](../pi/README.md) | Explicit per-call tool permission and compatible model; no E2B registration implied |
| Aider | [Pinned original CLI and source-edit verification](../aider/README.md) | Bounded selected workspace and explicit write permission |
| Grok Build | [Official original native CLI](../grok/README.md) | Exact version/archive, vendor-compatible profile; original install research is historical |
| QM | [Original harness with actual SDK backend](../qm/README.md) | Declared tool/context/backend slice; no full provider scope/snapshot promise |
| QM sandbox | [Original QM tool context](../qm-sandbox/README.md) | Actual Agent Sandbox HTTP SDK backend; no Superserve registration implied |
| Gemini | [Original native CLI and explicit compatible transport](../gemini/README.md) | Separate Google-hosted authentication from compatible model/tool testing |
| Kimi Code | [Pinned original CLI](../kimi-code/README.md) | Current source, typed commands and provider receipts are authoritative |
| Goose | [Pinned original native runtime](../goose/README.md) | Explicit configured model and owned workspace; no mutable installer claim |

Follow each current README's Verified section, manifest and timestamped receipts for exact qualification. Older draft-only, empty-tested_on and “no implementation” descriptions in the original survey do not describe these delivered sources. Historical failures stay in their dated evidence files.

## Windows Agent Arena, phone sandbox, AndroidWorld and Omarchy

The dated [evidence-backed review](feasibility/README.md) ([中文](feasibility/README.zh-CN.md)) delivers the feasibility/decision alternative explicitly requested by Issues37/38/39/43. These products have no verified installable profile here.

- WAA needs its original Windows11 environment and snapshot. Its launcher explicitly supports KVM=N, so missing KVM alone does not disprove software emulation. A remote original Windows task/evaluator integration remains designed and unrun.
- Phone sandbox requires a real provider/device lease and observable device operations. Accessible configured providers did not establish such a device pool.
- AndroidWorld expects a compatible API33 emulator, ADB and gRPC accessibility, not merely a remote phone or installed Python package. Software-emulated execution is unmeasured.
- Omarchy has CLI/headless maintenance helpers, but they manage an Arch desktop/system. No useful installed Omarchy operation is verified by copying them into Debian or returning a source-directory dev version.

The review contains actual owned Express SDK guest checks, independent cleanup, pinned original sources, provider prerequisite results and concrete remote-integration acceptance. It claims no successful product task or model run.

## K3s

Issue [42](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/42) remains implementation work. A full worker-node/container-runtime cluster needs privileges/networking that have not been qualified in the tested Express profile. An agentless control-plane-only manifest-validation slice must prove actual original API readiness, server-side validation and cleanup before it can become a template; node/pod execution must not be inferred from an API server.

## Other research

[Market survey](template-market-survey-2026-10.md) is a dated research input. Current [catalog](../awesome-templates.yaml), source READMEs and Issues determine delivery. New OpenHands or other product variants require their own pinned source, design, useful named API, actual API tests and provider evidence. Do not infer another provider's image/template ID from an Express deployment.
