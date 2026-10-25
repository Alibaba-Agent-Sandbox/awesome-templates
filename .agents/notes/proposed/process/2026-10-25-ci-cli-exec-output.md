# Verify CLI process output through its explicit JSON contract

Status: proposed

## Problem

The public source matrix reached CLI process/file checks after successful source launch and application smoke, then compared CI-selected JSON with plain text. Original public CLI 0.5.5 / SDK a6 failures and independent cleanup remain recorded.

## Decision

For OpenSandbox, use the existing global JSON option and require exit_code zero and stdout42. Express standard exec uses its existing text route, requires stdout42 and relies on the adapter to reject any nonzero process exit. Preserve Unicode upload/download, independent SDK byte checks and cleanup. Do not add native forwarding or alter the CLI automatic CI output contract.

## API Design

No public product API, template source, version or workflow changes. The existing CLI adapter follows the actual provider-selected dispatch: OpenSandbox generic exec parses explicit JSON, while Express standard exec rejects that native global flag and uses text.

## Alternatives considered

Accepting arbitrary text or JSON would hide mismatches. Disabling CI globally or adding native forwarding would change the tested contract. The initial unified-JSON candidate incorrectly assumed that the generic formatter owned Express exec too; actual public CLI dispatch rejected --json before backend access. The narrow existing-provider selection preserves both actual command surfaces without fallback parsing.

## Dependencies

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/226

https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40233330458

## Test Strategy

Exercise the existing helper in CI and ordinary output simulations, reject nonzero exits and wrong stdout, retain Unicode/partial-upload cleanup negatives, and run the current public-launch regressions. After normal CI/review/merge and official CLI patch publication, dispatch a new complete public-source matrix rather than rerunning old failed jobs.

## Acceptance criteria

Targeted regressions and latest-head gates pass. New cloud evidence preserves original failures and independently confirms owned cleanup. No template capability PASS follows from a verifier-only local pass.
