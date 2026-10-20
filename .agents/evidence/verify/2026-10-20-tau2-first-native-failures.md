# Tau2 first native attempts and Python3.13 compatibility

Status: FAIL for native acceptance; PASS for independent owned cleanup.

Exact tested template source:736af4229f0b88bcddc1d75c91c19387564a2173.
Original framework source remainsfc0055dc4e0a316c3f83133267fbd6faaa770992.

- Final pre-cloud local gates:57spec tests PASS in13.137s; strict all-template
  check0violations;54runtime/asset regressions PASS in31.71s;174public documents
  plus3explicit engineering records have0local link failures.
- Actual L1 workflow39495638816 and PR L1 workflow39495639993 FAILED the native
  `tau2_version` smoke after successful image/dependency installation and actual
  non-root workspace/server checks. A built image is insufficient qualification.
- [First canonical SDK-created steps attempt](../../../tau2-bench/evidence/verification-steps-2026-10-20T205252Z.json)
  FAILED native CLI and SDK version; real model was NOT RUN. Owned sandbox and
  template absence independently confirmed. Private OSS ACL/integrity and owned
  bucket/object cleanup independently confirmed. Duration133.543s.
- [Same-source keyless diagnostic attempt](../../../tau2-bench/evidence/verification-steps-2026-10-20T205617Z.json)
  FAILED the same smoke; model NOT RUN; owned sandbox/template and private asset
  cache cleanup independently confirmed. The unmodified source/runtime remained
  frozen during the run. A separate keyless SDK shell import reported
  `ModuleNotFoundError`, missing module `audioop`, through upstream audio
  preprocessing imported by its text evaluator dependency path. No model key was
  forwarded or native model request made in either failed attempt.

Python3.13 removed the standard-library module. Compatibility fix explicitly
adds [audioop-lts0.2.2](https://pypi.org/project/audioop-lts/0.2.2/), PSF-2.0,
with official Linux CPython3.13 wheel SHA256 enforced by pip. The verified wheel
license is retained. This is a disclosed additional compatibility dependency;
it does not change upstream source or any original frozen dependency pin.
Template version advances to1.0.1. Keyless version errors may expose only a
validated missing-module identifier; model-operation diagnostics remain private.

New actual image, canonical Express steps, real agent/user task and independent
keyless native replay remain required. Neither failed attempt is relabeled PASS.
