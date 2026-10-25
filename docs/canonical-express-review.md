# Express cloud review

[中文](canonical-express-review.zh-CN.md).

Current Express acceptance uses [Public template launch matrix](public-launch-testing.md), with the published CLI/Python distributions and provider-resolved application endpoints. The former fixed-commit deployment job is retired.

## Current task: local Express acceptance

Follow the public launch guide from installation. Configure your own Express account and build environment, then run `scripts/public_launch_e2e.py` for the chosen source. For prepared images, follow [source image acceptance](source-image-acceptance.md). Preserve the distinction between default source builds and prepared-image consumption.

## Fixed source and default gates

The existing `authorization` CI check remains read-only. It validates explicit opt-in, the exact reviewed head and same-repository scope and never executes cloud requests. Real cloud acceptance runs only through an explicit public-launch workflow or an operator's configured local invocation. A successful authorization check is not a deployment pass.

The old deployment implementation, 23-template snapshot, fixed old SDK/CLI checkouts and associated cloud job are removed. No compatibility deployment runner replaces them.

## Concrete approval and secret names

Keep credentials in the operator environment or explicitly authorized encrypted Actions Secrets. Do not copy credentials into Actions automatically. The current public-launch workflow lists its configuration names; no secret value belongs in a file, artifact or issue. The read-only authorization check does not store or forward provider credentials.

## Selecting and triggering a reviewed run

Use current catalog names or `all` in **Public template launch matrix**, choose `provider=alicloud-express`, and follow its exact-ref and installation instructions. The authorization helper reads the current source catalog; it does not maintain a separate snapshot list.

## Evidence and cleanup

Record exact package/source inputs, full CLI/SDK/HTTP results, skips and independently confirmed owned-resource absence. Failed attempts remain failures. Historical canonical receipts retain their original scope; the [retired implementation](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/2bacceec5161181e1f73f737955ddc8fae250ed9/scripts/canonical_express_review.py) remains available in immutable Git history. The current helper retains only read-only authorization planning and shared owned ACR deletion used by the public runner.
