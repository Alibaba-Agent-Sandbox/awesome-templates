# Engineering records: awesome-templates

This repository owns template source, specification, catalog and acceptance records.
Read [CONTRIBUTING.md](../CONTRIBUTING.md) and [the specification](../docs/template-spec.md).
New engineering records use English and stay in this repository.

- [Document HTML, slides and Writer PDF](notes/proposed/feature/2026-10-20-document-html-pptx-pdf.md) · [verification](evidence/verify/2026-10-20-document-html-pptx-pdf.md)
- [Document1.1final native/SDK/image/step acceptance](evidence/verify/2026-10-20-document-html-pptx-pdf-final.md)

- [Kimi Code runtime](notes/proposed/feature/2026-10-19-kimi-code.md)
  · [verification](evidence/verify/2026-10-19-kimi-code.md)

- [Contributor standards and platform steps](notes/proposed/process/2026-10-19-standards-and-platform-steps.md)
  · [verification](evidence/verify/2026-10-19-standards-and-platform-steps.md)
  · [actual platform limits and reruns](evidence/verify/2026-10-19-step-platform-limits.md)
  · [RUN environment verification](evidence/verify/2026-10-19-step-build-environment.md)
- [Provider-owned preparation](notes/proposed/process/2026-10-19-provider-preparation.md)
  · [verification](evidence/verify/2026-10-19-provider-preparation.md)

- [Native Crush](notes/proposed/feature/2026-10-20-crush-runtime.md) · [verification](evidence/verify/2026-10-20-crush-runtime.md)

- [Complete platform-step acceptance](notes/proposed/process/2026-10-20-complete-platform-steps.md) · [verification](evidence/verify/2026-10-20-complete-platform-steps.md)

## Layout and lifecycle

- `notes/proposed/<architecture|feature|process>/YYYY-MM-DD-<slug>.md`: pending decisions.
- `notes/implemented/<category>/...`: accepted decisions reflected in code.
- `notes/rejected/` and `notes/superseded/`: flat historical decisions.
- `evidence/verify/YYYY-MM-DD-<slug>.md`: point-in-time validation summaries.

Use the seven ADR sections: Problem, Decision, API Design, Alternatives considered,
Dependencies, Test Strategy, Acceptance criteria. Status matches its directory;
local implementation alone does not establish an accepted or merged decision.

Record exact tested scope/revision, commands and outcomes, real versus synthetic
backends, missing gates and owned-resource cleanup. Use PASS, PARTIAL, BLOCKED or FAIL.
Keep per-template provider evidence in its established location and link to it.
Preserve historical evidence; new runs receive distinct filenames. Do not store
credentials, private prompts or unsanitized logs. Cross-repository links are absolute.

- [Native Copilot CLI BYOK](notes/proposed/feature/2026-10-20-copilot-cli-byok.md) · [verification](evidence/verify/2026-10-20-copilot-cli-byok.md)

- [Copilot CLI native final acceptance](evidence/verify/2026-10-20-copilot-cli-native-final.md)
- [Explicit OpenClaw proxy/SDK acceptance](notes/proposed/feature/2026-10-20-openclaw-explicit-proxy-sdk.md) · [verification](evidence/verify/2026-10-20-openclaw-explicit-proxy-sdk.md)

- [OpenClaw native SDK final acceptance](evidence/verify/2026-10-20-openclaw-native-sdk-final.md)
- [Step manifest receipt binding](notes/proposed/process/2026-10-20-step-manifest-receipt-binding.md) · [verification](evidence/verify/2026-10-20-step-manifest-receipt-binding.md)
- [OSWorld required external SDK desktop](notes/proposed/process/2026-10-20-osworld-required-sdk-desktop.md) · [verification](evidence/verify/2026-10-20-osworld-required-sdk-desktop.md)


- [OSWorld SDK desktop and current gateway final acceptance](evidence/verify/2026-10-20-osworld-sdk-desktop-final.md)

## Current review

- [Node Web HTTP output protocol](notes/proposed/process/2026-10-16-node-web-http-output.md)
- [Node Web protocol verification](evidence/verify/2026-10-16-node-web-http-output.md)
- [Catalog completion decision](notes/proposed/feature/2026-10-16-catalog-completion-review.md)
- [Verification](evidence/verify/2026-10-16-catalog-completion-review.md)
- [Image-build gate](notes/proposed/process/2026-10-16-template-image-build-gate.md)
- [Image-build preparation evidence](evidence/verify/2026-10-16-template-image-build-gate.md)

