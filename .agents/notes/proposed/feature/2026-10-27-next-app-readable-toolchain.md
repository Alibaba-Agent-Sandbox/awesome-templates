# Decision: Keep the installed preview toolchain readable by runtime user

Status: proposed

## Problem
Two real default Next template launches failed toolchain_versions: root-owned
package.json copied with restrictive0600 context mode was unreadable by user.

## Decision
Normalize public toolchain read/traverse permissions after npm ci, preserving
write ownership. Bump next-app1.1.2 to1.1.3. Add a real restrictive-context Docker
regression that executes version inspection as the non-root image user.

## API Design
No method/argument changes. Existing pinned Next/React/Vite versions and runtime
user remain unchanged. The fix makes existing version/scaffold/preview use work
with restrictive source staging; it grants no new write permission.

## Alternatives considered
Running the service as root, relaxing the operator's private umask, or ignoring
version smoke would mask the image's missing non-root read contract.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/254 and
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244. No new
package dependency. Test base is explicitly resolved using the existing CLI's
materializeBaseImage rule and actual region, not an invented image endpoint.

## Test Strategy
Copy real recipe inputs with0600 mode, build the actual Dockerfile using an
explicit resolved default base, require non-root version inspection and exact
pins, remove only nonce-owned tags and independently inspect absence. Prove the
old recipe fails and the fix passes. Then run actual public launch/core and full
newcomer usage with external preview pages and cleanup.

## Acceptance criteria
Restrictive-context regression and real default provider/business workflow pass;
CI/docs/evidence agree. Keep existing failures immutable and do not promote other
templates from this fix. Full catalog acceptance remains pending.
