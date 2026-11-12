# Verification: shared v1 Core source reader

Date: 2026-11-12. Producer parent: fad843f60881b405cb386537337817e5144892bc.
Tracker: https://github.com/Alibaba-Agent-Sandbox/awesome-templates/issues/309.

## Actual behavior

- PASS:13 positive and25 negative raw YAML cases through actual Node yaml2.9.1 and Python
  PyYAML6.0.3+yamlcore0.1.1. Complete parsed values agree, including string/UTF-8 byte inputs.
- PASS:21 positive/59 negative resource and9 negative Registry schema/default/compile vectors;
  all complete Python/JavaScript results remain equal.
- PASS:14 Python tests, including inclusive1MiB boundary, no SafeLoader resolver mutation,
  invalid input type and source-free rendered traceback. Source native expressions stay text.
- PASS: npm ci from actual package lock, scoped Ruff and whitespace checks.
- Commands: `PYTHON=<Python3.13-venv> npm test --prefix contracts/template-v1`,
  `python contracts/template-v1/test_contract.py`, scoped Ruff and `git diff --check`.

## Dependency evidence and corrected alternatives

The pinned yamlcore0.1.1 wheel is6055 bytes, MIT, SHA256
85adda6abfe2ed6b13c80818d6b733f286bd6685314f7e6705321f4477f2dba1;
metadata was read from [PyPI](https://pypi.org/pypi/yamlcore/0.1.1/json).
Actual ruamel0.19.1 safe loaders with version1.2, both pure settings, still created dates and
legacy-number values. These probes rejected that unnecessary replacement before product code
changed. The implemented library Core profile keeps on/off/date and legacy numeric forms as
strings; ordinary octal/hex/exponents retain their real Core numeric meaning.
The scope follows the [YAML Core specification](https://yaml.org/spec/1.2.2/#103-core-schema),
with explicitly documented v1 JSON/alias/tag boundaries.

## Separate delivery gates

This producer commit does not update active consumer readers. Their exact source locks,
file-byte bounds, dependency/wheel builds and real entry paths must be verified afterward.
Actual official Devs parsing of the private project is a second phase; Node serialization
must preserve types there as well. No image, Agent turn, model request, cloud operation or
public package/catalog release is claimed by these checks.
