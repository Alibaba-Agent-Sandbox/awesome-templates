"""Run a standalone HTTP controller with documented application authentication.

OpenSandbox's server proxy strips Authorization. Supply the same existing
X-Access-Token fallback as the public HTTP guide, only for the selected service
and only when the request already carries the correct application Bearer token.
"""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys

import httpx


def application_fallback(base_url: str, token: str):
    base = httpx.URL(base_url)
    origin = (base.scheme, base.host, base.port)
    prefix = base.path.rstrip("/")

    def apply(request: httpx.Request) -> None:
        target = request.url
        if ((target.scheme, target.host, target.port) != origin
                or not (target.path == prefix or target.path.startswith(prefix + "/"))):
            return
        # A streaming proxy otherwise frames a bodyless DELETE as chunked. The
        # bounded application server requires Content-Length; preserve explicit
        # lengths, streams and transfer encodings rather than rewriting them.
        if (request.method == "DELETE" and "Content-Length" not in request.headers
                and "Transfer-Encoding" not in request.headers):
            try:
                if request.content == b"":
                    request.headers["Content-Length"] = "0"
            except httpx.RequestNotRead:
                pass
        if (token and request.headers.get("Authorization") == "Bearer " + token
                and "X-Access-Token" not in request.headers):
            request.headers["X-Access-Token"] = token

    return apply


def main():
    target = Path(sys.argv[1]).resolve()
    fallback = application_fallback(os.environ["E2E_BASE_URL"], os.environ.get("ABX_SERVER_TOKEN", ""))
    original_init = httpx.Client.__init__

    def application_init(self, *args, **kwargs):
        hooks = dict(kwargs.pop("event_hooks", None) or {})
        hooks["request"] = [*hooks.get("request", []), fallback]
        original_init(self, *args, event_hooks=hooks, **kwargs)

    # Convenience functions retain their original Client class reference.
    # Updating the public constructor covers them as well as explicit clients,
    # while retaining caller hooks before the scoped authentication fallback.
    httpx.Client.__init__ = application_init
    sys.argv = [str(target), *sys.argv[2:]]
    sys.path.insert(0, str(target.parent))
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
