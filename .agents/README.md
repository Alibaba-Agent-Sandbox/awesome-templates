# Engineering records: awesome-templates

## Pending specification 5 delivery (2026-10-25)

- [Unified template launch](notes/proposed/architecture/2026-10-25-unified-template-launch.md) · [verification](evidence/verify/2026-10-25-unified-template-launch.md).

Current authoring uses one startup command and all declared services, without workflow selectors. The decision remains proposed until compatible consumers, current-format cloud checks and publication gates complete. Earlier cloud receipts below retain their exact historical scope.

## Current delivery (2026-10-24)

- [Documentation and record synchronization](notes/implemented/process/2026-10-24-current-documentation-sync.md) · [verification](evidence/verify/2026-10-24-current-documentation-sync.md)
- [Public launch: 46 sources × 2 platforms](evidence/verify/2026-10-24-public-template-matrix.md) · [separate remote Git journeys](evidence/verify/2026-10-24-public-git-journeys.md)
- [Managed default execution and native upstream sessions](evidence/verify/2026-10-24-managed-template-usage.md) · [bilingual source quick starts](evidence/verify/2026-10-24-source-application-quickstarts.md)

These are dated results at their recorded inputs. CLI 0.4.17 is the current installation recommendation; the 92-case matrix used CLI 0.4.16. Managed entries, model tasks, PTY and desktop behavior do not inherit a source-smoke pass.

The earlier [cloud-steps documentation decision](notes/proposed/process/2026-10-24-developer-journey-docs.md) and its [partial receipt](evidence/verify/2026-10-24-developer-journey-docs.md) retain their pending post-publication rerun scope. The later default source-image matrix does not substitute for that separate no-Docker journey.

- [Workflow review validation](notes/proposed/architecture/2026-10-23-workflow-review-validation.md) · [verification](evidence/verify/2026-10-23-workflow-review-validation.md)

- [Droid explicit compatible BYOK](notes/proposed/feature/2026-10-20-droid-explicit-byok.md) · [verification](evidence/verify/2026-10-20-droid-explicit-byok.md)
- [Droid1.2 final native SDK/BYOK/image acceptance](evidence/verify/2026-10-20-droid-native-byok-final.md)
- [Original Tau2 retail runner](notes/proposed/feature/2026-10-20-tau2-native-retail.md) · [verification](evidence/verify/2026-10-20-tau2-native-retail.md)
- [Tau2 first native failures and compatibility correction](evidence/verify/2026-10-20-tau2-first-native-failures.md)
- [Tau2 original task and strict replay progress](evidence/verify/2026-10-20-tau2-native-model-progress.md)
- [Tau21.0.4 final original-task SDK/model/replay acceptance](evidence/verify/2026-10-20-tau2-native-final.md)

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


- [Codex API SDK/post-return completion](notes/proposed/process/2026-10-20-codex-api-sdk-postreturn.md) · [verification](evidence/verify/2026-10-20-codex-api-sdk-postreturn.md)
- [OSWorld SDK desktop and current gateway final acceptance](evidence/verify/2026-10-20-osworld-sdk-desktop-final.md)

- [Both native Agents CLI SDK adapters](notes/proposed/process/2026-10-20-agents-cli-both-native-sdk.md) · [verification](evidence/verify/2026-10-20-agents-cli-both-native-sdk.md)

## Current review

- [Complete public-template launch evidence](notes/implemented/process/2026-10-24-public-template-matrix.md) · [92-case matrix](evidence/verify/2026-10-24-public-template-matrix.md) · [public-install pilot](evidence/verify/2026-10-24-public-install-pilot-2.md) · [public Git journeys](evidence/verify/2026-10-24-public-git-journeys.md)

- [Final verification overview](notes/proposed/process/2026-10-21-final-acceptance-overview.md) · [verification](evidence/verify/2026-10-21-final-acceptance-overview.md)

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

- [Native Stagehand4 local browser](notes/proposed/feature/2026-10-20-stagehand-native-local.md) · [verification](evidence/verify/2026-10-20-stagehand-native-local.md)
- [Codex API final SDK/model acceptance](evidence/verify/2026-10-20-codex-api-sdk-model-final.md)
- [Both native Agents CLI adapters: final acceptance](evidence/verify/2026-10-20-agents-cli-both-native-sdk-final.md)

- [Native Cline CLI](notes/proposed/feature/2026-10-20-cline-native-cli.md) · [verification](evidence/verify/2026-10-20-cline-native-cli.md)
- [Stagehand final native SDK/model acceptance](evidence/verify/2026-10-20-stagehand-native-final.md)

