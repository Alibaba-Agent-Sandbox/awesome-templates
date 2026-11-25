# Decision: Restore reproducible database and document image sources

Status: proposed

## Problem

The actual unchanged dev-services and document-tools Dockerfiles fail against their Provider base's rolling Debian sources. The base pull succeeds, but PostgreSQL 17.11 packages disappear from the indexes and LibreOffice u9 conflicts with u12 dependency candidates. Native CI's separate dated-source repair cannot establish product image rebuildability.

## Decision

Replace the base's sole `debian.sources` file in these two recipes with signed Debian and Debian-security archives at `20261112T000000Z`. Preserve its actual `.pgp` archive keyring, every engine/server pin, the original Provider base, non-root runtime, startup and all business/version assertions. Disable only each historical source's Valid-Until check. Keep the equivalent native CI preparation repair so this PR can pass independently of the documentation PR.

Bump dev-services 1.1.2 to 1.1.3 and document-tools 1.1.3 to 1.1.4 because their build inputs change. Update only the affected dependency-source explanations and design/engineering records. Both catalog entries remain experimental; old provider receipts and qualification remain historical.

## API Design

No API, command, runtime behavior or schema change. Only the recipes' apt source policy and template patch identities change. The catalog has no separate version field to update.

## Alternatives considered

- Change only native CI: insufficient; the original Provider images demonstrably fail to build.
- Change engine versions: broader; it changes exact runtime contracts and requires coordinated application/test updates.
- Remove pins or relax tests: rejected because it removes the reviewed version contract.
- Global trust, unauthenticated apt or package downgrades: unnecessary and rejected. Debian archive signature validation remains required.
- A full catalog/cloud rebuild: unrelated to this two-template dependency defect. Use the existing two-context L1 gate and controlled HTTP verification.

## Dependencies

Refs [Issue314](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/314) and [documentation PR313](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/313). The earlier [Issue304](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/304) was completed with its own u8-to-u9 image acceptance and is not reopened or relabeled as current acceptance.

The exact observed Provider base, source-file layout and keyring are recorded in the verification. The original L1 failure and previous native CI success remain separate evidence. Public CLI/Python release work is independent of this repair.

## Test Strategy

Run the owner specification/catalog/document checks, inspect source/pin preservation and shell syntax, then use normal current-head CI and actual L1 builds for both changed image contexts. Verify non-root execution, exact installed engines and existing keyless smokes.

Use a separate, unmerged verification branch to add strict HTTP validation to the existing image workflow for only these two images. Run each manifest's real startup as the image user, expose only a loopback port, execute the existing unmodified E2E controller with required-engine flags, and independently remove the containers. Preserve exact context hashes proving these images match the repair PR. Do not merge that temporary workflow change or change the image selector, upload images or create cloud Sandboxes.

## Acceptance criteria

Both actual Provider-base images build from signed dated sources and retain their exact engines/server package. Current-head mandatory CI, non-root native checks and actual image HTTP/business/artifact/owned-cleanup checks pass. Context hashes match the repair source, old failures remain recorded, and neither Beta status nor historical provider qualification is promoted.

## Evidence

[Original failure and local preparation](../../../evidence/verify/2026-11-25-engine-image-sources.md) · [actual rebuilt-image and HTTP verification](../../../evidence/verify/2026-11-25-engine-image-sources-remote.md).
