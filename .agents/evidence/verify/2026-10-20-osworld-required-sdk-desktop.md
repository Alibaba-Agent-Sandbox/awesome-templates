# Verification: mandatory external OSWorld SDK desktop

Date:2026-10-20. Result:PARTIAL; real current-source cloud/native image and delivery pending.

Reviewed PR152baseline83a88853c82c0f4067fd9deed799e58dbd1125a8 has a real internal desktop named smoke but the external controller's GUI opt-in was unset, reporting6PASS/1GUI SKIP. The old full-HTTP classifier accepted this non-model skip. Reported in [review](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/152#issuecomment-6296258528); preserve its historical scope.

`python -m pytest -q scripts/test_step_acceptance.py scripts/test_steps_http.py osworld/test_commands.py osworld/test_tasks.py osworld/test_http.py`:88PASS in3.73seconds. Fixed authored worker/controller subprocesses only, not desktop/cloud evidence. New regression verifies E2E_REQUIRE_DESKTOP/E2E_RUN_DESKTOP=1, rejects a real controller subprocess GUI skip and rejects incomplete/missing desktop proof in the read-only auditor. Required18/0external acceptance has no model case. Runtime/image/source pins and commands remain unchanged; actual current-source cloud/L1 proof still pending before qualification/Issue36closure.

Preparation spec56PASS in12.699seconds, strict0violations,153Markdown documents0local-link failures. Optional operator OSS dependency2.19.1 installed using repository requirements; pip check reports no broken requirements. Official native CLIv0.4.1 Linux x64 source asset digest766b0b10c3e4c633632dad503ae7750183a8be41974a9d048f060836f8cb0c44 matched exact copied bytes; keyless --native --version exit0. No desktop/native model ran on operator.
