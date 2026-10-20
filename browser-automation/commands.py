"""Isolated, buffered Playwright commands; no shared browser state or value logging."""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlsplit
from uuid import uuid4

from agent_sandbox.server import command, start


def _workspace() -> Path:
    return Path(os.environ.get("WORKSPACE", "/home/user/app")).resolve()


def _validate(url: str, timeout_s: int) -> None:
    if not 1 <= timeout_s <= 120:
        raise ValueError("timeout_s must be between 1 and 120")
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https", "data"):
        raise ValueError("url must use http, https, or data")
    if parsed.username or parsed.password:
        raise ValueError("URL credentials are not allowed")
    if parsed.scheme in ("http", "https") and not parsed.hostname:
        raise ValueError("url must contain a host")
    if parsed.scheme == "data" and not url.startswith("data:text/html,"):
        raise ValueError("only data:text/html, inline pages are supported")


@contextmanager
def _page(url: str, timeout_s: int) -> Iterator[Any]:
    """Each request owns its browser in its HTTP worker thread."""
    _validate(url, timeout_s)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as runtime:
            browser = runtime.chromium.launch(
                headless=True, args=["--disable-dev-shm-usage"], timeout=timeout_s * 1000,
            )
            try:
                page = browser.new_page()
                page.set_default_timeout(timeout_s * 1000)
                page.goto(url, wait_until="load", timeout=timeout_s * 1000)
                yield page
            finally:
                browser.close()
    except Exception:
        # Playwright exceptions can contain URLs, form values and call logs.
        raise RuntimeError(
            "Browser operation failed; ensure pinned Playwright and Chromium are installed "
            "and the page and selectors are reachable. Request values are omitted."
        ) from None


def _screenshot(page: Any) -> str:
    directory = _workspace() / "browser-artifacts"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"screenshot-{uuid4().hex}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


@command("browse", description="Navigate and screenshot, extract text, list links, or return a summary.")
def browse(url: str, action: str = "screenshot", timeout_s: int = 30) -> dict[str, Any]:
    if action not in ("screenshot", "extract", "links", "full"):
        raise ValueError("action must be screenshot, extract, links, or full")
    with _page(url, timeout_s) as page:
        result: dict[str, Any] = {"action": action, "title": page.title()}
        if action == "screenshot":
            result["path"] = _screenshot(page)
        elif action == "extract":
            result["text"] = page.inner_text("body")
        elif action == "links":
            links = page.locator("a[href]").evaluate_all(
                "nodes => nodes.map(a => ({href: a.href, text: a.innerText.trim()}))"
            )
            result.update(count=len(links), links=links)
        else:
            result.update(screenshot=_screenshot(page), text_preview=page.inner_text("body")[:500])
        return result


@command("scrape", description="Extract visible text from elements matching a CSS selector.")
def scrape(url: str, selector: str, timeout_s: int = 30) -> dict[str, Any]:
    if not selector.strip():
        raise ValueError("selector must be non-empty")
    with _page(url, timeout_s) as page:
        texts = page.locator(selector).all_inner_texts()
        return {"count": len(texts), "texts": texts}


@command("fill_form", description="Fill fields without returning selectors, input values, or URL.")
def fill_form(url: str, fields_json: str, timeout_s: int = 30) -> dict[str, Any]:
    try:
        fields = json.loads(fields_json)
    except (ValueError, TypeError):
        raise ValueError("fields_json must encode a JSON array of selector/value objects") from None
    if not isinstance(fields, list) or not 1 <= len(fields) <= 100:
        raise ValueError("fields_json must contain between 1 and 100 fields")
    for field in fields:
        if not isinstance(field, dict) or set(field) != {"selector", "value"}:
            raise ValueError("each field must contain only selector and value")
        if not isinstance(field["selector"], str) or not field["selector"].strip():
            raise ValueError("each selector must be a non-empty string")
        if not isinstance(field["value"], str):
            raise ValueError("each value must be a string")
    with _page(url, timeout_s) as page:
        for field in fields:
            locator = page.locator(field["selector"])
            locator.fill(field["value"])
            if locator.input_value() != field["value"]:
                raise RuntimeError("Field verification failed")
        # Avoid page.url/title/DOM: page scripts can copy sensitive input into them.
        return {"fields_filled": len(fields)}


