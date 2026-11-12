# Verification: additional access ports

Date: 2026-11-12. Parent producer: `e9250512967d4c4abb59672567d68ba3e7d18473`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: actual AJV8.18.0/Python jsonschema4.26.0 consume20 positive and44 negative
  resource vectors plus5 negative Registry vectors; complete outputs deep-equal.
- PASS: eleven Python tests, including raw-port-only compilation without invented services,
  and sorted deduplicated union with declared service ports.
- PASS: bool/zero/out-of-range/duplicate raw port rejection in both languages.
- Migration of original ports is verified separately. This commit excludes active migrations.
- No cloud, model, native listener startup or public Gateway routing validation performed.

Commands: `PYTHON=<Python3.13-venv> node contracts/template-v1/test.mjs`,
`<Python3.13-venv> contracts/template-v1/test_contract.py` and scoped Ruff check.
