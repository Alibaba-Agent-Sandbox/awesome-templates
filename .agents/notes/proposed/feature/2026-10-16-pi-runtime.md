# Decision: Install official Pi on the Alibaba sandbox base

Status: proposed

## Problem

[Issue 41](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/41) requests Pi implementation and actual Express verification. Waiting for an E2B template registration chain does not prevent installing the official Pi CLI in Alibaba's supported base image.

## Decision

Pin official `@earendil-works/pi-coding-agent@1.3.0`, with SHA256-verified Node 24.16.0 satisfying Node >=22.19.0. Deliver ephemeral print mode against an OpenAI-compatible endpoint, typed diagnostics and bounded model execution. Explicit tool selection defaults to read-only tools; `allow_tools=true` grants edit/write/bash in the sandbox. Do not present this as E2B's Pi image or a provider-verified template.

## API Design

`pi_version`, `pi_setup_check` and `pi(prompt, cwd="", allow_tools=False, command_timeout=600)`. Prompt data uses stdin. Each model call owns a temporary configuration containing an environment key reference, not key material. Disable project/user discovery, sessions and automatic catalog traffic. `--no-approve` controls project trust; the explicit tools list controls tool availability. See [design](../../../../docs/design/pi.md) for exact flags and boundaries.

## Alternatives considered

An E2B-specific template ID is unnecessary for this independent installation. RPC/session adaptation adds an unrelated persistent protocol and is deferred. Passing a key in argv or reusing user/extension configuration would expose unnecessary secrets and hidden behavior. An exact npm version pins the package/direct dependencies but does not freeze transitive resolution; that limitation is documented.

## Dependencies

Official upstream release/package, public Node archives, pinned server source/wheel, an authenticated compatible model endpoint for model acceptance, and a real image/cloud run for L1/L2. Upstream MIT attribution remains alongside Apache-2.0 template code.

## Test Strategy

Actual child-process cleanup/privacy/cancellation regressions, HTTP and independent-verifier rejection tests, actual pinned Pi against a local SSE fixture for tool selection/project resource isolation, then real source-runtime model coding acceptance. These do not substitute for image/provider tests. Preserve separate failures, skips and pending gates.

## Acceptance criteria

- Complete v2 template, bilingual usage, design and matching experimental catalog entry.
- Default and writable tool selection independently observed in actual Pi requests.
- No prompt/key argv interpolation, config-secret persistence, or owned-process leak on tested exits.
- Actual source/model task modifies source and creates artifacts while preserving tests; independent isolated checks pass.
- L1 and Express L2 remain pending until actual changed-image execution; no provider verification claim until evidence passes.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-pi-runtime.md). Refs Issue 41; this local implementation does not close its Express/merge criteria.
