# Tau2 retail preparation verification — 2026-10-20

Status: PARTIAL. Proposed source/runtime preparation for
[Issue59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59).

## Provenance and dependency research

Official annotated tagv1.0.1 resolves to source
fc0055dc4e0a316c3f83133267fbd6faaa770992. Official codeload archive measured
92,081,935 bytes and SHA256 matching [upstream.json](../../../tau2-bench/upstream.json).
This is a controller measurement, not an upstream-published checksum. Selected
source/retail files total about38MB; original retail loader contains114 tasks.
Original task0 has empty NL assertions; tasks requiring an NL judge are refused.

Host uv0.11.28 `uv export --locked` FAILED upstream lock freshness. Frozen export
using unchanged original uv.lock succeeded; no resolution/update was performed.
Hash installation and dependency checks remain actual-image gates. Official
LiteLLM1.81.11 wheel digest matched the upstream lock; source inspection confirms
the local-price-map setting avoids price network refresh. No upstream model/native
runtime was installed or executed on the operator.

## Local and remote gates

Authored process/controller regression run before the final added empty-userinfo
case:28PASS. Final local suite, strict specification, documentation, immutable
steps wire budget and CI: PENDING, to be recorded after execution.
Uncommitted inputs exceed the immutable-copy wire budget; that failed preparation
is not a steps pass. Required image, Express deployment, SDK native benchmark,
real agent/user models, independent strict replay and cloud cleanup: NOT RUN.
No Tau2 cloud resources have been created at this preparation checkpoint.

## Acceptance boundary

`tested_on` is empty, catalog provider unverified and status experimental. A
native source version or mock score is insufficient. Original task0 reward1.0,
actual tool interaction, independently read artifact/hash, keyless original
strict replay and fresh post-return acknowledgement must pass before qualification.
Preserve later failures and separate source/image/steps/model proof.
