# Gemini cross-review by the OpenClaw implementer

Date: 2026-10-16
Result: PARTIAL
Scope: read-only independent review of gemini commands/tests/docs/design.

## Verified review

Read `gemini/commands.py`, `e2e_test.py`, behavior/protocol regressions,
Dockerfile/template.yaml, both READMEs and `docs/design/gemini.md`.

- Missing-key guard prevents model/device/OAuth launch. argv is a list, no shell
  prompt interpolation; default plan mode is explicit and yolo requires opt-in.
- cwd traversal and symlink escaping are rejected; docs correctly distinguish
  starting-directory containment from a tool filesystem boundary.
- Setup inspects metadata without configuration writes/contents. Version can run
  without a model key. stdout and failure output redact secret-valued environment
  variables, including JSON-escaped strings; timeout omits prompt argv.
- Process-group deadline is implemented with bounded reap and regressions.
- Required-model and forced-off negative controls reject missing target keys,
  marker-only responses, modified tests and failed remote verification.
- CLI/SDK/POST docs preserve buffered JSON, explicit permissions, client/server
  timeout separation, missing-key limitations, no claimed cloud/model pass.

## Finding sent to implementer

P1: final unittest verification imported the standard-library module from the
model-writable cwd. A newly created `unittest.py` can print `Ran 3 tests` plus OK
and exit0 without executing original tests. Demonstrated in a fresh temporary
project: calculator deliberately returns0 for original input(2,3), otherwise a+b;
a local unittest.py prints the expected verifier output. The existing final
unittest gate passes, current held-out arithmetic passes, while direct original
(2,3)==5 fails. No credentials, model calls or repository edits were involved.

Recommended fix: `python -I` with a controller-owned fixed script, load source by
absolute path, and independently assert original plus held-out semantics without
importing writable cwd unittest. Add this module-shadow negative control.
Gemini implementer acknowledged and is applying the fix; final review belongs to
that follow-up evidence. No Gemini files were modified by this reviewer.

## Validation and limitations

`python -m pytest gemini/test_commands.py gemini/test_e2e_protocol.py -q` executed
against the scoped working tree. The actual result is supplied in the follow-up
below. Existing tests alone do not cover the module-shadow finding. No image,
provider or model acceptance was attempted by this reviewer.

Follow-up: targeted Gemini tests exited0:17passed,1skipped (real pinned CLI was
not on this review process PATH). That is a regression pass, not the shadowing
fix acceptance or model/cloud evidence.

## Finding resolved: independent follow-up

Read the corrected Gemini verifier and reran scoped tests: exit0,23passed,
1skipped (real pinned CLI not on this review PATH). Final unittest invocation
starts `python3 -I`, imports system unittest before inserting project search
path, and runs the preserved test file. The independent verifier also uses -I,
loads calculator.py explicitly by path, checks all original plus held-out
semantics and requires exact INDEPENDENT_OK. New actual-subprocess regressions
exercise unittest.py and sitecustomize.py shadowing against incorrect original
arithmetic, and reject both. The correct implementation still passes with either
shadow file. This closes the concrete P1 reproduction from this review; no
remaining blocking finding was identified in these scoped verifier changes.
This acceptance is a negative-control regression result, not real-model or cloud
acceptance.
