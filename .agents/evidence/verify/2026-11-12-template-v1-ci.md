# Verification: template v1 contract CI coverage

- Date: 2026-11-12
- Result: PARTIAL — canonical commands pass locally; remote job and complete consumer activation remain pending.
- Change: add the `template-v1-contract` job to the existing e2e workflow for Issue309.

## Scope

The existing active-template checks do not import the inactive v1 normalizers. Add an independent
Node22/Python3.13 job that installs the existing pinned specification requirements and the new
fixture package lock, then executes both-language conformance and Python contract tests. It
does not require cloud credentials, run actions/components or activate source manifests.

## Validation

The commands are the same canonical commands recorded in
[the contract verification](2026-11-12-template-v1-contract.md). A local YAML read checks the
job, command steps and absence of credential permissions/secret requirements. Remote success
must be inspected for the actual pushed head; it is not inferred from this workflow change.

No cloud resources or model calls were created. This job does not replace the final CLI/SDK/
Registry, image, real model, upgrade and independent cleanup gates.
