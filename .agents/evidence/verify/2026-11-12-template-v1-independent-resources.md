# Verification: independent v1 resources and Worker bootstrap ownership

Date: 2026-11-12. Base: `ed3e955daf8413e2c92736a4c7976bfd6200412a`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: actual AJV8.18.0 plus Python jsonschema4.26.0 consume17 positive,
  40 negative resource and5 negative publication vectors; complete JS/Python outputs agree.
- PASS: nine Python contract tests, including preservation of both independent resource
  blocks and absence of an invented business coordinator.
- PASS: both Worker private bootstrap properties reject authored native role values;
  existing Managed role/topology/credential/TTL rejection vectors stay active.
- No expression evaluation, cloud calls, image builds, model execution or releases performed.
- Consumer pre-effect rejection is owned and verified separately by the CLI repository.

Commands: `PYTHON=<intended-venv-python> node contracts/template-v1/test.mjs` and
`<intended-venv-python> contracts/template-v1/test_contract.py`.
The uncommitted bulk template migration is deliberately excluded from this producer commit.
