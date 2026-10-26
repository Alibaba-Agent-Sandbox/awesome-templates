# Consumer template configuration and examples

Status: proposed

## Problem

The catalog's 46 source and four managed templates mixed user instructions with historical acceptance tables, test tiers and maintainer extension procedures. The specification and checker required engineering headings even when those sections did not help a consumer. Some coding examples omitted the actual model endpoint, credential or login prerequisites; version-only checks did not demonstrate the stated task. Short sandbox lifetimes and client waits could expire before a valid model command.

## Decision

Rewrite all 50 catalog entries' English and Chinese READMEs around their actual useful task, configuration, CLI/SDK/HTTP entry points, outputs and owned cleanup. Remove acceptance and secondary-development sections from consumer READMEs; retain original evidence and design documents in place. Stop requiring those two headings in the specification, skeleton and checkers. Keep rejection of unsupported provider-pass claims. Update shared usage/runtime guides and links to the retained evidence.

## API Design

No runtime, template version, manifest, catalog, provider, CLI or SDK API changes. Examples target published CLI 0.5.6 and Python client/server 0.4.0a6. Source examples connect to the application instance already launched, use application_client with an explicit wait, preserve gateway routing/authentication, and export artifacts before deletion. Each upstream tool retains its own model/authentication variables and endpoint constraints. For OpenCode, this template's configured provider is dashscope, not the alibaba provider shown in an unrelated SDK example. The command's model argument selects dashscope/<model-id>; keys and base URL are launch-time inputs.

## Alternatives considered

Copying a generic E2B/alibaba example would invent a contract for this project. Universal model environment aliases would misrepresent upstream behavior. Removing real evidence or weakening forged-pass checks would hide history. Changing CLI environment precedence in a documentation correction would expand the runtime contract: the current nonempty manifest value still wins over a host export, and documentation explains actual supported overrides instead.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/235

https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/tree/bf1bdda02f3a0e553b94c018624a2bc3a134e9e7

https://opencode.ai/docs/config/

https://opencode.ai/docs/providers/

## Test Strategy

Exercise the removed-heading regression with the old checker and the same new fixture, and retain negative forged-evidence cases. Run specification/catalog checks, docs/link tests, actual published CLI parser checks, code-fence syntax checks, source/schema payload binding and independent translation/content review. Validate shared direct-HTTP routing/authentication using local mock transport without calling that a provider pass. Attempt a separately scoped actual pinned OpenCode local model/API task with explicit ownership and independent file execution. Run required current-head CI before merging. Record actual results and host blockers in the dated verification; no new cloud-matrix claim follows from documentation checks.

## Acceptance criteria

All 100 catalog READMEs remove the requested engineering tails and document truthful configuration and task invocation. Both skeleton languages and contributor/spec/checker rules agree. The regression fails with the old required-heading checker and passes after the correction; forged provider tables remain rejected. Examples, links, scope and secret checks pass, historical/runtime inputs remain unchanged, and the normal PR is merged after applicable latest-head checks/review. Confirm the public registry consumes the merged source before reporting publication.
