# Decision: Release both local tags after Express acceptance

Status: proposed

## Problem

Successful Express acceptance deleted the local build tag and remote ACR tag but
left the registry-qualified local push tag. That reference retained complete
images during a serial, disk-limited template matrix. See [Issue 238](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/238).

## Decision

After confirming deletion of the exact owned remote ACR tag, remove its exact
local Docker tag and independently inspect local absence. An already absent tag
is reconciled. Refused deletion or a tag still present is a cleanup failure.

## API Design

No product API changes. The acceptance report can claim prepared artifacts absent
only after both local tag identities and the remote tag have been checked.
Existing namespace, alias and resource ownership guards remain mandatory.

## Alternatives considered

Deleting by image ID or pruning the shared registry repository can affect other
users. Global image pruning also exceeds one attempt's ownership. Both are
rejected. Manual follow-up was used to reconcile earlier attempts; it does not
replace the maintained cleanup behavior.

## Dependencies

Docker and the existing signed ACR tag deletion/GET-404 check. No additional
credential storage, cloud endpoint or runtime dependency.

## Test Strategy

A regression must first fail on the old verifier. Cover successful removal,
independent absence, refused removal, a still-present tag, already-absent
reconciliation and existing foreign-resource guards. Exercise the corrected
cleanup against a real source attempt's owned image tag.

## Acceptance criteria

- The exact owned local push tag is removed and independently absent.
- Cleanup cannot pass after local refusal or a still-present tag.
- Foreign/shared images and repositories remain untouched.
- Focused regression, document/record checks and current-head CI pass.

## Evidence

[Verification](../../../evidence/verify/2026-10-27-local-push-tag-cleanup.md).
Broader method/model matrix acceptance in Issues 215 and 221 remains separate.