- [Current35native/runtime and required HTTP receipt snapshot](evidence/verify/2026-10-20-current-native-http35.json)

- [Cline final native SDK/model acceptance](evidence/verify/2026-10-20-cline-native-final.md)
- [Official Grok Build native coding](notes/proposed/feature/2026-10-20-grok-official-native.md) · [verification](evidence/verify/2026-10-20-grok-official-native.md)

- [Official Grok Build final native SDK/model acceptance](evidence/verify/2026-10-20-grok-official-native-final.md)

- [Current37native/runtime and required full HTTP receipt snapshot](evidence/verify/2026-10-20-current-native-http37.json)

- [Visible native Chrome CDP/noVNC](notes/proposed/feature/2026-10-20-chrome-visible-cdp.md) · [verification](evidence/verify/2026-10-20-chrome-visible-cdp.md)
- [Current38native/runtime and required HTTP receipt snapshot](evidence/verify/2026-10-20-current-native-http38.json)

- [Current38native/runtime and required HTTP after Droid1.2](evidence/verify/2026-10-20-current-native-http38-droid.json)

- [Original AppWorld private runtime](notes/proposed/feature/2026-10-20-appworld-native-runner.md) · [upstream research](evidence/verify/2026-10-20-appworld-native-research.md)




- [Original stable Prime Agent](notes/proposed/feature/2026-10-20-prime-agent-native.md) · [research](evidence/verify/2026-10-20-prime-agent-native-research.md)
- [Headed Chrome final native SDK/image acceptance](evidence/verify/2026-10-20-chrome-native-final.md)

- [Current39native/runtime and required full HTTP snapshot](evidence/verify/2026-10-20-current-native-http39.json)

- [Original QM harness and SDK backend](notes/implemented/feature/2026-10-21-qm-sdk-native-runtime.md) · [research](evidence/verify/2026-10-21-qm-native-research.md)

- [AppWorld final original-task SDK/image/evaluator acceptance](evidence/verify/2026-10-21-appworld-native-final.md)

- [Current40native/runtime and requiredHTTP with AppWorld](evidence/verify/2026-10-21-current-native-http40-appworld.json)


- [Prime Agent final native SDK/image/coding acceptance](evidence/verify/2026-10-21-prime-agent-native-final.md)
- [Current40native/runtime and required fullHTTP snapshot](evidence/verify/2026-10-21-current-native-http40.json)

- [Current41native/runtime and required fullHTTP with Prime Agent and AppWorld](evidence/verify/2026-10-21-current-native-http41.json)

- [QM1.0.1 final original native SDK/backend/model acceptance](evidence/verify/2026-10-21-qm-native-final.md) · [current43native/runtime and required fullHTTP](evidence/verify/2026-10-21-current-native-http43.json)

- [Original Muse native runtime](notes/implemented/feature/2026-10-21-muse-native-runtime.md) · [research](evidence/verify/2026-10-21-muse-native-research.md)

- [Muse1.0.1 final original native acceptance](evidence/verify/2026-10-21-muse-native-final.md) · [current44native/runtime and fullHTTP](evidence/verify/2026-10-21-current-native-http44.json)

- [Original Claude explicit compatible transport](notes/proposed/feature/2026-10-21-claude-explicit-compatible.md) · [verification](evidence/verify/2026-10-21-claude-explicit-compatible.md)
- [Original Gemini explicit compatible transport](notes/proposed/feature/2026-10-21-gemini-explicit-compatible.md) · [verification](evidence/verify/2026-10-21-gemini-explicit-compatible.md)

- [Current44 native/runtime and full HTTP including Gemini2.1.4](evidence/verify/2026-10-21-current-native-http44-gemini.json)

- [Fresh comprehensive template review](evidence/verify/2026-10-21-comprehensive-template-review.md) · [decision](notes/proposed/process/2026-10-21-comprehensive-template-review.md)

- [Current44 native/runtime and full HTTP with Gemini2.2.0](evidence/verify/2026-10-21-current-native-http44-gemini220.json)

- [Original Cursor native template](notes/proposed/feature/2026-10-21-cursor-native-runtime.md) · [research](evidence/verify/2026-10-21-cursor-native-research.md)
- [Qoder native program/API review](evidence/verify/2026-10-21-qoder-program-api-review.md) · [decision](notes/proposed/process/2026-10-21-qoder-program-api-review.md)
- [Current44 native/runtime and full HTTP with Claude1.3.1/Gemini2.2.0](evidence/verify/2026-10-21-current-native-http44-claude131.json)

