# Verification: native Copilot CLI BYOK preparation

Date:2026-10-20. Result:PARTIAL; no provider/model qualification yet.

Public stable npm1.0.100 metadata and integrity verified, then npm ci --ignore-scripts --omit=optional installed the required native Linux x86_64 package. Only fixed --version/--help/help providers ran on operator, without credentials or prompts: all exit0; actual version1.0.100. The unmodified native binary SHA256 is0d0cfb14f1a214ebbe0edc20c509dce0bc4f2bd0e4310c849af5c436d4d9f321. Help confirms explicit BYOK needs no GitHub auth, wire API=completions/http, private COPILOT_HOME, closed available-tools, secret-env filtering and all used flags. Native-cache/tool relocation is local artifact maintenance, not cloud acceptance.

`python -m pytest -q copilot-cli/test_commands.py copilot-cli/test_model_controller.py`:23PASS in1.22seconds. These execute fixed authored subprocesses only; no native model or generated source runs on operator. The timeout case stops a marked detached child while a separately owned unrelated process survives. Native nonzero23 survives; configured test key is redacted and private HOME is removed. Local-target and malformed/error/tool-only model-result regressions reject false acceptance.

The first strict check identified four missing Issue-routing references and a false secret warning for the actual --no-ask-user flag; fixed the documentation and token-boundary scanner with a regression retaining actual credential-prefix detection. `python scripts/test_spec_tools.py`:57PASS in12.777seconds. `python scripts/check_template.py --all --strict`:0violations across35directories including scaffold; no provider pass inferred. `python scripts/check_docs.py`:157Markdown local-link targets,0failures before adding this record; rerun pending after record links. Current CI, source HTTP, native image/Express/model/cleanup remain required and unrun here.

Model controller uploads an authored failing project to the cloud target, requires real native completed response and independent target source/artifact/original-test/held-out checks, and verifies owned project absence. No provider is listed, manifest tested_on stays empty, catalog experimental/install-build. Partial source preparation does not close Issue64.

Targeted source HTTP: the first invocation used the system python3 without the task environment and failed startup with missing agent_sandbox; no model/cloud mutation occurred. Re-running the existing local harness with the task venv bin as PATH prefix yielded7PASS/0FAIL,1explicit missing-native SKIP and model NOT_RUN. This is source-only HTTP, not a native/provider pass.

Final preparation checks: strict checker0violations,157Markdown documents0link failures, both SDK snippets parse. Native keyless image smoke calls the actual pinned version and setup without an equality assertion on environment-dependent presence flags. The model/Express gates remain pending.
