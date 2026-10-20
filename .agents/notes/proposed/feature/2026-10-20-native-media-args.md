# Decision: Add native media argv and exact server-source selection

Status: proposed

## Problem

[Issue58](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/58)
requires CPU FFmpeg with native string-array arguments and actual process results.
The existing1.0 presets cover useful conversions but cannot satisfy the array
contract. The server previously coerced list[str] to string; see the SDK
[foundation PR78](https://github.com/Alibaba-Agent-Sandbox/python-sdk/pull/78).
Globally changing the injected server would invalidate existing template evidence.

## Decision

Add `transcode_args` and `media_args_smoke` in1.1 while retaining the published
preset API. Validate one bounded offline input/output and an explicit safe native
option subset. Run the actual argv without shell parsing; return real bounded
stdout/stderr/exit_code and publish only successful independently probed artifacts.
Keep descriptor snapshots, local protocols, process/resource limits and exclusive
artifact publication. Version1.1 stays unqualified until fresh cloud evidence.

The optional `server-sdk.commit` selects one immutable public SDK source agreeing
with the standalone Docker fallback. Image CI checks out that commit before
building its injected wheel; source/archive/proof validation checks the same pin.
The opt-in file is hashed in image/step provenance. Steps refuse an older explicit
server override. Templates without the file retain their historical common
injection, even if their standalone fallback differs; earlier qualified runtime
receipts are not changed or reinterpreted.

## API Design

`transcode_args(args: list[str], max_seconds: int=5, command_timeout: int=60)`
accepts3–64nonempty strings/8192 UTF-8 bytes, beginning `-i <workspace-file>` and
ending a plain MP4/WAV/FLAC filename. Output options are explicitly documented.
Actual FFmpeg nonzero returns200with its exit/results and no partial artifact;
guard/probe/timeout failures retain server errors. `transcode` stays compatible.
The survey name is delivered additively to preserve that existing public contract.

## Alternatives considered

- JSON strings or Python representations: do not implement native arrays.
- Replace preset transcode: breaks existing clients and changes required errors.
- Arbitrary FFmpeg options: expands file/network/device behavior beyond the task.
- Change all SDK pins globally: changes previously qualified independent templates.

## Dependencies

Exact Debian FFmpeg7.1.5/ABI pins and retained GPL/native notices. No CUDA/model.
The immutable SDK foundation must merge before this consumer. The SDK client and
CLI already forward native JSON arrays; actual cloud transport remains required.

## Test Strategy

Native FFmpeg and authenticated HTTP cover spaced inputs, actual output bytes,
real libx264 failure stderr/exit and no partial files, rejected options/types,
no-clobber and full PCM equality/cleanup. A borrowed-sandbox controller separately
uses native CLI array conversion and SDK array decode, independently reads bytes
and checks every sample, then removes its unique files. Source/CI pin tests refuse
mutable/conflicting/mismatched source and stale step overrides. Existing source
transfer limits remain; large committed commands use verified immutable archives.

## Acceptance criteria

- Native/HTTP regression and source/docs/contract checks pass with no required skip.
- Current-head L1 and all CI gates pass with the exact server source selected.
- Actual SDK-created Express image and native step attempts retain exact provenance.
- Native CLI/SDK arrays, complete HTTP/media bytes and independent cleanup pass.
- Historical1.0evidence remains intact; only new1.1receipts qualify1.1.
- SDK foundation lands first, then this PR merges normally and Issue58closes.

## Evidence

[Verification](../../../evidence/verify/2026-10-20-native-media-args.md).
