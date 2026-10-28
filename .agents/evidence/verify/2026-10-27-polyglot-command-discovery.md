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

Broader coverage review: SWE/apply-patch/IDE/database/Next native scripts also omit
explicit discovery. SWE version and report, plus Next self-test, are positively
exercised by existing smoke/README layers, so they are not missing named business
methods. The common source-launch runner now executes the actual literal CLI
command-list step and validates nonempty unique registered names. This covers
future templates even when a native controller groups its own checks differently.
Fresh full workflows for both providers of four native utility/service families
and Express SWE are queued; pending OpenSandbox SWE already has the actual CLI
callback. These are full native/business/README reruns, not metadata-only promotion.

The same review found original OpenSandbox Qwen/DeepSeek controllers list the
legacy Python run method but do not execute it; earlier Express supplements remain
separate positive evidence. The common launch runner now executes that entry for
Qwen/DeepSeek/Hermes through CLI/SDK/HTTP, changing trusted nonce program bytes
between consumers and independently removing the owned script even on failure.
No template runtime or dependency changes. The actual listed names exclude hidden
registrations; they cannot replace the full source-owned public-method inventory.
Fresh full OpenSandbox Qwen/DeepSeek workflows are added; upcoming current-source
Hermes workflows also execute the explicit compatibility callback. Native/private
model outputs and original deadlines remain unchanged.

## Published CLI discovery source audit

Published CLIv0.5.7 source inspection confirms named execution sends only
POST /commands/name and does not implicitly list GET /commands. The separately
recorded source hash and exact tag explain why explicit discovery verification
is necessary; previous business POST success alone does not certify discovery.
No extra provider case was added for this source-only audit.

[Immutable tag/source hash](2026-10-27-polyglot-command-discovery/published-cli-source-audit.json).

## Fresh complete public-method workflows

Actual published CLI0.5.7/client-server0.4.0a6, source-bound full original native
controllers and fresh literal CLI/full unchanged README SDK/direct HTTP business
use. Common actual CLI discovery precedes the workflows. Qwen/DeepSeek also run
the legacy Python method through all three consumers using new script bytes per
call, followed by independent file absence. The full source inventory is separate
from listed command names; hidden methods cannot be inferred from discovery.

| Template | Provider | Result | Native passes | Documented checks |
| --- | --- | --- | ---: | ---: |
| polyglot-toolchain | alicloud-express | PASS | 2 | 8 |
| polyglot-toolchain | opensandbox | PASS | 2 | 8 |
| apply-patch | alicloud-express | PASS | 5 | 12 |
| apply-patch | opensandbox | PASS | 5 | 12 |
| code-server | alicloud-express | PASS | 5 | 11 |
| code-server | opensandbox | PASS | 5 | 11 |
| dev-services | alicloud-express | PASS | 6 | 8 |
| dev-services | opensandbox | PASS | 6 | 8 |
| next-app | alicloud-express | PASS | 6 | 11 |
| next-app | opensandbox | PASS | 6 | 11 |
| swe | alicloud-express | PASS | 14 | 8 |
| qwen-code | opensandbox | PASS | 17 | 15 |
| deepseek-harness | opensandbox | PASS | 17 | 12 |

Completed receipts: 13/13; complete passing workflows: 13.
Successful entries require zero native failures/skips/not-run and exact source/
README/verifier matching plus independent owned sandbox/prepared/local/remote image
absence. Failing entries never qualify. Current-head checks, producer/Registry/blog
publication and public readback remain independent gates. No full50 claim.
