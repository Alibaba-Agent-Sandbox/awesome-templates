# Decision: Exercise both images for each Agents API Harness

Status: proposed

## Problem

The image workflow still selected the Server image by the retired `agents-api` directory name. After the rename none of the six recipes exercised the deployed Server image or checked its installed Harness under the Guest image user.

## Decision

Use the managed Serving recipe and its checked-in Harness descriptor to select the paired Server build and Guest binary/version smoke. Verify the exact paired Client import and version as the image user.

## API Design

The published Dockerfiles and exact PyPI pins retain their existing inputs. The keyless image worker probes each descriptor's binary with `--version`, checks its version, and checks the bridge independently.

## Alternatives considered

A duplicate list of six names and versions would drift from the descriptors. Source-built SDK wheels may support a separately labeled prerelease image check; published image checks still need the public artifacts.

## Dependencies

[Templates PR #312](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/312), [SDK runtime PR #165](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/165).

## Test Strategy

Use all six source manifests plus ordinary Codex and Python control recipes. Run the workflow's shell syntax checks and the existing standalone Dockerfile shell regression.

## Acceptance criteria

Each family member selects both actual image builds. Both public runtime versions, the installed native binary and the non-root user must pass CI after package publication.
