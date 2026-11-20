"""Small CSV exercise: repair aggregation, then add --with-share support.

The starter intentionally keeps only the last row of each month. Preserve the
command-line interface and the original tests while completing the exercise.
"""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from pathlib import Path


def summarize(source: Path, target: Path, *, with_share: bool = False) -> None:
    totals: dict[str, Decimal] = {}
    with source.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            # Exercise bug: repeated months must accumulate, not overwrite.
            totals[row["month"]] = Decimal(row["amount"])
    if with_share:
        raise NotImplementedError("Add the share column in the second turn")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["month", "total"])
        writer.writeheader()
        for month, total in sorted(totals.items()):
            writer.writerow({"month": month, "total": f"{total:.2f}"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--with-share", action="store_true")
    args = parser.parse_args()
    summarize(args.source, args.target, with_share=args.with_share)


if __name__ == "__main__":
    main()
