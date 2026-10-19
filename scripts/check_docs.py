#!/usr/bin/env python3
"""Check local Markdown links without network or cloud calls.

By default check tracked/unignored current documentation. Historical engineering
records are immutable and are checked only when explicitly passed as paths.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def prose(text: str) -> str:
    """Remove fenced and inline code so illustrative links are not executed."""
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return re.sub(r"(`+).*?\1", "", "\n".join(lines))


def targets(text: str) -> list[str]:
    text = prose(text)
    inline = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", text)
    refs = re.findall(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", text, re.M)
    return [item.strip("<>") for item in inline + refs]


def anchors(text: str) -> set[str]:
    found: set[str] = set()
    counts: dict[str, int] = {}
    # Keep inline code text in headings; GitHub includes it in the fragment.
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if not match:
            continue
        title = html.unescape(match[1]).lower()
        title = re.sub(r"<[^>]+>", "", title)
        title = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        index = counts.get(title, 0)
        counts[title] = index + 1
        found.add(title + (f"-{index}" if index else ""))
    found.update(re.findall(r'(?:id|name)=["\']([^"\']+)["\']', text))
    return found


def check_file(path: Path, root: Path = ROOT) -> list[str]:
    failures = []
    for raw in targets(path.read_text(encoding="utf-8")):
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc:
            continue
        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path.resolve()
        if not target.is_relative_to(root.resolve()):
            failures.append(f"{path.relative_to(root)}: link leaves repository: {raw}")
        elif not target.exists():
            failures.append(f"{path.relative_to(root)}: missing local target: {raw}")
        elif parsed.fragment and target.is_file() and target.suffix.lower() == ".md":
            fragment = unquote(parsed.fragment)
            if fragment not in anchors(target.read_text(encoding="utf-8")):
                failures.append(f"{path.relative_to(root)}: missing heading: {raw}")
    return failures


def current_documents(root: Path = ROOT) -> list[Path]:
    result = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*.md"],
                            cwd=root, check=True, capture_output=True)
    return sorted({root / name for name in result.stdout.decode().split("\0")
                   if name and not name.startswith(".agents/")})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = [path.resolve() for path in args.paths] if args.paths else current_documents()
    failures = [failure for path in paths for failure in check_file(path)]
    for failure in failures:
        print(failure)
    print(f"Markdown links: {len(paths)} documents; {len(failures)} failures (no network/cloud calls)")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
