# Tau2 original retail native acceptance — final1.0.4

Status: PASS for the stated image, Express steps, SDK, HTTP and original real-model
retail slice. [Issue59](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/59),
[PR166](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/166).

## Exact source and tooling

Template acceptance source3a0d8e91a6246bd276372a6c04a53a7de71cb6ae; template1.0.4,
native original Tau2 sourcefc0055dc4e0a316c3f83133267fbd6faaa770992/version1.0.1.
Official archive92,081,935bytes and measured SHA256 retained in
[upstream.json](../../../tau2-bench/upstream.json); measured digest is not an
upstream-published checksum. Retain original MIT source/data, wrapper Apache2.0
and pinned audioop-lts0.2.2 PSF2.0 notice. Unchanged original dependency pins plus
explicit Python3.13 compatibility dependency are hash-enforced in an isolated venv.
Original shared user guidelines are included; no replacement benchmark is used.

Official native CLI0.4.1 archive SHA256
766b0b10c3e4c633632dad503ae7750183a8be41974a9d048f060836f8cb0c44.
Operator installed noneditable Python client source
d4d93e8cbb986f33a8868f7a4139ed0edb49eaba; servere2cb27e24fde0a67112f82b8d44af463445a5d1a.
No native benchmark or model-generated code was installed/executed on the operator.

## Actual image and Express

Actual same-source [L1 workflow39500169930](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39500169930)
PASS: original Dockerfile/hash installation/pip check, native version/task-count
and non-root workspace/server checks. Image build is distinct from steps proof.

[Canonical native steps receipt](../../../tau2-bench/evidence/express-2026-10-20T212600Z.json)
and [full verification](../../../tau2-bench/evidence/verification-steps-2026-10-20T212600Z.json):
official READY, actual Python SDK creation, genuine CLI/SDK source/version and
114-task loader, full external HTTP8PASS/0FAIL/0SKIP. Steps preserve the same
original installer, source hashes and unchanged15,000-byte wire budget, using
verified private OSS transport for the exact official archive. Configured profile
is2vCPU/2048MiB, non-root; this is not a peak-memory benchmark.

## Real native task and independent replay

Actual SDK `tau2_run(domain="retail", task_id="0", max_steps=40,
command_timeout=900)` against an explicitly configured owned9010server used
approved compatible qwen3.8-flash for both native agent and user.17PASS/0FAIL/
0SKIP. Native termination `user_stop`, original reward1.0,22messages,
11assistant messages,4user messages,7actual native domain tool calls.

The sanitized original SimulationRun trajectory is79,516bytes, SHA256
b30a9c8538079f389895d48f7af4f0630be039d1740bc42e01f2023d4315459d.
`log_path` and `artifact_path` bind the same exclusive owned file. Independent
download matched bytes/hash, source/domain/task. A separate keyless native worker
ran original `evaluate_simulation(... strict_replay=True)` after return and
reproduced1.0. Post-return unpredictable ACK verified the exact target bytes.
No model marker, mock score or saved reward replaces strict replay.

## Ownership, failures and limits

Owned trajectory directory, private native HOME/process state and secondary
listener absence passed. Outer sandbox/template and private OSS bucket/object
absence were independently read back. Duration230.319s. No owned live resources
remain from this run. Private journals preserve exact ownership; no identifiers,
model keys/endpoints or raw transcripts are published.

Earlier image/native/model failures remain in their original receipts and
[failure analysis](2026-10-20-tau2-first-native-failures.md),
[native progress](2026-10-20-tau2-native-model-progress.md). Correct original text
defaults, shared data and Python3.13 compatibility do not relax score/completion/
trajectory/replay gates. The1.0.4 rerun also checks the promised `log_path` alias.
Scope is original text retail task0, not all114tasks, NL judges, voice, knowledge
domains, full-benchmark accuracy, other providers or model billing. Experimental
catalog status remains; only matching Express qualification metadata changes.

## Repository checks

Authored process/controller/installer suite35PASS in0.85s. Strict specification,
full57spec regression, bilingual document links/examples, exact current receipt
audit and final-head CI are recorded at the publication checkpoint. SDK examples
explicitly start and select a configured9010server with separate token, readiness,
model setup checks and owned sandbox/process-stream cleanup.

Publication local checks: strict all-template0violations;57spec regressions PASS
in13.141s;174public Markdown documents and6explicit engineering records have
0link failures. Both complete SDK snippets compile from the actual Markdown.
Current full receipt audit38/38runtime/native and38/38required full HTTP PASS,
without new deployment claims for the other37templates. Exact model controller
SHA256da68a2b97cb38be18d55ca3f9a7775b9d0473e69fbb745480f492c6c91cec409.
Final current-head CI/review and actual remote merge remain the delivery gates.