- [Codex existing-source acceptance](notes/proposed/process/2026-10-16-codex-existing-source-acceptance.md)
- [Codex premature-exit and actual-image verification](evidence/verify/2026-10-16-codex-early-exit-regression.md)
Coding verifier completion follow-up: [decision](notes/proposed/feature/2026-10-16-four-coding-verifier-completion.md) and [verification](evidence/verify/2026-10-16-four-coding-verifier-completion.md).
- [Aider independent verifier](notes/proposed/process/2026-10-16-aider-independent-verifier.md)
- [Aider verifier evidence](evidence/verify/2026-10-16-aider-independent-verifier.md)

- [Aider hardened image recheck](evidence/verify/2026-10-16-aider-hardened-image-recheck.md)
- [OpenCode verifier decision](notes/proposed/process/2026-10-16-opencode-verifier-completion.md)
- [OpenCode verifier evidence](evidence/verify/2026-10-16-opencode-verifier-completion.md)
- [Documentation ownership](notes/proposed/process/2026-10-18-template-documentation-ownership.md)
- [Canonical cleanup decision](notes/proposed/process/2026-10-16-express-cleanup-outcome.md)
- [Canonical cleanup evidence](evidence/verify/2026-10-16-express-cleanup-outcome.md)
- [Canonical Express CI decision](notes/proposed/process/2026-10-16-canonical-express-ci.md)
- [Canonical Express CI preparation](evidence/verify/2026-10-16-canonical-express-ci.md)

- [Integrated23 acceptance](notes/proposed/process/2026-10-18-integrated-template-acceptance.md) · [verification](evidence/verify/2026-10-18-integrated-template-acceptance.md)

- [Accepted Node startup repair](notes/implemented/process/2026-10-18-node-startup-race.md) · [verification](evidence/verify/2026-10-18-node-startup-race.md)
- [Accepted registry artifact retirement](notes/implemented/process/2026-10-18-orphan-registry.md) · [verification](evidence/verify/2026-10-18-orphan-registry.md)

- [Local Express/model review](evidence/verify/2026-10-18-local-express-model-review.md)
- [OpenCode completed-step decision](notes/proposed/process/2026-10-18-opencode-completion-steps.md)
- [Image CI checkpoint decision](notes/proposed/process/2026-10-16-image-ci-checkpoint.md)
- [Image CI checkpoint evidence](evidence/verify/2026-10-16-image-ci-checkpoint.md)
- [Prewarmed server configuration](notes/proposed/process/2026-10-16-prewarmed-server-configuration.md) · [verification](evidence/verify/2026-10-16-prewarmed-server-configuration.md)

- [Delivery integration review](evidence/verify/2026-10-18-template-delivery-review.md)

- [Consumer entry compatibility](notes/proposed/process/2026-10-19-consumer-entries.md) · [verification](evidence/verify/2026-10-19-consumer-entries.md)

- [Native acceptance entry](notes/proposed/process/2026-10-19-native-acceptance-entry.md) · [verification](evidence/verify/2026-10-19-native-acceptance-entry.md)

- [Provider-owned template launch](notes/proposed/feature/2026-10-19-provider-template-launch.md) · [verification](evidence/verify/2026-10-19-provider-template-launch.md)

- [Polyglot toolchain](notes/proposed/feature/2026-10-19-polyglot-toolchain.md) · [verification](evidence/verify/2026-10-19-polyglot-toolchain.md)
- [Native apply_patch](notes/proposed/feature/2026-10-19-apply-patch-runtime.md) · [verification](evidence/verify/2026-10-19-apply-patch-runtime.md)

- [Managed runtime catalog](notes/proposed/feature/2026-10-19-managed-template-catalog.md) · [verification](evidence/verify/2026-10-19-managed-template-catalog.md)
- [Native browser-use](notes/proposed/feature/2026-10-20-browser-use-runtime.md) · [verification](evidence/verify/2026-10-20-browser-use-runtime.md)
- [Bounded browser build](notes/proposed/process/2026-10-19-bounded-browser-build.md) · [verification](evidence/verify/2026-10-19-bounded-browser-build.md)

- [Express steps checkpoint](evidence/verify/2026-10-19-steps-checkpoint-1555.md)

