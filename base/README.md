# base

This directory is a catalog pointer. It is not a Dockerfile, and `abx deploy` here does not build an image.

| Provider | How to create |
|---|---|
| alicloud-express | `Sandbox.create(template="base")` or `abx create --template base`. The CLI treats `base` as a builtin and does not install this directory. |
| e2b | `Sandbox.create(provider="e2b", template="base")` when `ABX_E2B_API_KEY` is set. E2B's image is `e2bdev/base` (Debian, Python, Node, git). |
| alicloud-container | Only if the cluster already has a template id `base`. This provider rejects template build (E8004). |
| cubesandbox | Only if CubeAPI already has template id `base`. Template build is E8004. |
| opensandbox | The adapter rewrites the name `base` to `python:3.12-slim` and sets the entrypoint to `tail -f /dev/null`. The container does not run a Dockerfile `CMD`. |

Do not send the Express API key to `api.e2b.dev`. E2B reads `ABX_E2B_API_KEY` only.
