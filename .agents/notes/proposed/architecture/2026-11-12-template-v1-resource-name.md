# Decision: Keep engineering directory names out of the public resource contract

Status: proposed

## Problem

The v1 root-name pattern exempted _skeleton solely to match this repository's authoring
directory. The actual resource planner correctly expects an ordinary63-character ASCII name.
An engineering directory is not a product resource type or a naming capability.

## Decision

Remove the _skeleton root-name exemption. All public resource names use the same bounded
ASCII pattern. The authoring directory may remain _skeleton while its resource is named
example. Its engineering checks and catalog/design exemption must use directory identity.
This producer commit does not include that dependent repository migration.

## Alternatives considered

Teach every runtime planner the author directory exception: leaks repository layout into
all clients. Rename the actual engineering directory: unnecessary public-source churn.
Keep a normal resource name and directory-scoped tooling: minimal, explicit ownership.

## Dependencies

Parent and independent CLI review approved this correction. The active skeleton and its
fixtures/tooling migrate separately before catalog activation. Native template.reference
identifiers keep their existing Provider-owned semantics. Tracker:
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Test Strategy

Add a shared _skeleton resource-name rejection vector. Keep the existing valid63-character
name, invalid64-character name and long native reference regressions in both languages.

## Risks and Limitations

This does not rename any cloud object or grant current-format qualification to historical
fixtures. Active source migration must close the explicit authoring-tool dependency.

## Rollback Plan

Revert the isolated naming correction with synchronized consumers. Do not add runtime
exceptions merely to keep an engineering fixture unchanged.