- [Pinned preview runtime](notes/proposed/feature/2026-10-19-next-app-runtime.md) · [verification](evidence/verify/2026-10-19-next-app-runtime.md)
- [Development databases](notes/proposed/feature/2026-10-19-dev-services-runtime.md) · [verification](evidence/verify/2026-10-19-dev-services-runtime.md)
- [Standalone code-server](notes/proposed/feature/2026-10-19-code-server-runtime.md) · [verification](evidence/verify/2026-10-19-code-server-runtime.md)
- [Heavy template image acceptance](notes/proposed/process/2026-10-19-heavy-template-image-acceptance.md) · [verification](evidence/verify/2026-10-19-heavy-template-image-acceptance.md)
- [OCR Express resources](notes/proposed/process/2026-10-19-ocr-resource-profile.md) · [verification](evidence/verify/2026-10-19-ocr-resource-profile.md)

- [Exact-source CI image acceptance](notes/proposed/process/2026-10-19-ci-image-acceptance.md) · [verification](evidence/verify/2026-10-19-ci-image-acceptance.md)

- [Step workspace ownership](notes/proposed/process/2026-10-19-step-workspace-ownership.md) · [verification](evidence/verify/2026-10-19-step-workspace-ownership.md)
- [Controller prerequisites](notes/proposed/process/2026-10-19-controller-prerequisite-preflight.md) · [verification](evidence/verify/2026-10-19-controller-prerequisite-preflight.md)

- [Native DeepAgents](notes/proposed/feature/2026-10-20-deepagents-runtime.md) · [verification](evidence/verify/2026-10-20-deepagents-runtime.md)
- [Goose runtime](notes/proposed/feature/2026-10-20-goose-runtime.md) · [verification](evidence/verify/2026-10-20-goose-runtime.md)
- [Current heavy-image acceptance](evidence/verify/2026-10-20-current-heavy-image-acceptance.md)
- [OCR step acceptance](notes/proposed/process/2026-10-20-ocr-step-acceptance.md) · [verification](evidence/verify/2026-10-20-ocr-step-acceptance.md)

- [Database port ownership](notes/proposed/process/2026-10-20-database-port-ownership.md) · [verification](evidence/verify/2026-10-20-database-port-ownership.md)
- [Operator-local SDK preview](notes/proposed/process/2026-10-20-sdk-preview-relay.md) · [verification](evidence/verify/2026-10-20-sdk-preview-relay.md)
- [Single-file template application v3](notes/proposed/architecture/2026-10-20-template-application-v3.md) · [verification](evidence/verify/2026-10-20-template-application-v3.md)

- [Application provider baseline review](evidence/verify/2026-10-20-template-application-v3-baseline-review.md)

- [Application event reserve compatibility](evidence/verify/2026-10-20-template-application-v3-event-reserve.md)
- [Actual SDK creation acceptance](notes/proposed/process/2026-10-20-sdk-created-acceptance.md) · [verification](evidence/verify/2026-10-20-sdk-created-acceptance.md)

- [SWE real-model budget](notes/proposed/process/2026-10-20-swe-real-model-budget.md) · [verification](evidence/verify/2026-10-20-swe-real-model-budget.md)
- [Four exact-controller image/model reruns](evidence/verify/2026-10-20-four-coding-image-revalidation.json)

- [Native browser MCP](notes/proposed/feature/2026-10-20-browser-native-mcp.md) · [verification](evidence/verify/2026-10-20-browser-native-mcp.md)

- [Browser PDF and owned scripts](notes/proposed/feature/2026-10-20-browser-pdf-process.md) · [verification](evidence/verify/2026-10-20-browser-pdf-process.md)
- [Application current-main integration](evidence/verify/2026-10-20-template-application-v3-main-integration.md)

- [V3 structural smoke expectations](notes/proposed/process/2026-10-20-v3-structured-smoke.md) · [verification](evidence/verify/2026-10-20-v3-structured-smoke.md)

- [Three native SDK creation profiles](notes/proposed/process/2026-10-20-three-native-sdk-create.md) · [verification](evidence/verify/2026-10-20-three-native-sdk-create.md)

- [BrowserUse final SDK/image/model acceptance](evidence/verify/2026-10-20-browser-use-final.md)
- [Native coding SDK image acceptance](notes/proposed/process/2026-10-20-native-coding-sdk-acceptance.md) · [verification](evidence/verify/2026-10-20-native-coding-sdk-acceptance.md)
- [Native Media argv and exact SDK source](notes/implemented/feature/2026-10-20-native-media-args.md) · [verification](evidence/verify/2026-10-20-native-media-args-final.md).

- [Codex current SDK image acceptance](notes/proposed/process/2026-10-20-codex-sdk-image-acceptance.md) · [verification](evidence/verify/2026-10-20-codex-sdk-image-acceptance.md)
