# OSWorld actual image and Express verification — 2026-10-16

Status: PASS for the declared browser slice's standalone image and supplemental changed-image Express verification. Canonical deploy L2, model/full benchmark and final PR merge remain incomplete. Refs [Issue 36](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/36), [runtime PR 94](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/94), and the [public result](2026-10-16-osworld-changed-image.json).

## Exact tested image

- Source: `9a53b56c23624b3959da707083f5aa402bacb7bb`; PR merge checkout: `fee18700a24dd5e212bd8b37ca7919a69fe5d727`.
- Actual [L1 run 38863603298](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38863603298), job 116851325574: SUCCESS; only OSWorld was selected. The original standalone Dockerfile built, then ran its real full desktop smoke non-root with network disabled.
- Successful artifact: 12030222981, 870886096 ZIP bytes; Docker archive: 2107649536 bytes, SHA-256 `725e4292eca837599a4fcb1b7f6b330c6641e1f4d2554bb6b61ae6b8d50d9087`.
- Actual registry digest readback: `sha256:d36ac62dba5e78759333092d725709ffacb4a86a2b3538a54b505d42d5d02e41`.
- Platform server source: `e2cb27e24fde0a67112f82b8d44af463445a5d1a`; client/server SDK versions: 0.3.0. Runtime/template version: 1.0.0; provider: alicloud-express; UTC date: 2026-10-16.
- Both complete current-head local workflows succeeded: [PR 38863603277](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38863603277), [push 38863598299](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38863598299).

## Actual changed-image cloud checks

The host downloaded no large ZIP/tar. Bounded HTTPS ranges checked exact 206/Content-Range/length/offsets, expected three ZIP members, bounded metadata and SHA entries, ZIP CRC, source/run/checkout and SDK provenance. These small range reads did not validate the whole archive. An independently owned Express helper downloaded the full artifact, recomputed the entire archive SHA, then used the pinned official crane binary to push the exact archive and read back the registry digest. A shared flock covered fresh official temporary registry auth through push completion. No GitHub token or Alibaba AK/SK reached the helper; no secrets reached CI.

Official generation-2 CreateTemplate reached READY with the actual OSWorld resources/start/ready configuration. A newly created sandbox ran unchanged image files; no source overlay was uploaded. Nine application files (commands/runtime plus all packaged upstream files, including its whitespace attributes) and all 56 server Python modules matched exact reviewed/pinned bytes.

PASS: SDK, HTTP and CLI each independently invoked the real full desktop smoke. Each required native click/type/hotkey actions, actual upstream PNG and AT-SPI, baseline task score 0, final score 1, independently read browser state, changed pixels and exact full 4096-character Unicode destination readback.

PASS: the original external controller with E2E_REQUIRE_DESKTOP=1 and E2E_RUN_DESKTOP=1 produced 18 PASS, 0 FAIL, 0 SKIP. It uploaded a disposable OSWorld-shaped browser task, observed the failing baseline, decoded the PNG independently, used actual GUI events to complete ASCII/CJK text, received upstream score 1 and fresh real XML, compared PNG hashes and deleted its own fixtures. Successful acknowledgement/markers alone do not contribute to the score or Unicode check.

## Ownership and cleanup

All eight final cleanup flags passed: transfer helper kill ACK and independently listed absence; runtime sandbox kill ACK and independently listed absence; official template delete and independent exact-name absence; unique registry tag and repository GET 404 after deletion. Official inventory validation fails closed for nonarrays, malformed/empty names, malformed owned IDs or duplicate exact-owned names. Nine malformed negative controls and two valid exact-name/absence controls passed. Registry deletion and private-intent removal occurred only after compute/template reconciliation; no OSWorld private journal remains. Resource identifiers, private endpoints, temporary auth and signed URLs are omitted.

An earlier controller was interrupted to reload that stricter inventory validator after it had created a helper. That preparation attempt earned no product result. Its exact helper ID+nonce was independently matched, killed and verified absent, then its unique tag/repository deletion and GET 404 passed. The aborted result is retained separately; it is not counted as image acceptance. Later read-only review did not interrupt the frozen successful attempt.

## Preserved failures and limits

The earlier [cache-path](2026-10-16-osworld-browser-cache.md), [screen/viewport](2026-10-16-osworld-viewport.md), and [workspace ownership](2026-10-16-osworld-workspace.md) image failures remain historical. The real pinned image observed screen/outer 1024×768 and viewport 1024×712 with content offset (0,56); the final gate handles their different meanings. A non-kiosk native diagnostic variant's Tab failure remains recorded and is not a product pass. Historical native crashpad enumeration used its stated source/Chrome version; this cloud acceptance independently proves whole owned sandbox absence, without claiming a new pinned-image per-process audit.

This path used CI image build, daemonless transfer and official registration. The complete local `abx template deploy` command and canonical `scripts/express_e2e.py` L2 runner were not executed. Therefore it does not populate canonical `tested_on` or a Verified provider table, and status stays experimental. No model agent, full VM/Office benchmark, leaderboard score, other provider or permanent public registry/template publication is claimed. Issue 36 stays open.

## Documentation-only follow-up checks

PASS: all 19 strict conformance directories; 22 spec cases plus 25 subtests; scoped JSON parsing and local links; whitespace checks and staged secret scan. The actual seven changed paths select zero image contexts (`[]`); runtime/Docker/dependencies/workflow inputs remain byte-identical to the tested 9a53b56. Remote docs-PR CI remains pending until observed. No cloud or image test was repeated solely for this record.
