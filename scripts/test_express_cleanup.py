"""Actual process descendants must be stopped after their leader exits."""
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
import express_e2e as harness

class ProcessCleanupTests(unittest.TestCase):
    def test_completed_cli_reaps_redirected_descendants(self):
        for code in (0, 7):
            with self.subTest(exit=code), tempfile.TemporaryDirectory() as directory:
                marker = Path(directory) / "survived"
                child = f"import time;time.sleep(1);open({str(marker)!r},'w').write('bad')"
                leader = "import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) + "],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);sys.exit(" + str(code) + ")"
                result = harness.run_monitored([sys.executable, "-c", leader], idle_timeout=5, wall_timeout=5)
                self.assertEqual(result.returncode, code)
                time.sleep(1.2)
                self.assertFalse(marker.exists())
