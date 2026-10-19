# Decision: Check controller prerequisites before image acceptance
Status: proposed

## Problem

Corrected OCR image registration reached official READY and real CLI OCR smoke passed, but the external controller failed before assertions because local Pillow was missing. Resource cleanup succeeded; the failed attempt remains failed. The report previously conflated any test failure with unknown cloud cleanup. Secondary runtime ports also need authoritative SDK URLs.

## Decision

Check external controller imports before artifact/cloud operations. Preserve an independent cleanup-readback result even when acceptance fails. Pass actual SDK port URLs for code-server and Next/Vite to their external verifiers; never rewrite hostnames. Add behavior regressions and retain the original OCR failure.

## API Design

No image/runtime command or source contract change. Missing modules produce a sanitized failed-attempt record before mutation. Cleanup_verified reflects the canonical independent callback, not the acceptance exit code. Provider PASS still requires every test, unchanged registry tag digest and independent cleanup.

## Alternatives considered

Silently skipping HTTP, treating CLI smoke as full acceptance or relabeling the failure would hide missing gates. Installing packages after cloud mutation wastes resources. Guessing provider secondary URLs is not a contract.

## Dependencies

Merged image acceptance PR129; paired SDK network.get_url; Python import discovery. Corrected OCR profile in PR130 and genuine Hermes image/model evidence PR132.

## Test Strategy

Missing-controller-dependency regression forbids artifact/network calls; targeted source/tag/archive/cleanup suites; docs/spec; actual corrected OCR rerun and secondary-port product acceptance.

## Acceptance criteria

No cloud mutation for known missing controller prerequisites; no failure-to-PASS relabeling; cleanup evidence accurately separated; provider-owned actual port URLs; current-head CI and ordinary merge.
