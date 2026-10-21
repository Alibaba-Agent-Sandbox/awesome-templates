# Decision: Verify the managed OpenSandbox interpreter on a real isolated Docker backend

Status: proposed

## Problem

Issue34 remains open because no usable OpenSandbox service is configured in the operator environment. Local HTTP fixtures establish client contracts but cannot verify the original code-interpreter image, real server or kernel persistence.

## Decision

Run a credential-free hosted Docker acceptance job using the exact original upstream server/SDK source, exact Agent Sandbox SDK/CLI/provider commits and the original published interpreter/execd images. Resolve and record immutable image digests before creation. Use Agent Sandbox SDK creation, real shell/files and explicit unsupported generic interpreter behavior. Connect the original OpenSandbox SDK to the same sandbox ID and verify native interpreter execution, persistent context, isolation, program failure and context deletion. Independently confirm SDK NotFound and Docker container absence. Keep the managed entry unverified until actual successful receipt/cleanup is available.

## API Design

No public runtime or provider capability changes. The standalone controller emits sanitized receipts, pins, observed public image digests, check labels and cleanup results. Native OpenSandbox interpreter success is separate from Agent Sandbox's unsupported native code.interpret extension and Express source-template steps. No cloud/vendor/model credentials are provided.

## Alternatives considered

Reusing local HTTP fixture results as native proof would be false. Waiting solely for an operator endpoint leaves useful hosted Docker testing unattempted. A counterfeit Express Dockerfile would misrepresent the externally owned image.

## Dependencies

Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/34. Original OpenSandbox30348cbdfe4b9cfd49e0963617aed357a8f1ac4c; provider9d2cf07467ff0e36303e4c80cbfe9fbf0fd70c6d; CLIc8e8ad784323b8903505442cbc77d433a0d0367a; SDK33f857f5a79fd10326652e9d03f15f3621d6b848. The original uv lockfiles and CLI npm lockfile are used. Linux hosted runner requires Docker and sufficient image storage/network access.

## Test Strategy

Local diagnostic redaction/bounds and controller syntax checks; full documentation/record checks; actual hosted server/image/Agent Sandbox SDK/native interpreter/independent cleanup job. An offline/missing-Docker run is not a native pass. Failures remain failures with safe receipts and no qualification claims.

## Acceptance criteria

Real original components execute successfully, every native check passes, exact tested pins/digests and cleanup are recorded, both managed READMEs/catalog/evidence reflect only observed scope, required current-head CI and review pass, and the owner PR is actually merged. The external managed image is never presented as an Express source template.

## Evidence

See [verification](../../../evidence/verify/2026-10-21-opensandbox-native-acceptance.md).
