"""Isolated, buffered Playwright commands; no shared browser state or value logging."""
from __future__ import annotations

import json
import os
import subprocess
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
    try:
        result = subprocess.run(
            [sys.executable, str(path)], cwd=workspace, capture_output=True,
            text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Browser script exceeded timeout_s; captured output omitted") from None
    if result.returncode:
        raise RuntimeError(f"Browser script exited {result.returncode}; captured output omitted")
    return result.stdout


if __name__ == "__main__":
    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
