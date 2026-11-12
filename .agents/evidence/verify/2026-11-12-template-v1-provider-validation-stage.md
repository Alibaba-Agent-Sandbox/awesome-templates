# Verification: Provider validation stage

Date: 2026-11-12. Parent producer: `b9d11204d35525be898e75db277eaedb7f62197c`.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

- PASS: actual AJV8.18.0/Python jsonschema4.26.0 consume18 positive,40 negative resource,
  and5 negative Registry vectors, with complete cross-language outputs equal.
- PASS: ten Python tests. The new rejecting-callback probe records no intent invocation,
  retains the native numeric expression, and rejects real resolved input through the callback.
- PASS: existing unknown-plugin missing-descriptor gate, synchronous callback requirement,
  successful typed descriptor fixture and sensitive-error checks remain active.
- No cloud, model, image or expression evaluation. Bulk active migration excluded from commit.

Commands: `PYTHON=<Python3.13-venv> node contracts/template-v1/test.mjs`,
`<Python3.13-venv> contracts/template-v1/test_contract.py` and scoped Ruff check.
