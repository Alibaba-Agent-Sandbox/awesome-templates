"""Keep standalone templates' owned-process helpers on reviewed canonical sources.

Run with --check in CI, or without it after editing scripts/process_runners/.
Only runner source is synchronized; template command arguments and policies stay local.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNNERS = {
    **dict.fromkeys(["deepseek-harness", "hermes-agent", "openclaw", "pi", "qoder", "qwen-code", "amp", "gemini"], "text"),
    **dict.fromkeys(["apply-patch", "code-server", "goose"], "file"),
    "kimi-code": "bounded_text",
    "aider": "confirmations",
    "qm": "qm_invoke",
    "qm-sandbox": "qm_invoke",
}


def runner(source: str, name: str = "_run_process") -> ast.FunctionDef:
    return next(node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name)


def synchronize(check: bool) -> int:
    failures = []
    for template, kind in RUNNERS.items():
        path = ROOT / template / "commands.py"
        source = path.read_text()
        canonical = (ROOT / "scripts" / "process_runners" / f"{kind}.py").read_text()
        name = "invoke" if kind == "qm_invoke" else "_run_process"
        canonical_fn = runner(canonical, name)
        expected = "\n".join(canonical.splitlines()[canonical_fn.lineno - 1:canonical_fn.end_lineno])
        if template in {"amp", "gemini"}:
            expected = expected.replace('f"command timed out after', f'f"{template} timed out after')
        actual_fn = runner(source, name)
        actual = "\n".join(source.splitlines()[actual_fn.lineno - 1:actual_fn.end_lineno])
        marker = f"# Generated from scripts/process_runners/{kind}.py; update with scripts/sync_process_runners.py."
        lines = source.splitlines()
        marked = actual_fn.lineno > 1 and lines[actual_fn.lineno - 2] == marker
        if actual != expected or not marked:
            if check:
                failures.append(template)
                continue
            # This migration must preserve exact executable structure, not merely similar output.
            if not marked and ast.dump(ast.parse(actual), include_attributes=False) != ast.dump(ast.parse(expected), include_attributes=False):
                raise ValueError(f"{template}: runner behavior differs; review its policy before syncing")
            start = actual_fn.lineno - 2 if marked else actual_fn.lineno - 1
            lines[start:actual_fn.end_lineno] = [marker, expected]
            path.write_text("\n".join(lines) + "\n")
    if failures:
        print("Process runners differ from canonical sources: " + ", ".join(failures))
        return 1
    print(f"PASS: {len(RUNNERS)} standalone runtime helpers match their canonical sources")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    raise SystemExit(synchronize(parser.parse_args().check))
