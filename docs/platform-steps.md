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
