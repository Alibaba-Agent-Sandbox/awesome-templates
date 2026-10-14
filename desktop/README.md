# desktop

E2B publishes a `desktop` template: Ubuntu 22.04, XFCE, and noVNC. The upstream definition lives in the E2B docs, not in this repository. This directory intentionally has no Dockerfile.

| Provider | Support |
|---|---|
| e2b | `Sandbox.create(provider="e2b", template="desktop")` |
| alicloud-express | No builtin named `desktop`. |
| alicloud-container | No. |
| cubesandbox | No. `pty` is also E8004 on this provider. |
| opensandbox | No release image is wired for this template. |

