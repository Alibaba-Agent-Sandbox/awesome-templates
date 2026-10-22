# Verify a CI image on Alibaba Express

[中文](ci-image-acceptance.zh-CN.md). Large assets may transfer slowly during
[platform steps](platform-steps.md). The explicit image path uses the repository's
existing keyless Dockerfile CI export and the native CLI's `template from-image`.
It records `build_mode: image`; it does not establish a step build or a local
controller Docker build. Each template still needs genuine runtime acceptance.

## Prepare public inputs

Use the native CLI/SDK versions and installation recipe in the
[step guide](platform-steps.md). Obtain and SHA256-check upstream
[crane](https://github.com/google/go-containerregistry/releases) for Linux.
The exercised version is0.22.1; Linux_x86_64 archive SHA256 is
`0ab7a1d6932a213aed964ce97666c3077fe691c8606413674a8b3e0b9ec4cda0`.

Dispatch `image-build.yml` on the exact published source branch with
`templates=<name>` and `export_images=true`. This builds public source only;
keep cloud, registry and model credentials out of Actions. Wait for the whole
explicit workflow to succeed and obtain its `image-<name>-<checkout>` artifact
ID before its one-day retention expires. Fetch that source commit locally.

The controller verifies repository/run/artifact identity, successful explicit
workflow, ZIP/TAR hashes, current public Dockerfile/COPY/manifest contract,
actual final image command bytes, pinned server SDK, Linux amd64, non-root user
and working directory. Only `tested_on` metadata can change without invalidating
that contract. Changed runtime bytes require a new CI export.

## Run real acceptance

Provide existing account configuration through process environment:
`ALICLOUD_ACCESS_KEY_ID`, `ALICLOUD_ACCESS_KEY_SECRET`, `ACR_NAMESPACE`,
`ABX_SANDBOX_API_KEY`, `ABX_SANDBOX_BASE_URL`, `ABX_SANDBOX_DOMAIN`, and
`GH_TOKEN` or `GITHUB_TOKEN` for artifact retrieval. `ABX` selects the native CLI;
`NODE_PATH` supplies its documented dependencies. Never paste values into a
command, checked-in file or CI workflow.

```bash
python scripts/run_ci_image_e2e.py ocr \
  --artifact-id <successful-image-artifact-id> \
  --crane /path/to/verified/crane
```

The controller obtains temporary ACR authorization and stores Docker auth bytes
only in an anonymous Linux RAM fd. A private temporary directory contains a
symlink to that inherited fd, which is removed on exit. The client never receives
long-term cloud keys. It first uploads an empty public-content ownership guard,
requires the new repository to be PRIVATE, then transfers the reviewed image
and reads back its content digest. Existing account policy is never changed.

Actual `abx template from-image` registers the nonce-owned review tag; live digest readback before registration and after runtime requires an unchanged content digest. Official API polling requires
READY, and real CLI/SDK smoke precedes external HTTP acceptance. Model acceptance
is explicitly NOT_RUN by this controller; use a separate strict image-backed
model verifier when the owner Issue requires it. `--smoke-only` explicitly omits
full HTTP acceptance and does not certify the complete product.

## Evidence and cleanup

Sandbox/template absence is independently read back by the canonical harness.
Both owned registry tags and the nonce-owned repository are deleted and their
absence read back before any passing receipt is published. The published proof
contains public CI/source hashes and outcomes, without account namespaces,
registry references, sandbox IDs or credentials. Earlier receipts are preserved.

A failure retains a private recovery directory outside the checkout and exports
only a sanitized failed-attempt record. Resolve the retained owned-resource
journal before discarding it. A failed or ambiguous registration remains failed;
cleanup recovery cannot relabel it as acceptance. Historical step failures remain
separate from a later successful image run. Hosted CI and ordinary PR review are
still required before merge.

Actual digest-form registration attempted to pull latest and failed on2026-10-19. This provider path therefore uses the nonce-owned tag plus before/after digest readback; no provider digest-reference support or registry tag immutability is claimed.

The runner checks local external-controller imports before artifact/cloud work. Install the template controller dependencies first (OCR needs Pillow); a missing controller is not a provider pass. Failed test status and independently observed cloud cleanup are recorded separately. SDK secondary URLs are passed to the code-server/Next/Vite verifiers.

### Select actual Python SDK creation

Add `--sandbox-create sdk` to the step or verified-image runner when acceptance
requires executing `agent_sandbox.api.sandbox.Sandbox.create`. The default is
`cli`, preserving existing `abx create` behavior. Both routes wait for the owned
template to reach READY, execute named smoke commands through CLI and SDK, and
retain the same independently read-back sandbox/template cleanup gates.

For example, `python scripts/run_steps_e2e.py python-hello --sandbox-create sdk`
builds genuine platform steps and creates the resulting sandbox through Python.
The verified-image equivalent adds `--sandbox-create sdk` to
`scripts/run_ci_image_e2e.py` with the existing reviewed artifact ID and verified
crane arguments. The receipt's `sandbox_create` is `python-sdk-Sandbox.create`
or `abx create`; earlier receipts do not establish an unrecorded SDK-create call.
The SDK timeout is sandbox lifetime, independent of build readiness and request
timeouts. A lost creation response keeps the private recovery intent and never
publishes acceptance. Local client close does not delete the cloud sandbox;
the harness performs owned destruction and independent absence checks afterward.

The runner verifies the actual native `template from-image --help` contract before
archive or cloud writes. `--private-root` can place large archive/recovery files
on private storage without moving the RAM-auth fd symlink off the native
temporary filesystem. Auth values remain only in anonymous RAM.
