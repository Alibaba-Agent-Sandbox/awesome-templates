# Canonical Express acceptance on an explicitly authorized runner

This workflow is prepared for review. No cloud credentials have been uploaded,
no cloud run has been dispatched, and preparation/unit tests establish no L2 pass.
It executes the real cleanup-fixed `scripts/express_e2e.py`, including production
`abx template deploy`, Docker build/push, READY, new sandbox, CLI/SDK smoke and
owned cleanup. Supplementary image transfer/registration remains a separate path.

## Fixed source and default gates

The workflow pins template/Docker inputs to Pi `a361f49`, production CLI to
`37b6d27`, controller SDK to accepted `666657b`, and injected server-wheel source
independently to `e2cb27e`. Its canonical harness is separately pinned to the
cleanup-fix revision recorded in `scripts/canonical_express_review.py`; it does
not run the known-broken a361 harness. Controller/server checkouts are distinct
because the older server source predates the workspace dependency fix. The CLI
uses `npm ci`; Python installs the public pinned source packages and explicit
build tools through their existing package metadata (no SDK lockfile exists).

Default authorization is BLOCKED. The plan's green configuration check is not
an L2 check; its uploaded `canonical-authorization.json` explicitly says BLOCKED
and `cloud_executed: false` until all authorization conditions match. Cloud keys
are injected only into execution/cleanup steps, after public dependency installs.
No model key is an input or forwarded to the sandbox. Missing cloud configuration
returns exit 2 and a BLOCKED status, with names only and no provider-pass file.

## Concrete approval and secret names

The operator first reviews the final workflow commit and obtains approval to
store only these temporary, prefixed values in GitHub Actions. Preparing this
file or possessing local credentials is not approval for that new storage site.
This change does not upload any secret and does not provision an environment.

| Actions secret | Required meaning |
|---|---|
| `ABX_REVIEW_20261016_ENABLE_CANONICAL_L2` | Exact opt-in value `approved` |
| `ABX_REVIEW_20261016_APPROVED_WORKFLOW_SHA` | Exact reviewed PR head SHA |
| `ABX_REVIEW_20261016_ALICLOUD_ACCESS_KEY_ID` | Existing authorized Alibaba account key ID |
| `ABX_REVIEW_20261016_ALICLOUD_ACCESS_KEY_SECRET` | Corresponding key secret |
| `ABX_REVIEW_20261016_ACR_NAMESPACE` | Authorized ACR namespace; no namespace deletion is performed |
| `ABX_REVIEW_20261016_SANDBOX_API_KEY` | Express platform credential, not a native E2B provider key |
| `ABX_REVIEW_20261016_SANDBOX_BASE_URL` | Matching Express platform API URL |
| `ABX_REVIEW_20261016_SANDBOX_DOMAIN` | Matching Express sandbox domain |

The fixed region is `cn-hangzhou`. Model credentials and the operator's entire
`.env` are never inputs. Same-repository PRs and an exact approved SHA are
required; forks cannot enter the cloud job. Both controller checkouts explicitly
use that head, rather than silently running a different merge checkout.

## Selecting and triggering a reviewed run

Start with `python-hello`. Dispatch accepts one name, comma-separated reviewed
names or `all` (17). The PR path reads repository variable
`ABX_REVIEW_20261016_TEMPLATES`, default `python-hello`. Selection is a strict
whitelist; arbitrary paths/commands and duplicates are rejected. Cloud jobs run
serially and stop the queued matrix on failure. The concurrency group prevents
another authorized batch from overlapping this one.

GitHub does not make a new workflow dispatchable before it exists on the default
branch. While this is a draft stacked PR, the explicit same-repository
`pull_request` opened/synchronize/reopened/edited events provide the review path:
only after the storage approval and exact-head secret configuration can an
operator edit the PR description to trigger the unchanged approved head. This
document does not claim such an event was sent or a run scheduled. A later source
change invalidates the approved SHA and must be reviewed again.

## Evidence and cleanup

The exact canonical runner is invoked with existing flags: READY timeout 900s,
idle timeout 300s, deploy wall limit 3600s and zero push retries. The controller
also bounds the call, offers SIGINT grace for the runner's `finally`, then reports
a failure on timeout. It retains leader identity with WNOWAIT and kills the
owned process group before reaping, including completed leader paths. Platform
Requests/curl CA bundle settings and proxy configuration are forwarded. The job cap is 120 minutes. This is named-command L2 smoke;
the full external HTTP suite and image-backed real-model L3 are not claimed.

The runner refuses pre-existing aliases and persists private intent before cloud
mutation. The controller first requires its unique ACR repository name to be
absent. The alias is `e2e-gh-<run_id>-<run_attempt>-<template>`; only that exact
owned repository/tag is deleted after compute cleanup. Failed/unknown compute
cleanup retains the image, and no pass receipt is exported. Tag and repository
deletion require subsequent official GET 404. Neither shared repositories nor
the namespace is removed. The runner's exact-alias recovery uses existing
official CLI and SDK APIs; an empty list after an unknown response is not proof
of cancellation.

An `always()` step retries the private owned intents. Abrupt runner loss or
forced cancellation can still prevent cleanup or lose the VM's private journal;
that remains a failed/blocked run requiring operator reconciliation of the exact
derived alias with the same account. It is not a cancellation guarantee. Do not
restart a larger batch while ownership is unresolved. Private intents, Docker
auth, raw diagnostics and resource IDs are not artifact paths. Native HOME is
unchanged on the disposable runner; task Docker auth/temp paths are private.

Only canonical exit 0, a fresh validated provider-pass file with independent
official-alias/SDK-sandbox absence readback, and confirmed registry cleanup
permit an `express-<date>.json` upload. Sanitized status records include exact
source pins and separate failure/blocked outcomes. No evidence is automatically
committed or catalog promoted. Review the successful receipt against its exact
template version before incorporating it under the normal contribution rules.
After the authorized batch and reconciliation, remove temporary authorization
and credential secrets from Actions through the approved operator workflow.

See [the specification](template-spec.md#test-levels),
[contribution rules](../CONTRIBUTING.md) and
[中文](canonical-express-review.zh-CN.md).
