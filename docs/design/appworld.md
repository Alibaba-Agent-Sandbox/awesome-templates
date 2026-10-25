# appworld

## Purpose

Run original AppWorld0.1.3.post1 training tasks and evaluator on a disposable Express target for [Issue70](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/70). Pinned upstream supports direct Python; Docker is optional.

## Capabilities

Original engine/API/SQLite/evaluator plus explicitly authored compatible-model API bridge, training only. No paper-baseline reproduction, held-out benchmark/leaderboard score or other-provider acceptance. Protected image contents remain encrypted.

## Exposed API

[Command reference](../../appworld/README.md#command-reference) documents five commands and scalar bounds. Model-free native version/setup/smoke, appworld_run(task,max_steps,command_timeout) with strict native all-tests score and encrypted owned artifact, and independent keyless appworld_verify_artifact(path,task) reloading original saved databases/evaluator. Buffered results; successful result folders persist for caller cleanup, failed partial folders removed.

## How to build

[Dockerfile](../../appworld/Dockerfile): Alibaba generation2v0.0.49/Python3.13/Linuxx64, isolated full SHA256 Python lock and pip check. Original published wheel0.1.3.post1 corresponds to public tag66ad8099e12188ece0d3fe45e661dbc01880813b, not a reproducible-build claim. Original encrypted package bundles are SHA checked. Official encrypted data34280074bytes/SHA256fd9f9608c2ec71ed0ac25c3633a738b9129a318a129e31230425b9188e508250 is controller-measured, not upstream-published. No protected unpack during public image build. Runtime copies the package and invokes original install/unpack only in its private HOME. server package 0.4.0a3, non-root/9000,8GiB rootfs guard/noCMD/ENTRYPOINT. Exact S3 object transport remains hash-bound; arbitrary S3 paths are rejected.



Python3.13 compatibility: original SQLAlchemy1.4.54 has no matching wheel. Its unchanged SHA256-pinned source uses upstream DISABLE_SQLALCHEMY_CEXT=1 for pure Python; pinned setuptools80.9.0/wheel0.45.1 are installed from a separate hash lock before --no-build-isolation. All native/runtime requirements remain hash-pinned; SQLAlchemy2 is not substituted.

## Express feasibility

Feasible: slice. Limiting factor: original native dependencies/task/model/resource compatibility still require actual image and Express execution. Proposed2CPU/2048MB, noDocker/KVM/GPU. One original training task must pass actual original evaluator and keyless saved-database reevaluation; version/install/local tests alone are insufficient.

## Risks

[Protected distribution requirement](../../appworld/UPSTREAM-NOTICE.md): keep public app/task/data derivatives encrypted, including result bundles. No plaintext protected task/code/database logs in public records. Original bundle encryption is not a confidentiality guarantee. Minimal process environment, explicit approved HTTPS model base/key via anonymous stdin, no operator cloud/GitHub/model environment inheritance. Authored tool bridge validates exact original allowed API membership and JSON arguments as Python literals; original AppWorld safety defaults remain enabled. Request/output/time/context/tool limits, serialized owned group/nonce/pidfd descendants and private decrypted state cleanup on every terminal path. Native artifact verifier bounds encrypted/expanded sizes and members, rejects symlinks/path escapes/other experiments, binds source/data/task/version and requires exact native count/score agreement. Caller workspace artifacts persist intentionally.

## Test plan

Authored input/config/path/environment/anonymous-stdin/process/private-result cleanup and exact original data/cache transport controls; source-only HTTP keeps native/model omissions explicit. L1 actual image and original task/API smoke; L2 immutable-source canonical steps, official READY, SDK Sandbox.create, CLI/SDK native smoke/fullHTTP and independent sandbox/template/OSS absence. L3 real compatible model completes original training task through native APIs, all original evaluator tests pass, independently downloaded encrypted bytes/SHA match, separate keyless original evaluator reloads saved database and reproduces exact counts/score, fresh post-return ACK and own result/private/process/secondary-listener cleanup. No native benchmark/model-generated code executes on operator. Every failure/skip remains historical evidence.
