# Verification: current native coding SDK-created image

Date:2026-10-20. Result:PASS for actual OpenCode cloud runtime; latest-head PR/source gates and merge remain required. OriginalIssue17.

## OpenCode2.0.1

Unchanged runtime sourceca3118e5123e7ce2ae2e43e2a8a05c88ecf3653d. [Explicit image export39430931693](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/actions/runs/39430931693), artifact12268331301. [Exact source/image proof](../../../opencode/evidence/image-http-2026-10-20T142000Z.json) validates archive SHA25600775e2f32a0a78fd6e6cf9da183e178cc5b2259eb7201d086268bf582b80db6, native non-root context and common servere2cb27e24fde0a67112f82b8d44af463445a5d1a. Standalone Docker fallback remains a separate historical path, not the injected CI runtime.

[Actual SDK creation receipt](../../../opencode/evidence/express-2026-10-20.json): official READY, Python Sandbox.create, both version/setup commands via actual CLI and SDK, independent owned sandbox/template cleanup. Private-registry pre/post-runtime digest and independent registry deletion PASS. Model-off full HTTP15PASS/0FAIL/0SKIP is scoped to that basic stage; its model_acceptance=NOT_RUN does not erase the separate real-model run.

[Strict actual image/model controller](../../../opencode/evidence/model-image-2026-10-20T142001Z.json):28PASS/0FAIL/0SKIP, actual qwen3.8-flash via the approved OpenAI-compatible endpoint, existing-source modification/new artifact/unchanged original tests/fresh held-out assertions and exact-session continuation. Model-generated code executes only inside the owned cloud sandbox. Secondary owned server stopped; outer sandbox/template and registry absence independently confirmed. Commands SHA256e49f601544443658b517f14b60027e7f58dab71cbb38b8572139ea0a13802768; controllerc3fa6ad1e7c85d6681716464687e51aa71e56944d4c0fecac151bdd1af9ce1d6.

The same runtime hashes have [actual native platform-step basic acceptance](../../../opencode/evidence/verification-steps-2026-10-19T184023Z.json):83.703seconds,4CLI/SDK calls and cleanup PASS. That dated step receipt does not claim a model run. Historical failures remain immutable. Successful current image pipeline automatically deletes its local large image cache after independent cloud cleanup; source and public receipts remain.

Executed controller settings: actual immutable image runner with explicit sdk creation, real ABX_LLM_API_KEY/BASE_URL and OPENCODE_MODEL=dashscope/qwen3.8-flash in the explicitly owned native server; external e2e_test.py has E2E_REQUIRE_LLM=1/E2E_RUN_LLM=1. Credentials and raw logs are excluded. Reproduce basic image with scripts/run_ci_image_e2e.py and --sandbox-create sdk; strict model additionally requires the documented process configuration and existing strict e2e controller. Further source/protocol/links/current-head CI are pending and will be recorded separately.

Source regressions: python -m pytest -q opencode/test_commands.py opencode/test_e2e_protocol.py:56PASS in8.05seconds. Scoped strict checker and150Markdown local link checks PASS. These source checks are not another provider/model run.
