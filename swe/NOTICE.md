# Upstream attribution

This wrapper uses the official mini-swe-agent 2.4.6 distribution (MIT, copyright
2025 Kilian A. Lieret and Carlos E. Jimenez):
https://github.com/SWE-agent/mini-swe-agent/blob/v2.4.6/LICENSE.md
https://pypi.org/project/mini-swe-agent/2.4.6/

The runtime downloads the original Flask source snapshot
`7ee9ceb71e868944a46e1ff00b506772a53a4f1d` (BSD-3-Clause, copyright Pallets),
retaining its LICENSE.rst and other upstream notices:
https://github.com/pallets/flask/blob/7ee9ceb71e868944a46e1ff00b506772a53a4f1d/LICENSE.rst

`instance.json` contains the problem statement, original test patch and test
identities for `pallets__flask-5014` from SWE-bench Verified (MIT):
https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/tree/c104f840cc67f8b6eec6f759ebc8b2693d585d4a
https://github.com/SWE-bench/SWE-bench/blob/87ab1f6ced28f75ba73ca899dc759b019310944a/LICENSE

The benchmark gold solution patch is deliberately excluded. No model output,
private trajectory, credential, resource ID or full dataset is distributed here.

Full original license texts: [LICENSES.md](./LICENSES.md).
