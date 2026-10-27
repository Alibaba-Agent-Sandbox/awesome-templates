# Preview an owned sandbox web application locally

[中文](preview-proxy.zh-CN.md). This operator-side relay supports a browser on the
same machine as the paired native Python SDK. The Alibaba default FC domain can
mark HTML as an attachment; the [official FC behavior](https://www.alibabacloud.com/help/en/functioncompute/web-functions)
explains that restriction. A configured custom preview domain remains available
for direct mode. This local operation uses the actual remote application and
verified upstream HTTPS (or a configured loopback HTTP OpenSandbox endpoint), then relays HTTP/WebSockets through a loopback listener.

## Install and open

Use CPython3.13 on Linux amd64 for the tested operator profile and install the
[paired native client](python-client-installation.md). From this repository:

```bash
python -m pip install --require-hashes -r scripts/requirements-preview.txt
python scripts/preview_proxy.py --sandbox-id <owned-sandbox-id> --remote-port 8443
```

Replace the ID with an exclusively caller-owned sandbox whose authenticated
code-server application is already running. The remote port defaults to8443;
another caller-owned application can use a different integer port1–65535.
Open the printed private loopback URL on the same machine. Complete the real
application login there. Stop the relay with Ctrl+C. The caller owns application
stop and sandbox destruction; the relay only closes its local listener, HTTP/WS
clients and RAM cookie jar. It never starts or destroys the borrowed sandbox.

The initial URL carries a random local entry capability, exchanged locally by a303 redirect to the application's canonical path before application login. Later requests require
an HttpOnly SameSite=Strict local cookie. Host and Origin checks accept only the
actual loopback origin. Application cookies stay in a per-relay RAM jar; unrelated
browser/local-port cookies are not sent upstream. The target is always the SDK's
fixed selected endpoint resolved with `await sandbox.network.resolve(port)`. SDK gateway headers remain only in the relay and override browser-supplied values for those names. They are preserved for both HTTP and WebSockets. SDK authentication query values are retained and cannot
be replaced by browser query parameters. Operator proxy settings are respected
without automatic netrc credential loading. Keep the printed local URL private.

## HTTP, WebSockets and limits

The relay removes an attachment Content-Disposition only for text/html. Other
downloads, compressed response bytes, application bodies and status codes remain
intact. HTTP bodies stream with backpressure; incoming bodies are capped at16MiB
and individual WebSocket messages at8MiB. HTTP requests have a300-second budget.
Binary/text WebSocket frames and the selected subprotocol are relayed. Redirects
outside the fixed owned endpoint are rejected. This is a local preview operation,
not a public hosting service or a claim that the default FC domain renders HTML.

Upstream HTTPS certificate and hostname validation remain required. An explicitly configured HTTP SDK endpoint is accepted only on literal loopback IPs or localhost, for a local OpenSandbox server; arbitrary remote cleartext endpoints remain rejected. The local
browser uses HTTP on127.0.0.1; no browser response interception or replacement
page is used. The relay and its dependencies are operator-side utilities and do
not change a template's image/runtime or remove application authentication.

## Verify code-server

Install Playwright1.58.0, its Chromium revision1208 and certutil (Debian's
libnss3-tools) for the existing isolated browser controller. On an exclusively
owned sandbox with no running IDE:

```bash
python code-server/browser_e2e_test.py --sandbox-id <owned-sandbox-id> --preview-mode sdk-local
```

The controller starts a password-authenticated real IDE, loads the JavaScript
workbench in actual Chromium, writes a nonce through the real terminal WebSocket,
edits/saves it through Monaco and independently reads bytes through the files
SDK. It then stops its IDE, removes its own file and closes the local relay.
The caller still owns sandbox destruction. Default --preview-mode direct keeps
the direct-domain test; forced HTML download remains a failure in that mode.
Results explicitly identify the preview mode, upstream TLS and cleanup. The
[2026-10-20 browser run](../code-server/evidence/browser-ui-2026-10-20T091440Z.json)
records the executed SDK-local preview and its original versions; it does not certify later inputs.
