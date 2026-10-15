#!/usr/bin/env python3
"""Print per-layer sizes for a local image so a template can be slimmed.

``docker history`` sizes are the uncompressed diff of each layer, which is
what a registry stores before gzip. A template that copies ``commands.py``
last, and installs heavy tools in an earlier ``RUN`` with ``--no-cache-dir``,
re-pushes only the small layer when the command file changes.

Usage:
  python3 scripts/image_size_report.py IMAGE
  python3 scripts/image_size_report.py IMAGE --base fc-e2b-registry.cn-hangzhou.cr.aliyuncs.com/runtime/base:v0.0.49
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any


_SIZE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?B)\s*$", re.IGNORECASE)
_UNITS = {"": 1, "B": 1, "KB": 1000, "MB": 1000**2, "GB": 1000**3, "TB": 1000**4}


def parse_size(text: str) -> int:
    """Parse a docker history size (``606MB``, ``16.9kB``, ``0B``) into bytes."""
    raw = text.strip()
    if not raw or raw == "0B":
        return 0
    match = _SIZE.fullmatch(raw)
    if not match:
        raise ValueError(f"unrecognized size {text!r}")
    number = float(match.group(1))
    unit = match.group(2).upper()
    if unit == "B":
        scale = 1
    else:
        scale = _UNITS[unit]
    return int(number * scale)


def format_bytes(size: int) -> str:
    if size < 1000:
        return f"{size}B"
    value = float(size)
    for unit in ("kB", "MB", "GB", "TB"):
        value /= 1000.0
        if value < 1000.0 or unit == "TB":
            if value >= 100 or unit == "kB" and value >= 10:
                return f"{value:.0f}{unit}"
            return f"{value:.1f}{unit}"
    return f"{size}B"


def render(
    rows: list[dict[str, Any]],
    *,
    image: str,
    total_bytes: int | None = None,
    shared_with_base: int | None = None,
    base_layers: int | None = None,
    base_image: str | None = None,
) -> str:
    """Format one history (newest layer first, as ``docker history`` prints it)."""
    parsed: list[tuple[int, str]] = []
    for row in rows:
        created = str(row.get("CreatedBy") or row.get("created_by") or "").strip()
        size_field = row.get("Size") if "Size" in row else row.get("size")
        if isinstance(size_field, int):
            size = size_field
        else:
            size = parse_size(str(size_field or "0B"))
        parsed.append((size, created.replace("\t", " ")))

    nonempty = [(size, created) for size, created in parsed if size > 0]
    summed = sum(size for size, _created in parsed)
    lines = [
        f"image {image}",
        f"layers {len(parsed)}  nonempty {len(nonempty)}  history_sum {format_bytes(summed)}",
    ]
    if total_bytes is not None:
        lines.append(f"image_size {format_bytes(total_bytes)}")
    if shared_with_base is not None and base_layers is not None:
        base_name = base_image or "base"
        lines.append(
            f"rootfs layers shared with {base_name}: {shared_with_base} of {base_layers} "
            "(a shared digest is not uploaded again when the registry accepts a mount)"
        )
    lines.append("")
    lines.append(f"{'SIZE':>10}  CREATED BY")
    for size, created in parsed:
        shown = created if len(created) <= 160 else created[:157] + "..."
        lines.append(f"{format_bytes(size):>10}  {shown}")

    lines.append("")
    if nonempty:
        biggest = max(nonempty, key=lambda item: item[0])
        lines.append(f"largest layer {format_bytes(biggest[0])}: {biggest[1][:120]}")
    small = [size for size, _created in nonempty if size < 8_000_000]
    if len(nonempty) > 15 and len(small) > 10:
        lines.append(
            f"{len(small)} nonempty layers are under 8MB. Each layer is a registry blob "
            "and a round trip. Install a tool in one RUN instead of many COPY layers."
        )
    last_copy = next((created for _size, created in parsed if created.upper().startswith("COPY ")), "")
    if last_copy and "commands.py" not in last_copy.split("WORKDIR", 1)[0]:
        lines.append(
            "The newest COPY is not commands.py. Put heavy installs in an early layer "
            "and copy commands.py last so a command edit does not re-push the tool layer."
        )
    elif not last_copy:
        lines.append("Copy commands.py in the last COPY so a command edit stays a small layer.")
    lines.append("Use pip install --no-cache-dir (and npm cache clean) so the tool layer does not keep a download cache.")
    return "\n".join(lines) + "\n"


def _docker_json_lines(args: list[str]) -> list[Any]:
    proc = subprocess.run(args, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "docker failed").strip()
        raise SystemExit(detail)
    found: list[Any] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        found.append(json.loads(line))
    return found


def _history(image: str) -> list[dict[str, Any]]:
    rows = _docker_json_lines(["docker", "history", "--no-trunc", "--format", "{{json .}}", image])
    return [row for row in rows if isinstance(row, dict)]


def _inspect(image: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["docker", "image", "inspect", image],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "docker inspect failed").strip()
        raise SystemExit(detail)
    payload = json.loads(proc.stdout)
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise SystemExit(f"docker inspect returned no object for {image}")
    return payload[0]


def _rootfs(info: dict[str, Any]) -> list[str]:
    root = info.get("RootFS")
    if not isinstance(root, dict):
        return []
    layers = root.get("Layers")
    if not isinstance(layers, list):
        return []
    return [str(item) for item in layers]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print per-layer sizes for a local Docker image.")
    parser.add_argument("image", help="Local image reference, for example repo:tag")
    parser.add_argument(
        "--base",
        default=None,
        help="Optional base image. Prints how many rootfs digests the image still shares with it.",
    )
    args = parser.parse_args(argv)
    info = _inspect(args.image)
    rows = _history(args.image)
    shared = None
    base_count = None
    if args.base:
        base_info = _inspect(args.base)
        image_layers = _rootfs(info)
        base_layers = _rootfs(base_info)
        shared = len(set(image_layers) & set(base_layers))
        base_count = len(base_layers)
    total = info.get("Size")
    text = render(
        rows,
        image=args.image,
        total_bytes=total if isinstance(total, int) else None,
        shared_with_base=shared,
        base_layers=base_count,
        base_image=args.base,
    )
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
