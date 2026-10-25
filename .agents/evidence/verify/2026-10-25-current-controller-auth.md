# Current controller authentication names

Date: 2026-10-25
Result: PARTIAL

Scope: current template HTTP/BYOK controllers, their focused tests, host helper and current usage docs. Dated historical evidence is unchanged.

Local checks: focused SDK/controller/HTTP suite 127 passed. It exercises real local HTTP transport with different application Bearer and provider X-Access-Token values, child environment exclusion and required model behavior. Initial run: four old assertions expected no gateway header, but public client 0.4.0a1 supplies a fallback X-Access-Token. Those tests now supply a distinct real provider header and assert it is retained; no compatibility code is introduced. A follow-up test invocation exposed one incorrect test-module target while editing tau2; corrected and all 127 passed. The independent SDK's no-gateway fallback policy is outside this template patch.

`python scripts/check_docs.py`: 222 Markdown documents, zero link failures. `python scripts/check_template.py --all`: all 47 source directories including skeleton conformant. All changed controller Python files compile. These checks are not cloud/model proof.

Pending: current-head CI and final public cloud reruns. The previously passing published matrix uses its original controller hashes and does not certify this later cleanup.

`python scripts/test_spec_tools.py`: 58 tests passed.
