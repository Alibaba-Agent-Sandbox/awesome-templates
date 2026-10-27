# Chrome proxy authentication

Result: PARTIAL (local regression fixed; real-provider reruns required)

Date2026-10-27. Original OpenSandbox source46b7c1ccc01eae9cf41292dde89ab32411ed5f79:
15 native passes/1 failure/zero skips/not-run; JSONDecodeError at CDP flow, no fresh
documented business pass. All owned sandbox/template/local/remote artifacts absent.
[Original failure](2026-10-27-chrome-proxy-auth/original-opensandbox-failure.json).

A real loopback Authorization-stripping proxy returns401 on original relay and
200 after the fix. Direct correct Bearer still works; wrong/missing fallback and
wrong/unsupported explicit Authorization reject, including correct fallback with
wrong Bearer. No authentication removal or native VNC protocol substitution.

`pytest chrome/test_commands.py chrome/test_protocol.py`: PASS27.
`python scripts/test_spec_tools.py`: PASS39.
`python scripts/check_template.py --all`: PASS, zero claimed spec failures.
`python scripts/check_docs.py`: PASS224 documents, zero link failures.
Final secret/diff scan, native Express/OpenSandbox full method/GUI/documented
reruns, exact cleanup, final-head CI and source/Registry publication remain required.
