# Verification: ordinary public resource names

Date: 2026-11-12. Producer parent: `6dfaf3990b43364ea8ec1e2f5a46dc4db2cc0811`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: actual AJV8.18.0/Python jsonschema4.26.0 consume21 positive and59 negative
  resource vectors plus9 negative Registry vectors; complete outputs deep-equal.
- PASS:12 Python tests, retaining63/64-character boundary and long native reference checks.
- The new _skeleton vector rejects a repository engineering name as a public resource name.
- No active template/checker migration, native-ID limit, cloud operation or release included.

Commands: `PYTHON=<Python3.13-venv> node contracts/template-v1/test.mjs` and
`<Python3.13-venv> contracts/template-v1/test_contract.py`.
