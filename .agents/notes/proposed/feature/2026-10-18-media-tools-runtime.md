# Decision: Add a bounded offline CPU media template

Status: proposed

## Problem

[Issue 58](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/58) has a survey entry but no executable media template. The overall task remains incomplete while credential-free CPU tools have no implementation. FFmpeg supports arbitrary files, network URLs and flags, so a general argv wrapper would add an unnecessarily broad named-command interface.

## Decision

Implement `media-tools` with exact Debian FFmpeg/ABI version pins, standard server startup/non-root ownership, typed fixed MP4/WAV/FLAC presets, local-only protocol/demuxer lists, descriptor-based regular-file snapshots, resource/process/output limits and no-clobber artifact publication. Retain normal shared server capabilities. Add bilingual instructions, design/catalog entries, actual codec/process regressions and a dedicated Debian CI job; general host HTTP smoke explicitly marks unavailable pinned tools as SKIP. Required acceptance opts in to `E2E_REQUIRE_MEDIA=1` and cannot silently skip the engine.

## API Design

`media_version`, `media_setup_check`, `media_probe`, `transcode` and `media_smoke` are buffered server commands. See [the design](../../../../docs/design/media-tools.md) for exact typed parameters and bounds. The existing public server/client API is unchanged. The survey's freeform `args` proposal is narrowed to fixed presets; this is a new template with no prior consumers.

## Alternatives considered

Defer all implementation until cloud access: rejected because meaningful CPU execution and artifact acceptance need no external account. Expose arbitrary FFmpeg argv: rejected because it would permit network/device/file output paths beyond this task. Pretend successful native host execution proves image/cloud acceptance: rejected; each tier stays separate. Install a floating binary or GPU runtime: rejected in favor of verified Debian package pins and CPU codecs.

## Dependencies

This scoped branch is stacked on [OCR PR 103](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/103), immutable base `a4a18b0dbb18a18ccf5e2d5c113454bff9319bc4`; its pre-existing changes remain owned by that PR. Debian's official FFmpeg package metadata and actual installed `7.1.5-0+deb13u1` tools were inspected. Image installs use Debian repositories and preserve dependency licenses. The Dockerfile fallback server source is `e2cb27e24fde0a67112f82b8d44af463445a5d1a`. No cloud/model key is required or forwarded.

## Test Strategy

Execute actual pinned CPU codecs and independently run ffprobe on MP4/WAV/FLAC artifacts; compare output hashes and audio properties. Run native success/failure/timeout with redirected descendants, diagnostic overflow and sensitive-environment exclusion. HTTP acceptance generates fresh random PCM in the external controller, uploads through files API, converts through named commands, downloads complete artifacts, checks every WAV roundtrip sample, then removes controller-owned files. Run static checker, spec-tools suite, link and staged-secret checks. L1 image and canonical L2 remain separate required delivery evidence.

## Acceptance criteria

- Source/runtime and document/checker validations pass, including required-engine HTTP execution with zero skips.
- Independent review finds no unresolved runtime correctness issue.
- Actual Docker image build and non-root image smoke pass; no host result substitutes for them.
- Canonical deploy/CLI/SDK smoke and strict owned cleanup pass before provider evidence/status promotion.
- CI/review and permitted merge are confirmed against the current remote head; keep draft/incomplete status while gates remain.

## Evidence

[Verification record](../../../evidence/verify/2026-10-18-media-tools-runtime.md).
