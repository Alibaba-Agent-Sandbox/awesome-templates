# Bounded CPU media template verification

Date: 2026-10-18
Result: PARTIAL

## Source and environment

New `media-tools/`, its design/catalog/README integration, dedicated Debian CI job and owner records, stacked on exact OCR base `a4a18b0dbb18a18ccf5e2d5c113454bff9319bc4`. Existing parent-branch work is unchanged. Linux x86_64 Debian 13, Python 3.13, actual system FFmpeg/ffprobe `7.1.5-0+deb13u1`. Isolated virtual environment installs locally built agent-sandbox-server 0.3.0 from python-sdk `fbe506349693f9bb26c1755aa3d13ce855e1ab69`, httpx 0.28.1, pytest 9.1.1 and pyyaml 6.0.3. The tested host server source is identified separately from the Dockerfile fallback pin. No Docker executable or engine is available locally.

## Executed checks

Initial actual native regression run: 37 passed, zero skips, exit 0. This covered three actual codecs, independently executed ffprobe output assertions, exact hashes, path/protocol/FIFO/symlink/invalid-content limits, no-clobber artifacts, oversized input, invalid preset/deadlines, concurrency refusal, real nonzero/diagnostic overflow, redirected descendants after success/failure/timeout, and credential exclusion. The final follow-up run adds actual smoke, missing required-stream negatives and decoder-failure cleanup: `python -m pytest -q media-tools/test_commands.py` completed with 40 passed, zero skips, exit 0 (7.19 seconds).

- PASS: actual credential-sanitized `scripts/run_local_e2e.py::_run_one` for media-tools with `E2E_REQUIRE_MEDIA=1`: 20 HTTP checks passed, zero failures/skips, driver exit 0. It exercised registered typed commands, HTTP400 argument handling, HTTP500 traversal/network rejection, exact installed versions, native smoke, external random PCM upload, FLAC/WAV conversion, independent downloads/full hashes/FLAC magic, every WAV roundtrip sample, preserved original upload, and three successful owned artifact deletions. The server was terminated/reaped by the runner and no `.media-*` or controller artifact remained.
- PASS: `python scripts/test_spec_tools.py`: 22 tests, exit 0. Its Express protocol fixtures are synthetic tests, not actual provider acceptance.
- PASS: `python scripts/check_template.py --all --strict`: 20 conformant directories including skeleton, zero violations, exit 0.
- PASS: all scoped relative Markdown links, Python AST syntax, workflow YAML/container contract and `git diff --check`, exit 0.
- PASS: official Debian package page lists the pinned package, and local `apt-cache policy ffmpeg` reports the exact installed/candidate version. These establish package/source availability, not image success.
- NOT RUN: full all-template local E2E; this isolated environment lacks the existing unrelated pinned agent/browser runtimes. Target-template L0 executed its actual runner path without dependency skips.

## Independent review

The coordinating reviewer independently read the complete commands and regression source and found no blocking issue in fixed argv, snapshots/dirfd path handling, no-clobber publication, deadline/owned-group anchoring or actual codec assertions. It requested missing audio/video-stream negative controls and smoke-failure cleanup coverage; both were added for actual execution.

## Remaining gates and cleanup

First remote source CI at `0c19fb5ce81f0ecd4319e5344848af673aa1187e` failed the actual Debian native job: 39/41 tests passed, while MP4 encoding failed in two cases. WAV/FLAC and the typed SDK case passed. This remote failure is retained; the next revision adds a native MP4 reproducer using the same resource caps and only generated fixtures so safe native diagnostics can identify the platform difference. No limit is weakened and no failed case is skipped.

Actual Docker L1 and non-root container verification are PENDING. A successful host package/version check does not establish installation compatibility with the Alibaba base. Canonical `scripts/express_e2e.py` through actual `abx template deploy`, CLI/SDK smoke and strict official cleanup is NOT RUN. No provider receipt, `tested_on` value or official status is added. L3 is not applicable because this template does not call a model. L4 is NOT RUN.

The final combined `python -m pytest -q media-tools/test_commands.py media-tools/test_http.py` completed with 41 passed, zero skips, exit 0 (7.60 seconds). The additional test installs the actual source-built agent-sandbox-client 0.3.0 from python-sdk `fbe506349693f9bb26c1755aa3d13ce855e1ab69`, starts a real token-configured server, uses its actual typed `ServerClient` command/files APIs, checks unauthorized `/commands`, typed argument/execution errors, exact artifact hashes and every random PCM roundtrip sample, and independently confirms all three deleted SDK paths no longer exist. This is local SDK-over-HTTP acceptance; no cloud `Sandbox.create` occurred.

An initial SDK-test assumption that `/health` required authentication failed because this server intentionally keeps health public. The test was corrected to assert unauthorized `/commands`; the failure is not represented as a passing authentication check. An injected post-publication decoder failure verifies source and output cleanup; nested finally blocks ensure output cleanup and descriptor close even if source unlink raises.

All native test roots are temporary; the process regression kills only its owned children. HTTP controller cleanup removes only its unique uploads/outputs. No cloud resource, registry repository, remote model turn or credential upload is created by these checks. Template artifacts intentionally retained by ordinary commands belong to callers.
