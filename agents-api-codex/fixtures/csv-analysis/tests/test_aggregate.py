"""Original exercise tests. The Agent must not change these assertions."""
from __future__ import annotations

import csv
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROGRAM = Path(__file__).resolve().parents[1] / "aggregate.py"


class AggregateTest(unittest.TestCase):
    def summarize(self, content: str) -> tuple[list[str] | None, list[dict[str, str]]]:
        with tempfile.TemporaryDirectory(prefix="agents-csv-check-") as temporary:
            root = Path(temporary)
            source, target = root / "input.csv", root / "summary.csv"
            source.write_text(content, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(PROGRAM), str(source), str(target)],
                capture_output=True, text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 0, "aggregation command failed")
            reader = csv.DictReader(io.StringIO(target.read_text(encoding="utf-8")))
            return reader.fieldnames, list(reader)

    def test_repeated_months_use_decimal_arithmetic(self) -> None:
        fields, rows = self.summarize(
            'month,amount,label\n2026-02,2.50,"North, renewal"\n'
            '2026-01,19.90,中文客户\n2026-02,7.50,Support\n2026-01,10.10,Launch\n'
        )
        self.assertEqual(fields, ["month", "total"])
        self.assertEqual(rows, [{"month": "2026-01", "total": "30.00"},
                                {"month": "2026-02", "total": "10.00"}])

    def test_negative_amounts_and_month_order(self) -> None:
        fields, rows = self.summarize("month,amount\n2025-12,4.25\n2025-11,9.90\n2025-12,-1.10\n")
        self.assertEqual(fields, ["month", "total"])
        self.assertEqual(rows, [{"month": "2025-11", "total": "9.90"},
                                {"month": "2025-12", "total": "3.15"}])

    def test_empty_input_keeps_the_schema(self) -> None:
        fields, rows = self.summarize("month,amount\n")
        self.assertEqual(fields, ["month", "total"])
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