@command("run", description="Run a workspace Python browser script and return buffered stdout.")
def run(script: str = "main.py", timeout_s: int = 120) -> str:
    if not 1 <= timeout_s <= 120:
        raise ValueError("timeout_s must be between 1 and 120")
    workspace = _workspace()
    path = (workspace / script).resolve()
    if not path.is_relative_to(workspace) or not path.is_file():
        raise ValueError("script must be an existing file inside the workspace")
    code, stdout, _ = _browser_process.run_owned([sys.executable, str(path)], cwd=workspace, timeout=timeout_s)
    if code:
        raise RuntimeError(f"Browser script exited {code}; captured output omitted")
    return stdout


import tempfile as _browser_tempfile
import importlib.util as _browser_import
_browser_spec = _browser_import.spec_from_file_location('template_owned_browser_process', Path(__file__).with_name('browser_process.py'))
_browser_process = _browser_import.module_from_spec(_browser_spec)
_browser_spec.loader.exec_module(_browser_process)


@command("pdf", description="Render an A4 PDF with owned process deadline; return a workspace artifact path and size.")
def pdf(url: str, landscape: bool = False, print_background: bool = True, timeout_s: int = 30) -> dict:
    _validate(url, timeout_s)
    if type(landscape) is not bool or type(print_background) is not bool:
        raise ValueError("PDF flags must be booleans")
    if len(url.encode()) > 256*1024 or "\0" in url:
        raise ValueError("PDF URL must be at most256KiB with no NUL")
    directory = _workspace() / "browser-artifacts"
    if directory.is_symlink():
        raise ValueError("PDF artifact directory must not be a symlink")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ("pdf-" + uuid4().hex + ".pdf")
    with path.open("xb"):
        pass
    try:
        with _browser_tempfile.TemporaryFile() as payload:
            payload.write(json.dumps({"url":url,"path":str(path),"landscape":landscape,
                "print_background":print_background,"timeout_s":timeout_s}, ensure_ascii=False).encode())
            payload.seek(0)
            code, _, _ = _browser_process.run_owned([sys.executable, str(Path(__file__).with_name("pdf_worker.py"))],
                cwd=_workspace(), timeout=timeout_s, input_file=payload, private_home=True)
        if code or not 100 <= path.stat().st_size <= 16*1024**2:
            raise RuntimeError("PDF renderer failed or artifact exceeded16MiB; diagnostics omitted")
        with path.open("rb") as stream:
            if not stream.read(5) == b"%PDF-":
                raise RuntimeError("PDF renderer did not create a PDF")
        return {"path":str(path),"bytes":path.stat().st_size,"format":"PDF"}
    except BaseException:
        path.unlink(missing_ok=True)
        raise


# Load only the local helper definitions; no listener/browser starts on import.
import importlib.util as _mcp_import
_mcp_spec = _mcp_import.spec_from_file_location('template_browser_mcp', Path(__file__).with_name('mcp_runtime.py'))
_mcp = _mcp_import.module_from_spec(_mcp_spec)
_mcp_spec.loader.exec_module(_mcp)


@command("mcp_start", description="Start actual Playwright MCP0.0.83 on sandbox-loopback8931 using existing Chromium.")
def mcp_start() -> dict:
    return _mcp.start()


@command("mcp_status", description="Inspect only this command server's owned MCP; never scans credentials.")
def mcp_status() -> dict:
    return _mcp.status()


@command("mcp_call", description="Call owned actual MCP tools/list, tools/call or ping through authenticated command transport.")
def mcp_call(method: str, params_json: str = "{}") -> dict:
    return _mcp.call(method, params_json)


@command("mcp_stop", description="Close the owned MCP session, process group and marked browser workers; verify listener absence.")
def mcp_stop() -> dict:
    return _mcp.stop()


@command("mcp_self_test", description="Actual native MCP initializes, lists tools, clicks a real counter twice, screenshots and cleans its fixture.")
def mcp_self_test() -> str:
    return _mcp.self_test()


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
