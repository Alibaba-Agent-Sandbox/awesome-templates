# media-tools

## Purpose

Deliver the CPU conversion slice requested by [Issue 58](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/58): inspect uploaded media and produce independently verifiable MP4/WAV/FLAC files without cloud accounts, GPU, display or model configuration.

## Capabilities

Buffered named commands, workspace file artifacts, offline audio/video inspection and bounded CPU conversion. MP4 contains H.264 640-wide/24fps video with optional AAC audio; WAV/FLAC contain mono 16 kHz audio. Version1.1 also accepts native argv within a documented offline option allowlist; network streams, playlists, devices, arbitrary filters and live progress remain excluded. The shared server still supplies shell/files/code/ports.

## Exposed API

See [the command reference](../../media-tools/README.md#command-reference) for required/default parameters and response fields. `media_version()` verifies exact `ffmpeg -version` and `ffprobe -version`; `media_setup_check()` reports availability. `media_probe(input_path: str, command_timeout: int=30)` performs bounded offline `ffprobe -protocol_whitelist file -format_whitelist ... -show_entries ... -of json -i <snapshot>`. `transcode(input_path: str, output_name: str, preset: str="mp4", max_seconds: int=5, command_timeout: int=60)` runs a fixed argv `ffmpeg -nostdin -v error ... -i <snapshot> -t <seconds> ... <private-output>`, independently probes output, hashes complete bytes and publishes with no-clobber `link`. `media_smoke()` creates PCM, uses the FLAC command, independently decodes via FFmpeg and compares every sample before cleanup.

## How to build

[Dockerfile](../../media-tools/Dockerfile) keeps the Alibaba base, generation 2 serve/healthcheck and non-root user. Install Debian FFmpeg and its ABI libraries at exact `7:7.1.5-0+deb13u1`; retain installed distribution license notices. The Dockerfile installs published `agent-sandbox-server==0.4.0a4` directly. No private artifact, model key or GPU package is required. Debian repository resolution is retained for unrelated system libraries. Package/version existence was verified from the official Debian package page and actual installed tools; no image build is inferred.

## Express feasibility

Feasible: yes

Limiting factor: none for the bounded CPU slice; image/provider acceptance still must execute.

The template uses 2 vCPU, 2048 MB RAM, non-root ownership and writable workspace, with no nested containers/KVM or extra capabilities. FFmpeg processes have 1 GiB address-space, 120/121-second CPU, 64 MiB file and caller-bounded wall deadlines. Codec/filter threads are bounded. Inputs and outputs are at most 64 MiB; individual conversions produce at most 30 seconds.

## Risks

Malformed native media is processed inside the sandbox with resource limits, local-only protocols/demuxers and snapshot files. Descriptor walks reject symlink components and traversal; exclusive output publication never overwrites existing files. Preset calls return normalized metadata. The new argv entry additionally returns actual bounded native stdout/stderr/exit_code; inherited model/cloud credentials are excluded. A single-operation lock prevents concurrent conversion memory amplification. General shell/files permissions, deliberate session escapes, server SIGKILL and accumulated retained artifacts remain outside the named operation's guarantees. Dependency licenses are preserved separately from template Apache-2.0 code. The survey argv interface is delivered additively as `transcode_args(args: list[str], max_seconds=5, command_timeout=60)` to preserve the existing preset contract. Its allowlist and forced final resource limits retain the offline file boundary. Native nonzero exits never publish partial files. The Dockerfile pins the published server package; image checks verify its installed version.

## Test plan

L0: checker, actual codec/process regressions and HTTP E2E. Real tests generate MPEG4/PCM input, produce H.264/WAV/FLAC, independently probe codecs/dimensions/channels/sample rates/duration and verify complete output hashes. The HTTP controller uploads fresh random PCM, downloads FLAC and WAV artifacts, validates hashes and independently parses every roundtrip sample. Negative cases cover invalid paths/URIs/FIFO/symlinks, corrupt/playlist inputs, invalid limits, existing artifacts, diagnostics overflow, missing/failed native programs and redirected descendant cleanup on success/failure/timeout. `E2E_REQUIRE_MEDIA=1` forbids a missing-engine skip.

L1: actual Docker build must display FFmpeg `7.1.5-0+deb13u1`, verify non-root user and run `template.yaml`'s `media_version` and byte-verified `media_smoke` commands. L2: canonical `python scripts/public_launch_e2e.py media-tools --provider alicloud-express --application-controller` must deploy through the actual CLI, call both smoke commands from outside via CLI and SDK and confirm cleanup before provider receipt/promotion. L3: N/A, no model dependency or agent claim. L4: no additional provider tested or claimed.
