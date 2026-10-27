# Crush native compatible-agent experience

Result: PARTIAL (Crush complete; remaining catalog pending)

Date: 2026-10-27. Actual standalone CLI0.5.7, Python client/server0.4.0a6,
Docker29.9.2 overlay2/MTU1450. Source Crush folder identical across
a63f0f8f8996fd772116c570aa21e927dcc1aea0 and
1627b69177263c47886ec8d9ebdb34951c2d3388. Build serialization uses a task-local
flock wrapper around native Docker builds; recipes and images are not rewritten.

- [Native core](2026-10-27-compatible-agent-usage/crush-core-express.json): PASS,
  17 assertions, zero failure/skip/not-run. Exact version/setup/Crush methods,
  wrong-token rejection, original failing calculator repaired, original three
  tests unchanged, report/exact artifact retrieved, independent original and
  held-out assertions passed. Controller/transport hashes captured before run;
  inputs unchanged. Model qwen3.8-flash actually ran, no synthetic account fixture.
- [First documentation attempt](2026-10-27-compatible-agent-usage/crush-docs-failed-order.json):
  FAIL retained. Operator helper ran README export-stage execution before creating
  the file. This was a checker ordering error, not evidence of a product defect.
- [Fresh documented tasks](2026-10-27-compatible-agent-usage/crush-docs-express.json):
  PASS,12 checks: actual CLI, complete unchanged SDK program, direct HTTP, generated
  Python independently executed, and all three GENERATED_REPORT.md files downloaded
  and nonempty. Primary/report outputs were removed and independently absent before
  the next consumer. Actual second startup model qwen3.8-max completed all three.
- The documentation receipt originally references an earlier passing core's SHA;
  the newly guarded core above has exactly the same manifest, staged source and
  provider digests and the same HTTP-controller SHA. This record reviews the new
  guarded core, not an assumed earlier adapter identity. Both runs used the same
  unmodified Crush runtime/manifest/README/controller bytes.
- All completed cloud cases independently confirmed own sandbox and prepared
  image/template absence, zero retained/uncertain cleanup. Local isolated program
  execution is an additional verifier, not provider qualification by itself.
- All declared template methods: crush_version, crush_setup_check, crush; health
  and commands discovery were exercised. This does not certify every optional
  upstream product integration or every model offered by a vendor.
- Shared guide correction matches actual model switching via new configured
  instances; it does not claim a second endpoint was exercised.

Local checks: check_docs.py PASS,224 documents/zero failures; diff and
configured-secret scan PASS. Current-head CI pending. Practical article and
Registry receipt are separate owner deliveries. Interpreter Issue251 remains
unresolved and its successful normal case does not qualify the interpreter.
