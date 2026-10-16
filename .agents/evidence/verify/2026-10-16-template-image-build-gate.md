# Template L1 image-build gate preparation

Date: 2026-10-16
Result: PARTIAL

## Scope

Uncommitted .github/workflows/image-build.yml, Amp SDK wheel-compatible Dockerfile,
agents-cli pinned Node24.16.0 Dockerfile and bilingual README/design updates, plus
owner engineering records. The existing e2e workflow is preserved. Initial base
HEAD:2acb53481739e9585803076dd4c05ce5c2048219. No local commit/push is claimed here.

## Verified review facts

- Actual CLI source DockerBuilder.injectSdkWheel builds the explicit server-sdk
  source with pip wheel --no-deps and copies wheels to the template root. The new
  gate uses that path with public SDK commit
  e2cb27e24fde0a67112f82b8d44af463445a5d1a.
- Actual CLI materializedDockerfile defaults FROM placeholders to cn-hangzhou and
  v0.0.49. The gate replaces those placeholders only on the FROM line and leaves
  SDK install logic intact, with a wheel present so COPY is never an empty glob.
- Calling actual compiled rewriteDockerfileForServerInstall on the original
  agents-cli/Amp Dockerfiles with a wheel reproduced malformed physical-line
  rewrites: COPY/RUN inside a continued if/else instruction, and an orphaned
  continuation echo respectively. This belongs to the CLI owner and was reported
  separately. No CI rewrite hides that defect; image L1is not CLI materialization.
- Actual installed Qwen0.23.0 package metadata requires Node>=22. Agents-cli's old
  Dockerfile used base Node20, whereas shared CI uses Node24. The image now uses
  the reviewed official Node24.16.0 installer and architecture-specific SHA256
  values already verified for OpenClaw. No image success is inferred from this fix.
- Matrix covers16product templates, excluding _skeleton, max-parallel4, fail-fast
  false. Triggers are PR,main push,manual; no image push,secret/env-file inputs or
  cloud/model provider actions are present. Container diagnostics have networking
  disabled and do not submit a model turn.

## Executed preparation checks

PASS: YAML parsed; matrix compared exactly with all16awesome-templates.yaml paths;
parallel limit asserted; bash -n for every run block; ast.parse for every embedded
host/container Python block. Exit0.

PASS: python scripts/check_template.py agents-cli and amp, each conformant/exit0.
PASS: scoped git diff --check and engineering/document relative-link checks,exit0.

The official installed Hermes CLI version was inspected while reviewing the
version check: Hermes Agent v0.22.1 with upstream297552a9 and Python3.14.6. The
server registry API was checked directly: default_registry() returns the registry
instance; the container smoke uses its supported get(...).fn dispatch. These are
host/source checks, not an executed container smoke.

## Remote state and limits

PENDING: all actual docker build --progress=plain jobs, image-user assertions,
installed-pin checks and keyless container commands. This environment has no
Docker executable/engine; no Docker test or image build was run locally. The root
integrator will commit/push the workflow and inspect each actual remote result.
A prepared workflow, queued job or green host test is not L1acceptance.

L2provider deployment and L3independently verified real coding remain separate
required gates. No provider pass file,tested_on entry or official status was added.
No cloud resource,model call,published image or package release was created.

All modifications are repository source/docs/records. Workflow contexts and images
are created only when the actual remote job executes; no fake Docker runner was
used for validation.
