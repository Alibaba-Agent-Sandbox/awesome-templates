# Source image acceptance

[中文](source-image-acceptance.zh-CN.md).

2026-10-22 results: Express regular-image runtime/cleanup46/46, complete HTTP46/46; original OpenSandbox source-image CLI/SDK, complete HTTP and independent cleanup46/46. [Per-template matrix](../.agents/evidence/verify/2026-10-22-source-image-backend-matrix.json).


Issue [185](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/185)
tracks all46 source templates on Express regular images and native OpenSandbox
Docker. Existing steps receipts remain separate. A workflow, build or managed
interpreter pass does not certify these source runtimes.

## Express regular images

Use **Template images (L1)** workflow dispatch with the desired catalog names and
`export_images=true`. After that exact-source run succeeds, use
`scripts/run_ci_image_e2e.py TEMPLATE --artifact-id ID --crane PATH --sandbox-create sdk`
with the verified native CLI, paired SDK and account credentials in the operator
environment. Credentials are never copied into Actions. The existing controller
checks the archive/source/SDK/digest, transfers to a nonce-owned private ACR
repository, registers the real image with `abx template from-image`, waits for READY, executes CLI and SDK smoke,
runs the unchanged complete HTTP controller and independently checks owned
sandbox/template/registry absence. It publishes receipts only after cleanup.

OpenClaw uses a generated test token; Cursor uses a synthetic invalid key. An
owned sibling server receives those fixtures because a prewarmed server does
not inherit create-time environment. OSWorld/Chrome desktop checks and native
Cursor/Devin authentication refusal are required; version-only/skip-only success
does not qualify them. Missing vendor/model accounts remain explicit L3 limits.

For a bounded operator batch, use the successful export run ID:

```bash
python scripts/run_image_e2e_batch.py --workflow-run EXPORTED_RUN_ID \
  --crane /path/to/verified/crane --private-root /private/template-acceptance \
  --workers 4 --output /private/template-acceptance/progress.json
```

The runner skips sources already qualified against current image inputs and the
complete HTTP controller. `--templates` selects explicit comma-separated names;
`--rerun` explicitly includes already qualified sources. Workers are isolated
processes, at most four. Unknown cleanup stops new operations while existing
owned runs finish. Private consoles/recovery journals stay outside the checkout;
only sanitized progress and template-local receipts are public evidence.

## Original OpenSandbox Docker

Dispatch the same workflow with explicit comma-separated catalog names,
`test_opensandbox=true` and `export_images=false`. The selected image is built
from the normal template Dockerfile with its pinned server SDK wheel. A separate
fixed-source original OpenSandbox server, provider and CLI then run on the
isolated Docker runner. No cloud/model account is needed.

`scripts/opensandbox_template_e2e.py` verifies image identity and source bytes,
creates through the Agent Sandbox SDK, observes the actual Docker container,
checks SDK shell/files, starts the template service as the non-root user, calls
every manifest smoke through the real provider CLI (`abx exec` calling the
guest named HTTP API) and SDK, then runs its unchanged complete HTTP test
against the real guest bridge address. It verifies SDK NotFound, Docker absence,
engine reaping and original-server shutdown. Each selected template emits its own
sanitized receipt; private IDs, endpoints, journals and raw logs are not uploaded.

This qualifies the named template API. The provider's generic `run_code` remains
unsupported (`E8004`) and is checked as such. Manifest `code` requirements still
prevent CLI `template launch` where that provider capability is absent; this
native SDK source-runtime test does not remove the capability gate or certify
that launch path. The managed original interpreter's native code API is separate.

## Evidence and cleanup

Keep timestamped template-local receipts, failed attempts and the owner summary.
Bind every pass to current source/build inputs, controller hash, SDK and image
identity. Preserve earlier records. Delete only resources owned by the run;
unresolved cleanup prevents a pass. The acceptance work remains incomplete until
all46 current sources have both requested backend receipts and complete HTTP.

The legacy execd pilot failed when explicitly repeating the image user through
SDK user switching. The source profile instead preserves image USER and verifies
its actual numeric UID is nonzero. Explicit user switching is not qualified.
