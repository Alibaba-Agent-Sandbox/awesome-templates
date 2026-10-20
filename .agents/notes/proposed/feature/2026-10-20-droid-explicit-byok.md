# Decision: genuine Droid compatible BYOK and isolated execution

Status: proposed

## Problem

[Issue19](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/19)
remains open after historical version/basic HTTP smoke because real coding
acceptance was blocked on Factory credentials. Actual fixed0.241.1 supports a
custom compatible model independently of a Factory account. The old subprocess
also copied the entire server environment and retained unbounded output.

## Decision

Keep genuine official0.241.1, lock all npm dependencies/integrities and check the
actual Linuxx64 binary SHA256 at image build and native execution. Add explicit
`droid_byok` and read-only BYOK setup while retaining legacy Factory arguments.
Private per-call settings contain only a key reference, explicit model/base and
native `generic-chat-completion-api`; real key enters private environment only.
Use anonymous task stdin, fixed native argv with low autonomy, no builtin skills,
bounded streams/deadline and owned group/nonce/pidfd cleanup. Both modes use
allowlisted environments/private HOME; operator cloud/GitHub secrets are excluded.

## API Design

[Complete bilingual command reference](../../../../droid/README.md#command-reference).
BYOK returns genuine native stdout/stderr/exit/version. Nonzero native exits are
retained and cannot certify success. Native version and old Factory string API
remain compatible. New settings are captured at server import; document explicit
startup for prewarmed servers. Template advances to1.2.0; old receipts stay history.

## Alternatives considered

A compatible key cannot stand in for a Factory product credential in the legacy
API, but the native custom-model API is a distinct supported path. A direct chat
wrapper would not establish Droid operation. Floating installation/update hooks
lose provenance. Unsafe permission bypass, forwarding operator tokens and treating
marker-only output as acceptance are rejected.

## Dependencies

Official proprietary `@factory/cli@0.241.1` and native matching package, full npm
lock, binary SHA2561f50e238df053573aec1dae7b90b19c8e5afca83ab13a790a00f53ba4e4b9ab1.
Package declares UNLICENSED; retained upstream notice explains wrapper license
does not relicense it. Immutable servere2cb27e and explicit approved compatible
model/base/key. Source repository metadata is not a public source-commit claim.

## Test Strategy

Preserve legacy process/protocol tests; add actual authored-process stdin/settings,
environment exclusion, native nonzero, private-state cleanup, output overflow,
input/URL/path/timeout bounds and terminal JSON tests. Synthetic-only genuine
native probe must observe exact owned compatible endpoint/model/Bearer and native
positive-turn success before real credentials. Actual L1 and canonical native
steps with SDK creation, full HTTP, strict real source edit/artifact/original+
held-out post-return tests and independent owned cleanup. Generated code runs
only on a fresh owned remote cloud sandbox. Legacy Factory controller remains
separate and unverified for real Factory-model behavior without that credential.

## Acceptance criteria

Complete bilingual docs/design/catalog/records and current required checks.
Actual native image, Express SDK-created steps, strict BYOK coding and independent
owned cleanup receipts with exact provenance. Normal reviewed merge and actual
Issue closure only after required gates. Synthetic-only probe is not L3/cloud.

[Verification](../../../evidence/verify/2026-10-20-droid-explicit-byok.md).
