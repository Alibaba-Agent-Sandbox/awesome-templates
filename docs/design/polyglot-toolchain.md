# polyglot-toolchain

## Purpose

Provide actual pinned Go, Rust and Java compilers for agent coding work without per-turn installation.

## Capabilities

Non-root shell/files/code/ports. All three compilers, Cargo, standard libraries and system linker. No model service or multi-version manager. Sources, compiled proof and Go cache created by smoke are removed together.

## Exposed API

`toolchain_versions() -> dict`: no parameters, actual Go/rustc/Cargo/Java/javac version lines and disk/non-root facts; absent tools return null. `toolchain_smoke() -> dict`: no parameters, actual go build, rustc and javac followed by executable output comparison GO_OK/RUST_OK/JAVA_OK and cleanup_verified. Trusted processes have90-second deadline and group cleanup.

## How to build

[Dockerfile](../../polyglot-toolchain/Dockerfile) installs official Go1.25.14, Rust1.90.0 components and Temurin21.0.12.1+1, with immutable [asset hashes](../../polyglot-toolchain/toolchains.json), retains licenses and enforces actual rootfs budget8GiB. Base v0.0.49, published server package. generation2 start_cmd `agent-sandbox-server serve --port 9000 --commands /home/user/app/commands.py`, ready_cmd `agent-sandbox-server healthcheck --port 9000`. 2vCPU/2048MB; non-root final USER.

## Express feasibility

Feasible: slice.

Limiting factor: actual 10 GiB rootfs; require no more than8GiB used after install. Issue62's reviewed workload covers Go+Java first; this implementation attempts all three with a fail-closed used-rootfs budget. No KVM, Docker or privileged capabilities required. Actual space and compile feasibility need real Express acceptance; no pass inferred from archive sizes.

## Risks

Official downloads require egress and bounded retries; hashes prevent changing assets. The installer refuses unsupported architectures, unexpected layouts and over-budget filesystem. Compiler projects may download their own dependencies, outside these fixed no-input smoke commands. Retain Go, Rust and OpenJDK legal notices and Classpath exception.

## Test plan

L0 actual HTTP health/command-discovery/versions; discovery must list both registered methods, with explicit skip if local exact compilers are absent. L1 actual non-root image executes toolchain_smoke, checks installed version pins and real compilation. L2 canonical Express steps/deploy READY, CLI and SDK toolchain_smoke, independent owned cleanup. L3 not applicable (no model); L4 unrun. No provider badge until a passing canonical receipt exists.

Review follow-up:1.0.1 gives the non-root runtime explicit ownership of its
workspace, filters child environment to compiler necessities, drains both pipes
concurrently and rejects output beyond256KiB per stream while retaining the
90-second deadline and unreaped group identity. Actual noisy-child and inherited
credential regressions are required. Old1.0.0 image/export records are historical.
