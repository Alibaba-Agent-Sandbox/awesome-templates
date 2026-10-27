# Decision: exercise additional original template workflows on OpenSandbox

Status: proposed

## Problem
40 templates have complete Express usage receipts, while only13 currently have
complete OpenSandbox receipts. Best-effort OpenSandbox coverage requires actual
native/application/business use, not inferring portability from an image build.

## Decision
Run the remaining26 source templates serially on the official explicitly enabled server-proxy
OpenSandbox server. Use unchanged pinned source, full original native controller,
fresh literal README CLI/full SDK/direct HTTP, independent business outputs and
owned cleanup. Publish only individually complete reviewed provider receipts.
Keep all failures and partial runs; never infer qualification from a batch exit.

## API Design
No runtime, command, model credential or template declaration change is proposed.
Managed Express Base is provider-owned and cannot be relabelled OpenSandbox.
Native vendor/desktop accounts and interpreter capacity/owner defects stay separate.

## Alternatives considered
A health check, build, source-provider pass or compatible-only mode is insufficient.
Parallel images would waste the constrained local root disk; use exact owned image
cleanup and registry garbage collection after each completed resource lifecycle.

## Dependencies
Refs https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/244.
Frozen input46b7c1ccc01eae9cf41292dde89ab32411ed5f79 includes merged PR276/277.
Existing40-template Registry and practical articles remain independently delivered.
New Registry receipts require source evidence review and unchanged folder identity.

## Test Strategy
Published CLI0.5.7/client-server0.4.0a6, official OpenSandbox1.1.1 and pinned
execd1.1.1 with internal proxy enabled. Full native method inventories, zero native
omissions for passes, actual model/browser/language/service artifacts, independent
owned sandbox/template/local/remote image absence. Local docs/spec/secret/diff and
final-head CI gates remain required. All26 original results are available:11 complete candidates and15 failures, retained separately from follow-up runs.

## Acceptance criteria
Review each actual result separately, retain blockers/failures, qualify only complete
matching provider results through Registry. No full50-template completion claim.
