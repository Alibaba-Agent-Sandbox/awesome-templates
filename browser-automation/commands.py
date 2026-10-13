"""browser-automation 模板命令 — 基于内置 BROWSER 能力组的高层浏览器自动化。

本模板利用 Server 提供的 CapabilityGroup.BROWSER 能力组（8 个内置端点），
并在此之上注册面向 AI Agent 的高层业务命令：

- browse   — 智能浏览（导航 + 截图 / 提取文本 / 提取链接 / 全量信息）
- scrape   — 按 CSS 选择器提取元素文本
- fill_form — 自动填写表单

内置 BROWSER 端点（由 CapabilityGroup.BROWSER 启用）：
    POST /browser/navigate, POST /browser/screenshot, GET /browser/content,
    POST /browser/click, POST /browser/type, POST /browser/evaluate,
    POST /browser/pdf, GET /browser/console
"""
from __future__ import annotations

import json
import time
from typing import Any

from agent_sandbox.server import (
    CapabilityGroup,
    command,
    default_table,
    start,
)

# ---------------------------------------------------------------------------
# Opt-in capability group
# ---------------------------------------------------------------------------

table = default_table()
table.enable_group(CapabilityGroup.BROWSER)    # opt-in: 8 built-in browser endpoints

# ---------------------------------------------------------------------------
# Module-level Playwright singleton (lazy-initialised)
# ---------------------------------------------------------------------------

_playwright: Any = None
_browser: Any = None
_page: Any = None


def _ensure_browser() -> Any:
    """Return the shared Playwright *page*, creating the singleton on first call.

    The browser instance persists across command invocations for performance.
    """
    global _playwright, _browser, _page  # noqa: PLW0603

    if _page is not None and not _page.is_closed():
        return _page

    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    if _playwright is None:
        _playwright = sync_playwright().start()
        _browser = _playwright.chromium.launch(headless=True)

    _page = _browser.new_page()
    return _page


# ---------------------------------------------------------------------------
# Named commands — high-level business commands
# ---------------------------------------------------------------------------

@command(
    "browse",
    description=(
        "Smart browse — navigate to a URL and perform an action. "
        "action: screenshot | extract | links | full"
    ),
)
def browse(url: str, action: str = "screenshot") -> dict[str, Any]:
    """Navigate to *url* and execute *action*.

    Actions:
        screenshot — take a screenshot, return the saved file path.
        extract    — return the page's visible text content.
        links      — extract all hyperlinks as a list of {href, text} objects.
        full       — screenshot + title + first 500 chars of text.
    """
    page = _ensure_browser()
    page.goto(url, wait_until="networkidle", timeout=30000)

    if action == "screenshot":
        ts = int(time.time() * 1000)
        path = f"/app/screenshot_{ts}.png"
        page.screenshot(path=path, full_page=True)
        return {"action": "screenshot", "url": page.url, "path": path}

    if action == "extract":
        text = page.inner_text("body")
        return {"action": "extract", "url": page.url, "title": page.title(), "text": text}

    if action == "links":
        raw_links = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href, text: a.innerText.trim()
            }))"""
        )
        return {"action": "links", "url": page.url, "count": len(raw_links), "links": raw_links}

    if action == "full":
        ts = int(time.time() * 1000)
        path = f"/app/screenshot_{ts}.png"
        page.screenshot(path=path, full_page=True)
        text = page.inner_text("body")
        return {
            "action": "full",
            "url": page.url,
            "title": page.title(),
            "screenshot": path,
            "text_preview": text[:500],
        }

    raise ValueError(f"Unknown action: {action!r}. Expected: screenshot, extract, links, full")


@command(
    "scrape",
    description="Scrape — navigate to a URL and extract text from a CSS selector.",
)
def scrape(url: str, selector: str) -> dict[str, Any]:
    """Navigate to *url* and return the text content of elements matching *selector*."""
    page = _ensure_browser()
    page.goto(url, wait_until="networkidle", timeout=30000)

    elements = page.query_selector_all(selector)
    if not elements:
        return {
            "url": page.url,
            "selector": selector,
            "count": 0,
            "texts": [],
        }

    texts = [el.inner_text() for el in elements]
    return {
        "url": page.url,
        "selector": selector,
        "count": len(texts),
        "texts": texts,
    }


@command(
    "fill_form",
    description=(
        "Auto-fill a form — navigate to a URL and fill fields. "
        'fields_json: \'[{"selector": "#email", "value": "test@example.com"}]\''
    ),
)
def fill_form(url: str, fields_json: str) -> dict[str, Any]:
    """Navigate to *url* and fill form fields described by *fields_json*.

    *fields_json* is a JSON array of objects, each with ``selector`` and ``value``::

        [{"selector": "#email", "value": "test@example.com"},
         {"selector": "#password", "value": "secret"}]
    """
    page = _ensure_browser()
    page.goto(url, wait_until="networkidle", timeout=30000)

    fields: list[dict[str, str]] = json.loads(fields_json)
    filled: list[dict[str, str]] = []

    for field in fields:
        sel = field["selector"]
        val = field["value"]
        page.fill(sel, val)
        filled.append({"selector": sel, "value": val})

    return {
        "url": page.url,
        "fields_filled": len(filled),
        "details": filled,
    }


# ---------------------------------------------------------------------------
# Hidden diagnostic command
# ---------------------------------------------------------------------------


@command(hidden=True)
def _browser_status() -> dict[str, Any]:
    """Return the current browser singleton status (not listed in /commands)."""
    running = _browser is not None and _browser.is_connected()
    current_url: str | None = None
    pages = 0

    if running and _browser is not None:
        contexts = _browser.contexts
        for ctx in contexts:
            pages += len(ctx.pages)
        if _page is not None and not _page.is_closed():
            current_url = _page.url

    return {
        "browser_running": running,
        "current_url": current_url,
        "pages": pages,
    }


# ---------------------------------------------------------------------------
# Freeze & serve
# ---------------------------------------------------------------------------


def _run(argv: list[str], *, timeout: int, cwd: str = "/app") -> str:
    """Run *argv* in ``/app`` when that directory exists and return stdout."""
    import os
    import subprocess

    workdir = cwd if os.path.isdir(cwd) else (os.environ.get("WORKSPACE") or os.getcwd())
    result = subprocess.run(
        argv, cwd=workdir, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(detail or f"command exited {result.returncode}")
    return result.stdout



@command("run", description="Run a browser automation script.")
def run(script: str = "main.py") -> str:
    """Run a Python script (``python3 {script}``)."""
    return _run(["python3", script], timeout=120)


if __name__ == "__main__":
    import os

    start(int(os.environ.get("ABX_SERVER_PORT", "9000")))
