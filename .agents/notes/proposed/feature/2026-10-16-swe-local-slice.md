# Decision: Real single-instance SWE local evaluation

Status: proposed

## Problem

The previous backlog treated missing nested Docker as a blocker for every SWE workflow. Issue35 explicitly allows a non-Docker slice, but an ordinary coding CLI or a success marker would not satisfy actual instance preparation, patch artifacts and FAIL_TO_PASS/PASS_TO_PASS evaluation.

## Decision

Support only real SWE-bench Verified `pallets__flask-5014`, pinned base archive and original benchmark test patch/test IDs, without the gold solution. Use actual official mini-swe-agent2.4.6 CLI and a documented LocalEnvironment extension preserving shared process-group ownership. Require explicit model shell permission. Rebuild an independent original checkout and venv for evaluation, admitting only the supported source diff. Require the actual one-failure/59-pass baseline and exactly60 passing declared identities for a repaired slice. Report no official benchmark score. Preserve HOME and use the upstream private config directory entry point. Final sandbox destruction remains the boundary for arbitrary shell and deliberately detached children.

## API Design

`swe_version`, `swe_setup_check`, `swe_prepare`, `swe_run_agent`, `swe_evaluate`, `swe_report`, `swe_cleanup`; see [complete API](../../../../swe/README.md#command-reference). Default execution permission is false; IDs are opaque, same-run operations are locked, errors omit upstream logs, and sensitive configured values refuse patch persistence. No arbitrary caller test shell/URL or gold patch API.

## Alternatives considered

Keep all SWE work blocked: contradicts the feasible local backend and Issue35 acceptance scope. Run official Docker evaluation: requires unavailable nested Docker and original per-instance environment. Substitute a synthetic toy task: insufficient real-instance proof. Use unmodified local action sessions: separate per-action sessions escape the outer ordinary process group cleanup. Treat shared process group as a hostile-code isolation boundary: incorrect; tasks/models must be trusted and VM destroyed afterward.

## Dependencies

Alibaba base/Python3.13/Node20, pinned server source e2cb27e24fde0a67112f82b8d44af463445a5d1a, official mini-swe-agent2.4.6/LiteLLM1.82.6, separately pinned Flask evaluation packages and archive, real OpenAI-compatible model. Dataset revision c104f840cc67f8b6eec6f759ebc8b2693d585d4a. No new host/global dependencies.

## Test Strategy

Real process cleanup/timeout, permissions/type/path/lock/privacy tests, exact JUnit identity/skip/duplicate/missing-test negatives, HTTP acceptance false-green/missing-target-config controls. Actual owned Express baseline→real model edit→independent60tests→remote patch/report retrieval. Image build and canonical Express deploy remain distinct gates. Retain failed attempts separately and verify owned cleanup.

## Acceptance criteria

Scoped conformance/tests/docs/translations/provenance/license checks; real source and built-image acceptance, requiredCI/review, canonical Express deploy evidence before promoting provider verification. Official Docker scores, broad SWE-agent/SWE-rebench and arbitrary instances remain incomplete under https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/35. Do not close the cross-scope Issue or mark catalog verified from supplemental source evidence.
