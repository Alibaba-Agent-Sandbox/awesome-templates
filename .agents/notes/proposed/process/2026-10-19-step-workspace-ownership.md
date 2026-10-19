# Decision: Writable native-step runtime workspace
Status: proposed

## Problem

Genuine full Python and Node step-backed HTTP workflows failed on workspace mkdir/upload with permission denied under /home/user/app. Earlier basic CLI/SDK hello/version/service smoke did not exercise that write. Both failed runs independently cleaned owned resources. Native WORKDIR and copied-file ownership did not establish a writable runtime directory.

## Decision

Before the generated final USER user, explicitly chown the standard /home/user/app directory to user:user. Preserve file bytes, source Dockerfiles, pinned dependencies and historical evidence. Add actual non-root write/read/removal to Dockerfile L1 so that image and step paths both exercise the workspace contract.

## API Design

No named-command API change. The common supported native-step profile gains an explicit root build RUN before runtime USER. COPY/ENV/server pins retain their existing provenance. Full cloud reference controllers provide real regressions.

## Alternatives considered

Running application servers as root violates the template contract. Writing fixtures outside the declared workspace or counting basic smoke as full acceptance hides the defect. Do not change every runtime Dockerfile without comparing real image behavior.

## Dependencies

Issues21/29/119, native step USER semantics, existing strict materializer and current source SDK. The public image L1 probe independently executes as the image user; real full step workflows remain required.

## Test Strategy

Materializer regressions and strict docs/spec; actual Dockerfile L1 non-root workspace roundtrip; repeat complete Python/Node step-backed HTTP including independent SDK-forwarded Node3000, original file/script/service checks and owned cleanup.

## Acceptance criteria

Writable declared workspace under user, complete reference workflows pass, failed/baseline receipts preserved without relabeling, exact generated provenance, current-head CI and ordinary merge before Issue closure.
