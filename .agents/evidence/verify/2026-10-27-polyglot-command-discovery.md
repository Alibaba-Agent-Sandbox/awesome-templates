# Polyglot command-discovery acceptance

Result: PARTIAL (new assertion; actual provider reruns pending)

Date:2026-10-27. Original source46b7c1ccc01eae9cf41292dde89ab32411ed5f79 runs actual
compiler versions and Go/Rust/Java programs with owned cleanup, but contains no
GET /commands request. Those native business outcomes remain valid; complete
public-method qualification additionally needs the actual discovery call.

The revised external controller requires HTTP200 and exactly toolchain_versions /
toolchain_smoke before proceeding with unchanged installed-pin and native output
assertions. No image/runtime/dependency/readme-program change. Source folder identity
changes and requires fresh source-bound provider receipts.

Fixture negative/positive controls, local process/spec/docs, actual Express and
OpenSandbox full method/literal CLI/full README SDK/direct HTTP, exact owned cleanup,
current-head CI, Registry/public readback remain pending. No full50 claim.

Protocol controls PASS4: old controller accepts missing discovery without requesting
it; revised controller rejects missing404 and incomplete inventory, accepts complete
inventory. Synthetic compiler outputs here prove controller protocol behavior only;
fixture listener independently stopped. Existing process tests PASS6; spec PASS39;
all-template checker PASS; documentation links PASS224; secret scan6 files/diff PASS.

Targeted local L0 starts the actual SDK server and PASSes real discovery. Native
compiler stage is explicitly SKIP because host pins are absent; this is not image
acceptance. Initial L0 operator invocation used the system python3 child instead
of the installed SDK venv and failed startup; adding the venv to child PATH fixes
that environment mistake. Both runs stop their owned server; no cloud calls here.
