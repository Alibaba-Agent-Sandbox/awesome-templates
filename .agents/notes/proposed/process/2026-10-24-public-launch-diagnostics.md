# Public launch diagnostics and native cleanup

Status: proposed

## Problem

The first real two-platform pilot passed Express application calls but failed its
prepared-resource cleanup check. The cleanup wrapper mixed standard and native CLI
surfaces and passed an unsupported native `--format` option. OpenSandbox failed during
launch with only an exit code retained, obscuring the failure stage. Refs
https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/203 .

## Decision

Select `--native` as the first CLI argument for Express template deletion and listing,
use the existing global `--json`, and retain independent absence checks. Reports add
controlled phase/category values, stable SDK codes, numeric HTTP status, and the
random test alias for precise recovery. Dynamic exception messages and private CLI
logs remain excluded. Keep the original failed reports unchanged.

## API Design

Only the acceptance runner changes. Template manifests, runtime commands, provider
contracts, and released CLI/SDK artifacts remain unchanged.

## Alternatives considered

Do not accept successful application calls as successful cleanup. Do not publish raw
CLI output to debug a cloud failure. Do not replace the failed server-proxy path with
a direct-address success without separately recording which path was exercised.

## Dependencies

Actual pilot https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40107869809 .
The OpenSandbox proxy failure still needs evidence; adding a guessed authentication
header is not justified by the pinned server's single-tenant implementation.

## Test Strategy

Regress native argument position, exact list options, independent readback, and the
allowlist that excludes resource IDs and secret messages. Repeat the real two-platform
pilot with the exact same producer refs after reviewing this fix.

## Acceptance criteria

Owner checks pass, failed evidence remains available, the real pilot is repeated,
and every success claim includes owned-resource cleanup. Full 46×2 acceptance stays
open in Issue #203 until executed.

The raw HTTP request now sends the existing X-Access-Token application header when the gateway has not supplied one, alongside Bearer. It never replaces a gateway header, retries authentication, or falls back to another endpoint. Negative authentication reconstructs both application headers with the wrong token so the positive X-Access-Token cannot invalidate the negative test.
