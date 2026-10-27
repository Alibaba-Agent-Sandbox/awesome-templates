# Decision: Accept independently absent owned local image tags

Status: proposed

## Problem
Task-owned fully pushed local images may be reclaimed after cloud provisioning to
fit limited disk. The local build-tag cleanup branch required docker rm exit0,
although its remote/push-tag branches already accept an absent image. Completed
business tasks therefore received false cleanup failures after early local reclaim.

## Decision
Accept exact No such image removal errors only when independent docker inspect also
confirms No such image. Require the tag suffix to belong to the exact launch alias,
including when an alias appears in a foreign repository name. Preserve all original
failed receipts; reconcile exact owned resources separately without repeating models.

## API Design
No template/runtime/public command changes. Harness cleanup becomes idempotent for
known absent local tags. In-use images, inaccessible daemons, present tags and foreign
tags remain failures. Remote image/template/sandbox verification stays independent.

## Alternatives considered
Ignoring Docker errors or rewriting original failed evidence could mask retained
resources. Repeating expensive completed business/model work does not establish
cleanup better than fresh exact-resource observations.

## Dependencies
Fixes https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/266;
refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
User explicitly authorized task-image cleanup to keep the constrained host usable.

## Test Strategy
Regression cases for already absent, still present, inaccessible daemon, in-use and
foreign tags. Real Docker control creates/removes an exact task tag; old cleanup
fails while fixed cleanup independently confirms absence and retains shared image.
Reconcile only exact original journals and independently observe outer/template/
remote/local absence, preserving the immutable failed receipt and original hashes.

## Acceptance criteria
Local regressions, actual Docker control and current-head CI pass. A later verified
cleanup supplement must bind an original completed business receipt; no uncompleted
business task or failed model call is promoted.
