# goose

## Purpose

Run the real official Goose terminal agent on caller-owned projects with an
explicit compatible-model configuration and controlled tool enablement.

## Capabilities

CPU/non-root terminal agent; named version/setup/goose API, files and shell
through the shared server. This profile uses OpenAI-compatible providers and
the developer builtin, not the desktop UI or every upstream provider.

## Exposed API

`goose_version() -> str`, `goose_setup_check() -> dict` (read-only flags),
`goose(prompt:str,cwd:str="",allow_tools:bool=false,command_timeout:int=600)->dict`
with stdout/stderr/exit_code. Prompt256KiB/no NUL, cwd inside WORKSPACE,
command_timeout1..1800. Actual argv is official `run --instructions - --no-session
--no-profile --max-turns 20 --quiet --output-format text --provider openai --model ID`,
plus `--with-builtin developer` only for explicitly allowed tools. Input is private
file stdin. API errors and limits are specified in both READMEs.

## How to build

[Dockerfile](../../goose/Dockerfile): required FC base, exact official1.54.0 CPU
GNU archive URL/length/SHA256 for x64/arm64 and sourcecd643d2126fffab4c6a6186905211ba868d6a657.
Do not use floating install scripts or Vulkan/CUDA archives. Verify actual
version before install completion; preserve upstream license. Published server package pinned in the Dockerfile; generation2 serve/healthcheck9000, explicit app chown
before USER user, no CMD/ENTRYPOINT. Separate Docker-only8GiB du budget.

## Express feasibility

Feasible: yes

Limiting factor: model endpoint reachability and configured credentials.

No GPU/KVM/Docker/display required. Two CPU/2GB profile and ~81MB compressed
asset; source generation does not establish a working cloud build. Local x64
native/protocol proof is not arm64 or provider evidence. Actual model/Express
qualification for1.0.0 now has [actual SDK-created image and model17 proof](../../goose/evidence/model-image-2026-10-20T073500Z.json): source edit/artifact/original tests/held-out checks and independently verified owned cleanup passed. The failed native step build remains separate; no successful step receipt is claimed.

## Risks

Tool mode executes shell/file actions as the sandbox user; cwd validation is not
a second filesystem security boundary. Default chat has no tools. Caller
configuration/history/hints/extensions are excluded with private HOME/XDG/path
root and no profile/session. Only model/CA/PATH necessities enter the child;
no cloud/GitHub/server keys. Both pipes256KiB, time limits and unreaped group
cleanup. Detached setsid and SIGKILL require final sandbox deletion. Project
artifacts remain caller-owned and stdout can contain their contents.

## Test plan

L0: exact real version, unchanged caller home, actual native HTTP fixture and
literal stdin, zero tools by default and exact developer tools when opted in,
missing config/path/type/endpoint negatives, redirected descendants, timeout
and noisy output bound. Synthetic HTTP is explicitly not real-model evidence.
L1: official package SHA/version, image user/SDK and writable workspace.
L2: true Express steps or verified image registration, native CLI/SDK plus full
remote API and independent sandbox/template/registry cleanup as applicable.
L3: required real compatible model edits calculator source, creates a report,
preserves/runs all original tests and passes fresh independent held-out values.
L4 only for an independently executed additional provider.
