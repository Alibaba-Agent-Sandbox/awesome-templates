# Chrome proxy authentication

Result: PARTIAL (both provider workflows PASS; Registry/public delivery pending)

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

## Fresh complete real-provider execution

Actual published CLI0.5.7/client-server0.4.0a6, source4c4d1a700b76135333d8a85f32008f59745cc926
(immutable combined verification branch; template folder tree exactly matches this
individual PR). Both Express and OpenSandbox complete native/public methods,
wrong-token, process/file round trips and fresh literal CLI/unchanged full README
SDK/direct HTTP business use PASS, with zero native failures/skips/not-run.
See per-provider complete JSON and method-audit.json in the adjacent evidence folder.
All owned sandbox/prepared/local/remote image artifacts independently absent,
zero retained/uncertain/cleanup failures. Registry qualification and publication
remain separate; original failures above are preserved.

Each provider:30 native assertions and9 documented checks PASS. Actual headed CDP
navigation, native authenticated VNC and same-session PNG bytes were independently
decoded. OpenSandbox explicitly uses server-proxy mode, exercising the fixed
X-Access-Token fallback through the actual Authorization-stripping server1.1.1.
