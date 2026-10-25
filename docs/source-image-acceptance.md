# Source image acceptance

[中文](source-image-acceptance.zh-CN.md).

The current catalog contains 46 source recipes and four provider-managed entries. Use the [public launch testing guide](public-launch-testing.md) for fresh installation, source builds, provider-resolved CLI/SDK/HTTP calls and independent cleanup on Express and OpenSandbox. Provider-managed IDs are tested separately on their owning provider.

## Image build checks

The **Template images (L1)** workflow builds each selected Dockerfile, installs its exact published server dependency and checks native dependency pins, non-root workspace access and named smoke commands. It does not inject a source SDK wheel. A successful image build alone does not establish a working provider launch or a real model task.

The optional `export_images` input saves an already verified image for one day. Export metadata records the exact source and image digest and the verified server package version. Treat image transfer as a separate experiment from the default source build.

## Provider launch and full HTTP checks

Use **Public template launch matrix** with `distribution=published`, `provider=opensandbox`, `alicloud-express` or `both`, and `templates=all` or explicit catalog names. The workflow installs official published CLI/Python packages, installs the public provider plugin where needed and runs the existing `scripts/public_launch_e2e.py` controller. Follow its guide for exact reviewed package/provider refs and provider configuration.

The controller launches the documented source, checks the actual guest server version against the Dockerfile, invokes manifest commands through CLI, Python and HTTP, checks service authentication, shell/files and every template's complete HTTP controller. Browser templates use actual provider-resolved CDP/noVNC endpoints. Only owned resources are deleted; independent absence is required. Model/vendor-account omissions remain explicit.

The retired `test_opensandbox` image-workflow branch, fixed old CLI/SDK checkouts and direct Docker-bridge controller are replaced by this existing public path. A template's Python application commands do not require a provider-native interpreter.

## Express image transfer

For an already verified export, use the [image consumer](../scripts/run_ci_image_e2e.py) or a bounded batch:

```bash
python scripts/run_image_e2e_batch.py --workflow-run EXPORTED_RUN_ID \
  --crane /path/to/verified/crane --private-root /private/template-acceptance \
  --workers 4 --output /private/template-acceptance/progress.json
```

`EXPORTED_RUN_ID` identifies a successful exact-source image export; `crane` is the verified registry client. The private directory holds local console/recovery data and must stay outside the checkout. Configure provider/registry credentials in the operator environment. `--templates` selects explicit comma-separated names. Every selected case runs; historical PASS records do not skip it. Unknown cleanup stops new operations while existing owned runs finish.

The consumer transfers a nonce-owned private image, registers it and uses the current unified launch lifecycle with the declared startup, services and environment. It runs current SDK/CLI/HTTP checks and independently checks sandbox, template and registry absence. This is prepared-image acceptance; it does not prove the default source-build path.

## Evidence and cleanup

Keep failed attempts and dated receipts with exact input and controller hashes, installed package versions, real versus controlled fixtures and independently confirmed cleanup. [The 2026-10-22 matrix](../.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json) remains historical. Current acceptance requires a fresh run after runtime dependencies change.
