# Verification: source-manifest binding during step review

Date:2026-10-20. Result:PASS for local classifier/materializer regressions; remote CI/normal merge pending. No cloud resource/model call is made by these checks.

Before the fix, source at PR152head143afff686d0d13f22b162baff788af11257b591 (and later83a88853c82c0f4067fd9deed799e58dbd1125a8) ignored the recorded raw template.yaml hash. A synthetic receipt with unchanged version/smoke/Docker/commands still passed after same-version start_cmd/resource/env changes; this false PASS was reproduced and reported in [the review](https://github.com/Alibaba-Agent-Sandbox/awesome-templates/pull/152#issuecomment-6295663190).

`python -m pytest -q scripts/test_step_acceptance.py scripts/test_prepare_steps.py`:60PASS in25.25seconds. Positive controls retain exact legacy receipts without Git and qualification-only changes with the original bytes bound to their SHA256 in immutable local history. Negative controls reject seven classes of same-version manifest changes, missing/malformed/bad source bindings, unavailable/mismatched recorded revisions and current required SDK pin/input changes. Real authored local Git fixtures use explicit fixed commits, never remote/model code.

`python scripts/step_acceptance.py --require-http`: exit0,33/33runtime and33/33full-HTTP profiles PASS on this exact reviewed baseline, using its existing immutable cloud receipts. This is a read-only classification, not33fresh cloud deployments, not model validation and not a claim about future catalog/source revisions. Legacy inline-copy receipts are accepted only after exact original raw SHA256 bytes are recovered; missing/shallow history fails closed. Canonical new proof binds all manifest fields except tested_on. No historical receipt was modified. Final spec/docs/current-head CI and merge remain delivery gates.

Final source/document gates: `python scripts/test_spec_tools.py`:56PASS in12.710seconds; strict checker0violations;153Markdown local-link checks0failures; git diff --check clean. These remain local checks, not latest-head CI or a merged-state claim.
