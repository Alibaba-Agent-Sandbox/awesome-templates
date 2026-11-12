# Verification: strict identifier end boundaries

Date: 2026-11-12. Parent producer: `5cf448296361b3bcd8341bd8ae8131f2ca703496`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- Reproduced before fix: Python jsonschema4.26.0 accepted root name `example\n`.
  Actual Node22.22.2/AJV8.18.0 and native JS regex rejected it. CRLF was already rejected.
- PASS:21 positive and58 negative resource vectors,9 negative Registry vectors, actual schema
  validators and complete Python/JS normalized/compiled meanings deep-equal.
- PASS:12 Python tests, including valid63-character local name, invalid64-character and
  LF/CRLF resource names, and an unchanged native reference longer than128 characters.
- PASS: scoped Python lint. Only semantic ASCII ID patterns change; JSON Pointers,
  expressions, paths and Provider-defined template reference fields are untouched.
- No cloud, model, image, package release or consumer copy mutation performed.

Commands: `PYTHON=<Python3.13-venv> node contracts/template-v1/test.mjs`,
`<Python3.13-venv> contracts/template-v1/test_contract.py` and scoped Ruff check.
