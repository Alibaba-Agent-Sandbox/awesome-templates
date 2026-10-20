# Decision: Pinned native Copilot CLI with explicit BYOK

Status: proposed

## Problem

[Issue64](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/64) requests an actual terminal Copilot template and genuine Express/SDK acceptance. The dated survey only found a prerelease and unverified argv/auth names. A similarly named wrapper or response marker cannot establish the native agent works.

## Decision

Install public stable GitHub Copilot CLI1.0.100 and required Linux x86_64 native package using an integrity lockfile. Select upstream's explicit OpenAI-compatible BYOK completions/http profile, requiring no GitHub login. Provide authenticated named version/setup/prompt commands with fresh private state, bounded processes/output, exact tool availability and explicit file-write opt-in. Retain the unmodified upstream custom license independently of the wrapper's Apache license. This service adds authenticated remote command/file-transfer/lifecycle functionality; no standalone native-CLI redistribution or GitHub-service entitlement is claimed.

## API Design

copilot_version()->{native_version}; copilot_setup_check()->presence booleans without network; copilot(prompt,cwd="",allow_write=false,command_timeout=300)->{stdout,stderr,exit_code,native_version}. Bound prompt32KiB, cwd4096bytes/existing inside resolved WORKSPACE, deadline1..600seconds and each output256KiB. Closed read-only view/glob/grep list; explicit writes add edit/create/apply_patch. Disable builtin MCP, custom instructions, update/telemetry/remote/BASH_ENV, delegation and shell tools. Forward only explicit startup-captured provider settings, private HOME/XDG/temp and optional CA/PATH; no GitHub/cloud/key-command credential. Preserve native nonzero status. Stop owned process groups and identity-pinned marked detached workers before deleting private state. Actual cloud SDK examples start9010 with explicit settings rather than assuming prewarm reconfiguration.

## Alternatives considered

Using the survey prerelease has no reproducible stable qualification. Replacing the native product with a chat API client does not fulfill the Issue. Passing a compatible-provider key as a GitHub token would misroute credentials. Broad yolo/path/URL permissions or arbitrary flags are unnecessary. Host execution of generated code is excluded: the model controller requires an explicitly owned remote target. The checker previously mistook the real --no-ask-user flag's internal sk- substring for a credential; bound that secret prefix to a token boundary, retaining actual key-prefix detection and adding a regression.

## Dependencies

Public npm @github/copilot=1.0.100, @github/copilot-linux-x64=1.0.100 and pinned detect-libc integrity in package-lock.json; npm ci --ignore-scripts --omit=optional. Native fixed --version/--help/help providers were actually read without credentials or prompts. Official [BYOK](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/use-byok-models), [programmatic reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference) and bundled upstream license are authorities. Server/common image injectione2cb27e24fde0a67112f82b8d44af463445a5d1a; no SDK change or vendor account added.

## Test Strategy

Authored fixed process substitutes exercise validation, literal prompt argv, tool/credential boundaries, exact redaction/native nonzero status, timeout/detached descendant cleanup and unrelated process survival. Controller regressions reject malformed/error/tool-only JSON and local generated-code targets. L0 HTTP against source explicitly reports unavailable native binary and omitted model tier. L1 builds exact packages/native image. L2 real Express SDK creation plus CLI/SDK named smoke with independent owned cleanup. L3 real native BYOK edits existing source, preserves all original tests, creates fresh artifacts, then independent cloud original/held-out evaluations succeed with unpredictable post-return ACKs. No model-generated code runs on operator. Current-head CI and all Issue criteria must pass before qualification and merge/closure.

## Acceptance criteria

Spec/catalog/bilingual docs/design/record remain consistent and pinned; license preserved. Required local regressions, spec/docs and native image gate pass. Actual current-source Express and strict native model receipts prove useful behavior and independent sandbox/template cleanup; image-registry cleanup if an image is transferred. Preserve every failure/skip as such. Normal latest-head-reviewed merge; Issue64 closes only after required delivered behavior and receipts.

[Verification](../../../evidence/verify/2026-10-20-copilot-cli-byok.md).
