# Build templates with Agent Sandbox platform steps

Agent Sandbox's `abx template deploy --build steps` sends the base image and an
ordered step list to Alibaba Express. It needs no local Docker daemon or ACR
push. [中文](platform-steps.zh-CN.md).

## Requirements and build-mode selection

Configure the existing authorized Express sandbox API and Alibaba control-plane
credentials in the environment. Use a CLI revision whose deploy, official
template inventory/info/delete and sandbox commands match the
[canonical harness](../scripts/express_e2e.py). The source CLI described in
[installation](using-templates.md#installation) supports those interfaces.
Do not infer compatibility from the displayed package version alone: the
published 0.4.0's standard template-list/create interface differs from the native
interface used by this harness. The 0.3.0 standalone release requires the official
Alibaba SDK modules to be available; a verified source build supplies them.

`auto` selects a Dockerfile when present. Explicit `--build steps` selects the
manifest's steps even if a Dockerfile exists. Never combine it with
`--acr-namespace` or `--legacy-api`. Sandbox creation does not select a build mode.
The CLI owner's [build-mode contract](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/blob/main/docs/en/design/template-build-modes.md)
describes the wire expansion; actual provider instruction arguments still need
provider verification. Express ENV uses alternating key/value arguments: for
example `{type: ENV, args: [LANG, C.UTF-8]}`. A single `LANG=C.UTF-8` argument was
rejected in the real 2026-10-19 pilot; that failed attempt remains recorded.


For CLI0.4.1, select the existing project surface explicitly before all other root options:

```bash
export ABX='abx --native'
python scripts/run_steps_e2e.py python-hello --sandbox-create sdk
```

The actual installed0.4.1 candidate passed real step READY/SDK creation/CLI+SDK/cleanup. The public entry is owned by [CLI PR90](https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/pull/90); its default standard commands remain unchanged.

## Preparing an actual template

Platform steps do not upload local COPY inputs. Generate a standalone staging
manifest from the selected catalog directory instead of silently dropping source:

```bash
python scripts/prepare_steps.py python-hello --output /tmp/python-hello-steps-review \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
```

Use a new output directory. The optional server commit matches the existing
image CI's injected server source and is recorded as an override; omitting it
uses the Dockerfile's own immutable fallback. The materializer preserves ordered
RUN, ENV, WORKDIR and USER instructions, interprets heredocs/continuations, and
transfers only explicit public COPY inputs with hashes and file modes. Inputs
are compressed inline when they fit. Larger profiles fetch the exact public
checkout archive and verify every copied file before publication; publish that
immutable commit before a cloud build. Transient archive failures retry within
a bounded budget. Build steps explicitly select root for the Docker dependency
installation profile, then return to USER user for runtime. It replaces
the optional local-wheel branch with its pinned public-source install. USER user
remains required. EXPOSE is represented by the unchanged manifest ports.

The accepted profile is a single Alibaba FC base stage. Unknown instructions,
unreviewed wheel fallback shapes, external/symlink/glob/secret-named COPY inputs,
oversized files, floating commits and output-directory reuse are rejected.
Express limits the serialized steps to 16 KiB. RUN/source payloads are compressed,
and preparation rejects steps above a conservative 15,000-byte budget before
making any cloud request. Provenance records the wire size and COPY source commit.
Native ENV does not consistently feed subsequent RUN processes. The adapter
exports the declared build environment and working directory explicitly for RUN,
and resolves runtime PATH against the actual v0.0.49 Express base PATH observed
in a clean owned probe. A different base tag requires its independently verified
`--base-path`; local controller PATH is never substituted.
This is a catalog-profile adapter, not a general Dockerfile implementation.
Inspect `steps-provenance.json` and the generated manifest before deployment.
Generated source is public code, never credentials or runtime model settings.

## Deploying and running commands

From the source checkout, use the full canonical step acceptance path:

```bash
python scripts/run_steps_e2e.py python-hello \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
```

Set `ABX` to the verified CLI command in the environment if it is not on PATH.
Pass more catalog names or `--all` for a serial complete-catalog run. This is a
real paid cloud operation. It creates uniquely owned resources and keeps private
recovery journals outside the checkout; it does not send credentials to Actions.

For a prepared directory, the equivalent underlying acceptance command is:

```bash
python scripts/express_e2e.py /tmp/python-hello-steps-review --build steps --push-retries 0
```

The runner calls real `abx template deploy --build steps`, records the returned
template ID privately before polling official GetTemplate until READY, creates a
new sandbox, invokes every smoke through CLI and SDK, and independently confirms
owned sandbox/template absence after cleanup. A submitted response, failed build,
unknown state, smoke error, timeout or uncertain cleanup cannot write a pass.
Recovery uses the existing `--recover-intent` path and exact owned alias.

For manual operation, deploy the staging directory with
`abx template deploy /tmp/python-hello-steps-review --build steps -y`, wait for
official READY, then use the CLI/SDK/HTTP calls in the original template README.
Delete only the resources created by that operation. Manual submission alone is
not an acceptance receipt.

## Evidence and limitations

`run_steps_e2e.py` retains a sanitized per-attempt outcome under the original
template's evidence directory, including failures, exact copied-input hashes,
base image and server-source override. A successful canonical receipt includes
`build_mode: steps`, external command results and `cleanup_verified: true`.
Existing receipts are never overwritten. Private CLI/provider logs and resource
IDs are not copied into the repository.

All current Dockerfile profiles can be materialized locally. That statement does
not assert their cloud builds passed. A step deployment proves the generated
recipe at its recorded hashes; it does not prove a local Docker build, reproduce
an untested dependency pin, satisfy an unrun real-model L3, or verify another
provider. Consult the current per-template attempt records and the
[acceptance specification](template-spec.md#test-levels).

## Reproducing the tested native CLI

This pins the actual Linux x86_64 native entry used by these receipts alongside the standard entry. The controller used Node22.22.2/npm; the standalone binary needs these two exact external Alibaba SDK modules. The asset, SHA256 and module combination were actually used. A displayed version alone does not establish interface compatibility. This step downloads public tools without creating cloud resources.

```bash
ABX_NATIVE_DIR="$(mktemp -d /tmp/abx-native-review.XXXXXX)"
curl --fail --location --max-time 120 \
  --output "$ABX_NATIVE_DIR/abx" \
  https://github.com/Alibaba-Agent-Sandbox/agent-sandbox/releases/download/v0.3.0/abx-0.3.0-linux-x64
printf '%s  %s\n' \
  e6d1c46626fd3f48e86b23bc99b0b8d565dfadd3f61a42ea352a27cb637d9cdd \
  "$ABX_NATIVE_DIR/abx" | sha256sum --check
chmod 700 "$ABX_NATIVE_DIR/abx"
npm install --prefix "$ABX_NATIVE_DIR/modules" --ignore-scripts --no-audit --no-fund \
  --save-exact @alicloud/fcsandbox20260509@1.5.1 @alicloud/openapi-core@1.0.8
export ABX="$ABX_NATIVE_DIR/abx"
export NODE_PATH="$ABX_NATIVE_DIR/modules/node_modules"
"$ABX" template deploy --help
```

Then configure the existing Express account in the process environment and run the pinned-server commands above. ABX/NODE_PATH select this isolated tool directory. Use the native acceptance syntax consistently. Remove only your own tool directory after owned cloud resources and private journals are reconciled.

For heavy assets, the separately recorded [CI image acceptance path](ci-image-acceptance.md)
uses real Dockerfile CI export and native image registration, with its own provenance.

## Observed large-asset constraint

On2026-10-19 an actual step-build diagnostic retrieved8MiB in385/398seconds
from the selected code-server/Rust assets, while Go/Hermes source samples took
less than2seconds. This is measured behavior, not a promised throughput limit.
A306.777-second RUN stream deadline failure occurred in browser installation;
it does not establish a universal300-second execution cap. Split build phases,
bound transfers and preserve errors. A timed-out build is not acceptance.
Heavy templates still need their own successful current-profile receipt; a
partial network probe, local install or CI-only build cannot supply it.

Generated steps explicitly assign /home/user/app to user:user before selecting the runtime user. Genuine full Python/Node HTTP workflows exposed root-owned native WORKDIR preventing file writes; COPY file ownership alone was insufficient. Version/basic smoke cannot replace a workspace file roundtrip. Historical failures and basic receipts retain their original scope.

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

## Auditing complete current-version step acceptance

Run `python scripts/step_acceptance.py` to check every current catalog entry. It exits nonzero for missing current-version native step receipts. The audit requires unchanged recorded Dockerfile/runtime input hashes, every current CLI/SDK smoke call and independent resource absence; historical versions and image-only successes cannot pass. This audit does not execute cloud requests or certify Docker/model acceptance.

Add `--http` to `scripts/run_steps_e2e.py` to execute the original complete external HTTP controller within the canonical owned sandbox. The receipt separately records controller hash, pass/fail/skip counts and exit status. Model cases remain explicitly off/NOT_RUN; a skipped model is not L3. Missing local controller prerequisites fail before cloud creation.

For Goose, Crush, code-server, Polyglot, Aider, SWE and Hermes, `--asset-transport parallel` enables bounded parallel byte-range transport for their exact official archives. Every response must match its requested Content-Range, all bytes must match the pinned size/budget and SHA256, and the original unchanged installer still checks integrity/version/extraction. The temporary root-only cache and its process-local Python URL adapter are removed before USER user. Hermes uses the documented local-file uv mirror with original Python3.14.6 and uv0.12.3 pins; its generic GNU architecture assets and official metadata source are recorded. Its original compound installation is split into bounded ordered phases. DeepAgents, OSWorld and browser-use use a temporary uv0.12.3 installer for the unchanged hash-locked Python graph and separate original installation phases; that build tool/cache is removed before runtime. Other profiles retain direct transport. No substituted artifact or operator credential is introduced. The materializer receipt records the helper hash and exact asset metadata. A failed/unsupported range or checksum cannot publish acceptance.

```bash
python scripts/run_steps_e2e.py goose --asset-transport parallel --http \
  --sandbox-create sdk --timeout 3600 \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
python scripts/step_acceptance.py
```

### Temporary private OSS transport

For the complete heavy-archive path, install the optional local controller SDK with `python -m pip install -r scripts/requirements-steps-cache.txt`, then select `--asset-transport oss`. This creates a uniquely owned private bucket in the same Alibaba region/account, checks official archive hashes before upload and after build download, and passes only short-lived GET authorization in the private execution recipe. Public source/provenance and Actions never receive signed URLs or operator secrets. Bucket/object ACLs remain private; no account policy changes. A pass is published only after independent sandbox/template AND exact object/bucket absence. Unknown creation responses retain a private recovery intent and cannot certify cancellation. Cache creation/upload/download/deletion are real cloud operations.

```bash
python scripts/run_steps_e2e.py goose --asset-transport oss --http \
  --sandbox-create sdk --timeout 3600 \
  --server-commit e2cb27e24fde0a67112f82b8d44af463445a5d1a
```

The original direct mode remains the default. OSS mode supports reviewed archives, the exact uv0.12.3 bootstrap and OSWorld's pinned Playwright1.58.0 browser archives. Original installer, hash-lock, version, extraction and runtime-user requirements remain enforced. Temporary browser serving binds loopback only, exposes verified archive paths only, and closes before the build returns. Browser digests are measured from the upstream pinned-client URLs; they are not labelled upstream-published hashes.

Publish the exact adapter source commit before cloud execution. Larger profiles fetch that public immutable helper and verify its SHA256 rather than exceeding the provider wire budget; unsupported/unpublished profiles fail closed. `ABX_STEP_LOCAL_ARCHIVE_DIR` optionally reuses controller-local files named by SHA256; every reused byte still must match the original pinned size/hash before upload. It never reads a caller credential file or changes runtime package requirements.

The [current-source matrix](../.agents/evidence/verify/2026-10-20-complete-platform-steps-matrix.json) records the latest scoped step checkpoint; rerun the audit after catalog/source changes. The final Hermes path also caches its immutable upstream commit archive with a controller-measured SHA256; OSWorld's OSS profile uses the regional public PyPI mirror while retaining every original version, --require-hashes and --no-build-isolation. Browser-use retains its original Python3.13, hash lock, Chromium --no-shell and8GiB rootfs assertions; its reviewed public PyPI/bootstrap/browser transports are build-only. This changes transport only. Model SKIP remains NOT_RUN, and earlier image/model receipts are not reclassified.
