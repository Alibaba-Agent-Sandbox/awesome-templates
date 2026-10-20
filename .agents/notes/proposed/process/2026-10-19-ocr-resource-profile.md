# Decision: Valid OCR Express resources
Status: proposed

## Problem

Actual immutable CI image registration returned template error: CPU2 and memory1024MB violate the provider minimum memory/CPU ratio1. A manifest-only source checker accepted that pair. No sandbox or HTTP acceptance ran. Owned template and private registry deletion were independently confirmed.

## Decision

Use CPU1 and memory1024MB for OCR, matching its lightweight single-process use. Preserve the failed image receipt and repeat exact-source export/real cloud acceptance. No runtime command or dependency changes.

## API Design

Only template resource declaration changes. Existing OCR command contracts remain.

## Alternatives considered

Increasing memory to2048MB would also satisfy the observed minimum but is unnecessary for the selected single-process OCR smoke. Do not silently override manifest resources in deployment tooling.

## Dependencies

Issue57 and119; actual provider image registration and exact-source CI export.

## Test Strategy

Target strict conformance/doc links; actual image export and genuine native READY/CLI/SDK/full OCR HTTP acceptance; independent owned cleanup.

## Acceptance criteria

Passing declared CPU/memory profile on Express, preserved failures, current-head CI and ordinary merge before closing Issue57.