- [Hardware products and Omarchy decision](notes/proposed/feature/2026-10-21-hardware-products-feasibility.md) · [verification](evidence/verify/2026-10-21-hardware-products-feasibility.md)
- [Current45 native/runtime and complete HTTP with Cursor](evidence/verify/2026-10-21-current-native-http45-cursor.json)

- [External managed catalog and client contracts](notes/proposed/feature/2026-10-21-external-managed-catalog.md) · [verification](evidence/verify/2026-10-21-external-managed-catalog.md)
- [Original Devin native runtime](notes/proposed/feature/2026-10-21-devin-native-runtime.md) · [verification](evidence/verify/2026-10-21-devin-native.md)

- [Current46 native/runtime and complete HTTP with Devin](evidence/verify/2026-10-21-current-native-http46-devin.json)

- [Original agentless K3s validation](notes/rejected/2026-10-21-k3s-agentless-validation.md) · [verification](evidence/verify/2026-10-21-k3s-agentless-validation.md)

- [Devin diagnostic-origin correction](notes/proposed/process/2026-10-21-devin-diagnostic-origin.md) · [verification](evidence/verify/2026-10-21-devin-diagnostic-origin.md)

- [Current46 native/runtime and complete HTTP with corrected Devin1.0.1](evidence/verify/2026-10-21-current-native-http46-devin101.json)

- [K3s evaluated feasibility decision](notes/proposed/process/2026-10-21-k3s-feasibility-decision.md) · [seven original native attempts](evidence/verify/2026-10-21-k3s-final-feasibility.json)

- [Original managed OpenSandbox native acceptance](notes/proposed/feature/2026-10-21-opensandbox-native-acceptance.md) · [verification](evidence/verify/2026-10-21-opensandbox-native-acceptance.md)

Source image backend acceptance: [decision](notes/proposed/feature/2026-10-22-source-image-backend-acceptance.md), [verification](evidence/verify/2026-10-22-source-image-backend-acceptance.md).

- [Remove retired project compatibility](notes/implemented/architecture/2026-10-22-remove-legacy-compatibility.md) · [verification](evidence/verify/2026-10-22-remove-legacy-compatibility.md)

- [Compatibility cleanup remote acceptance](evidence/verify/2026-10-22-remove-legacy-acceptance.md)

- [Use current Express CLI in runnable template examples](notes/implemented/process/2026-10-22-current-express-cli-examples.md) · [verification](evidence/verify/2026-10-22-current-express-cli-examples.md)
- [All46 source image backends](evidence/verify/2026-10-22-source-image-backend-matrix.json) · [current steps recheck](evidence/verify/2026-10-22-current-steps-after-backend-qualification.json)

- [Command recovery review](notes/implemented/process/2026-10-23-command-recovery-review.md) · [verification](evidence/verify/2026-10-23-command-recovery-review.md)

- [Explicit template workflows](notes/proposed/architecture/2026-10-23-explicit-template-workflows.md) · [verification](evidence/verify/2026-10-23-explicit-template-workflows.md)

- [Workflow ID schema alignment](evidence/verify/2026-10-23-workflow-id-schema-alignment.md).

- [Portable profile YAML scalar correction](evidence/verify/2026-10-23-portable-profile-yaml-scalar.md).

- [Current application authentication docs](evidence/verify/2026-10-23-current-application-auth-docs.md).

- [Application auth docs follow-up scope](evidence/verify/2026-10-23-auth-docs-followup-scope.md).

- [Release source alignment](notes/proposed/feature/2026-10-23-release-readiness.md) · [verification](evidence/verify/2026-10-23-release-readiness.md)

- [Release integration on current main](evidence/verify/2026-10-24-release-integration.md).

- [Simplify template usage](notes/implemented/process/2026-10-24-template-usage-simplification.md) · [verification](evidence/verify/2026-10-24-template-usage-simplification.md)

- [Public launch diagnostics and native cleanup](notes/implemented/process/2026-10-24-public-launch-diagnostics.md) · [verification](evidence/verify/2026-10-24-public-launch-diagnostics.md).

- [Public launch pilot2, both default platforms](evidence/verify/2026-10-24-public-launch-pilot-2.md).

- [Source application quick starts](notes/implemented/process/2026-10-24-source-application-quickstarts.md) · [verification](evidence/verify/2026-10-24-source-application-quickstarts.md).
- [Managed template usage and default execution](notes/implemented/process/2026-10-24-managed-template-usage.md) · [verification](evidence/verify/2026-10-24-managed-template-usage.md)
