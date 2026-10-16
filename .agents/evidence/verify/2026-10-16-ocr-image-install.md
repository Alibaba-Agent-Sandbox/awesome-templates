# OCR actual image install failure and repair — 2026-10-16

Result: PARTIAL — the first actual L1 failed; the repaired install was verified natively, and its actual image CI remains pending.

Scope: OCR Dockerfile dependency installation, bilingual stack text/design and the existing proposed decision. Recognition commands and source HTTP controller remain byte-identical to reviewed commit `75fa2298c05d3b98086ff0dbb46ffe321a8901e6`.

## Preserved actual failure

[L1 run 38870375361](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/38870375361), image job 116872852327, actually installed the five exact critical Debian engine/library/language packages. It then failed at Pillow installation: the additional command-line `Pillow==11.3.0` requirement had no own hash in pip's strict hash mode, even though the committed requirements entry had hashes. No image smoke/archive/cloud acceptance occurred. Log artifact 12033222283 preserves the first failure. The additional requirement had been introduced to satisfy the checker's literal pin rule; passing that checker did not prove pip installability.

## Repair and observed validation

Download only binary Pillow wheels against the unchanged committed hash list, then install the already verified wheel with `--no-index --no-deps`, and remove the temporary wheel directory. This preserves strict hashes and fixed dependencies without adding an unhashed duplicate or changing shared checker rules.

Actual native Python 3.13 / pip 26.0.1 executed the same hashlocked download, offline no-deps installation into a disposable target, then an isolated interpreter imported actual Pillow 11.3.0 and created an image. The selected cp313 manylinux x86_64 wheel SHA256 was `13f87d581e71d9189ab21fe0efb5a23e9f28552d5be6979e84001d3b8505abe8`, present in the committed list. All temporary download/install files were removed. An initial local harness invocation used a venv without pip and failed before download; rerunning with the native Python/pip exercised the install. No shared installation was replaced.

The earlier 27 real-engine source tests / 19 source HTTP checks remain source-only evidence; root independently repeated the exact real-engine pytest invocation with 27 passed, no skips. Runtime Python code was not changed for this Docker repair. The strict all-template checker passes the repaired wheel installation; actual rebuild/smoke is still required before any cloud run. Canonical deploy L2 stays unrun and tested_on stays empty.
