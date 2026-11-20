# Verification: Agents API L1 image coverage

Result: PARTIAL.

- Based on templates draft head `048db39f5a865b07343ede2a93393ceab7f2df31` and the scoped workflow, helper and regression diff.
- `python -m pytest -q scripts/test_agents_api_family.py -k 'image_matrix or guest_npm'`: 2 passed, 12 subtests passed. The six actual profile descriptors select the corresponding native binary/version and Server Dockerfile. Ordinary Codex and Python Hello are controls. The Dockerfile shell probe uses bounded stand-ins.
- `python scripts/test_spec_tools.py`: 57 passed. The suite executes the real image context preparation for every catalog image and the image smoke plan for managed compact, expanded and ordinary configurations. The harness pin lookup lives in the existing shared image input `scripts/template_application.py`.
- The combined image selector and scoped family pytest run passed 31 cases and 12 subtests, with 2 unrelated cases deselected.
- Parsed the workflow with PyYAML and checked every image job shell block with `bash -n`. All six Guest package lines resolve to the paired expected version `0.4.0a8`.
- The prior PR head still had six failed published image checks. Both public PyPI JSON requests for `agent-sandbox-client` and `agent-sandbox-server` version `0.4.0a8` returned 404. Docker is unavailable locally, so neither published image was built here. The new workflow executes actual Guest binaries and paired Server import/module entry inside containers when the dependencies are available.
- No cloud or model calls were made.
