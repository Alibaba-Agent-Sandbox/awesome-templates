# next-app

## Purpose

Give coding agents concrete Next.js/Vite preview projects with pinned dependencies.

## Capabilities

Fresh non-overwriting scaffolds; one owned persistent server; bounded logs/status/stop. Next3000, Vite5173, commands9000. No Vercel publish. HMR/streaming unverified.

## Exposed API

See complete parameter/default/return table in [README](../../next-app/README.md#command-reference). scaffold, dev_start, dev_status, dev_logs, dev_stop, toolchain_versions, preview_self_test. Literal Node argv, local pinned CLI; no shell interpolation or runtime npm installation.

## How to build

[Dockerfile](../../next-app/Dockerfile) installs integrity-locked Next16.4.2/React19.3.1/Vite8.3.4 with npm ci, retains package notices and uses observed base Node20.20.2. Alibaba base defaultv0.0.49, published server package, generation2 standard start/health commands, USER user.

## Express feasibility

Feasible: yes. Limiting factor: runtime memory and separately unverified WebSocket forwarding. Non-root Node servers need no Docker/KVM/display.2vCPU/2048MB. Preview URLs use SDK network.get_url; HMR forwarding remains separately unverified. Current source/image/cloud acceptance is required, not inferred.

## Risks

Development preview has no app authentication; provider access control is required. Package scripts are disabled during installation. Application edits are executable user code; filtered environment carries no cloud/model secrets. Cleanup signals unique marked pidfds and the unreaped leader group only; confirms no kernel listener. Does not erase caller projects.

## Test plan

Actual pinned Next and Vite GET, source edit reflected, original caller files retained, process/listener absence, unrelated listener preservation, traversal/symlink/overwrite rejection. L0 full HTTP checks; L1 installed pins and real local preview self-test; L2 real image READY/CLI/SDK/full HTTP and external forwarded preview; HMR/WebSocket separate gate.

Version1.1.3 normalizes read/traverse permission on the public root-owned toolchain
after npm ci. Restrictive0600 source context metadata must remain readable by
runtime user; write permission is unchanged. The optional actual image regression
uses explicit NEXT_APP_TEST_BASE_IMAGE, copies inputs0600, builds the real recipe,
requires non-root toolchain_versions and independently confirms its own tag absent.
