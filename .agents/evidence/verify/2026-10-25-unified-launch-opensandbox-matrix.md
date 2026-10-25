# Specification 5 OpenSandbox source-candidate matrix

Status: PASS for the exact source-launch and consumption scope below.

## Execution and provenance

The real Docker-backed OpenSandbox [manual run 40177005215](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/40177005215) completed successfully on 2026-10-25. All 46 catalog source recipes used `template launch` without a workflow selector. This record preserves the existing run; it does not describe a new cloud experiment.

| Input | Exact value |
| --- | --- |
| Distribution | Source candidates, not public npm/PyPI installation |
| Templates | `1d2953e16eec96da6c9c8a0a631220e2933c2aaf` |
| CLI | `ea28f207c8a0016cf798f5a355e3c363c7c936f4`, reported version 0.5.0 |
| Python client and host server distribution | `ff073167f8993a5c580c78cccccd5779db1f5836`, reported version 0.4.0a1 |
| Providers | `ebfb1c1554a567585e337f2e68cb3d449d5414b1` |
| Provider and endpoint mode | `opensandbox`, `direct` |
| Matrix input | `templates=all`, `distribution=source` |

Receipts retain the launch input digests and successful runtime source-identity check. In-image server pins remain defined by each template's Dockerfile at the recorded checkout; the host package version does not replace those pins.

## Results and cleanup

- PASS: 46 of 46 template launches and 73 declared smoke definitions.
- PASS: 219 named-command calls through CLI, Python client and direct host HTTP: 67 smoke definitions have explicit `expect` assertions (201 calls), and six check a nonempty result (18 calls).
- PASS for every template: rejection of a wrong service token, runtime source identity and SDK exec/file round trip.
- PASS: all 46 manifest SHA-256 values match the migrated manifests at final template PR head `ecf15959e2620402d6d497b1378e00c39a16fc78`. Source directories were unchanged between the matrix input and that head.
- PASS: independent absence checks for all 46 sandboxes and their prepared artifacts. Retained artifact count, uncertain cleanup count and artifact cleanup failures are all zero.

The separate final-head PR CI had 54 successful checks and one conditional skip, including all 46 image builds. [PR acceptance comment](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/213#issuecomment-6395807324).

## Durable receipts and offline verification

All 46 downloaded sanitized JSON receipts are preserved unchanged in [the receipt directory](2026-10-25-unified-launch-opensandbox-matrix/), together with the [receipt index](2026-10-25-unified-launch-opensandbox-matrix/summary.json) and [independent verification summary](2026-10-25-unified-launch-opensandbox-matrix/verification.json). They contain no raw credentials or private endpoint logs.

From this repository, with the pinned checker dependencies installed, recheck receipt coverage, actual source pins, smoke definitions, manifest hashes and cleanup:

```bash
python3 -m pip install -r scripts/requirements-spec.txt
python3 .agents/evidence/verify/2026-10-25-unified-launch-opensandbox-matrix/verify_receipts.py
```

The verifier intentionally fails if later template manifests no longer match this dated experiment. Use the record's repository revision for historical verification. Receipt inspection is offline evidence validation, not a new provider launch.

To repeat the actual cloud experiment, dispatch [public-template-launch.yml](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/blob/1d2953e16eec96da6c9c8a0a631220e2933c2aaf/.github/workflows/public-template-launch.yml) at the recorded template commit with the source distribution, provider, complete template selection and exact consumer/provider revisions above. A new run requires its own evidence and independent cleanup.

## Limits

This matrix verifies CLI source launch plus Python client connection/calls. It does not establish published-package installation, the later SDK `TemplateLauncher`, managed catalog launch, Express/E2B execution, real-model tasks, PTY or every native interpreter/desktop interface. Older two-platform and managed receipts keep their original format and API scope. No historical receipt was overwritten or relabeled.
