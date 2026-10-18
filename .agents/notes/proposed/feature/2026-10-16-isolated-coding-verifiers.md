# Decision: Isolate coding acceptance from writable Python startup and standard-library shadows

Status: proposed

## Problem

Independent cross-review reproduced a false coding pass: an agent could add `unittest.py` that printed the expected test summary while leaving an original input incorrect. The existing held-out inputs omitted the original positive case, so both gates could pass. A writable `sitecustomize.py` could similarly intercept calculator imports. The affected Gemini and Qwen HTTP verifiers needed stronger target-side verification. Refs [Gemini Issue #30](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/30) and [Qwen Issue #26](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/26).

## Decision

Use isolated Python (`-I`) with a clean environment for baseline, original-test rerun and held-out verification. Import the system unittest before adding the target project to sys.path; restrict discovery to the preserved original test file. Require baseline exit 1, AssertionError and three executed tests. The separate isolated verification script loads the source by absolute path with importlib, checks all original cases plus held-out cases and requires the fixed script's exact completion output. Preserve prior evidence as historical source, and record new verifier hashes and new runs separately.

## API Design

No product API changes. Only `gemini/e2e_test.py`, `qwen-code/e2e_test.py` and their protocol regressions change. Target-side files/process APIs, remote credential inspection and forced-off behavior remain intact. A simulated model transport is not real-model acceptance.

## Alternatives considered

An environment-cleared Python process alone still imports cwd modules. A random response marker or additional held-out inputs cannot prove the preserved original tests ran. Instead, isolate startup/import paths and check original cases independently as well as through unittest.

## Dependencies

Existing server files and shell APIs, target Python supporting `-I`, the preserved source/tests, pinned upstream CLI for product acceptance, and genuine model credentials for real-model L3. The previous Qwen real-model acceptance remains evidence for its previous verifier/source, not these new hashes.

## Test Strategy

Each template adds six real subprocess scenarios: incorrect/correct source combined with fake `unittest.py`, import-hook `sitecustomize.py`, or no shadow. Only transport and model edits are simulated; actual emitted target shell commands run in real temporary directories. Incorrect original positive input must fail original and held-out gates even if the report/marker exist and other inputs are correct. Correct code must pass in all three cases; startup hooks must not execute. Run both template checker/L0 contracts again using actual pinned CLIs.

## Acceptance criteria

- Both templates reject writable Python shadows using actual subprocess verification.
- Correct source still passes; forced-off and missing-target-key controls remain covered.
- Actual local HTTP L0 passes with model explicitly skipped.
- New scoped hashes/evidence distinguish this revision from historical real-model runs.
- Real-model/image/cloud acceptance and PR/CI/review/merge are reported separately and remain required where applicable.

## Evidence

[Verification](../../../evidence/verify/2026-10-16-gemini-qwen-isolated-verifier.md). Coordinated cross-review also corrected OpenClaw's SDK deadline-name collision and owned-descendant termination; OpenClaw's own records describe those separately.
