# code-interpreter-v1

This directory is a catalog pointer for the public template id `code-interpreter-v1`. It is not a rebuild of that image.

| Provider | How to create |
|---|---|
| alicloud-express | `Sandbox.create(template="code-interpreter-v1")`. Builtin. No install step. |
| e2b | `Sandbox.create(provider="e2b", template="code-interpreter-v1")`. This is the template the E2B Code Interpreter SDK uses. |
| alicloud-container | Only when that template id is already registered on the sandbox-manager. |
| cubesandbox | Only when that template id is already registered. `code.interpret` on Cube falls back to a shell command if the Connect code route returns 404. |
| opensandbox | Do not pass the name `code-interpreter-v1`. Use `opensandbox/code-interpreter` (see `opensandbox-code-interpreter`). `run_code` on the OpenSandbox provider returns E8004. |

