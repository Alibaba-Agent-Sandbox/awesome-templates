"""The local runner must never delete acceptance controller source."""
import tempfile
import unittest
from pathlib import Path

from run_local_e2e import _cleanup


class LocalCleanupTest(unittest.TestCase):
    def test_python_verifiers_survive_generated_output_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sources = {name: ("# " + name + "\n").encode()
                       for name in ("e2e_test.py", "e2e_sdk.py", ".e2e_helper.py")}
            for name, data in sources.items():
                (root / name).write_bytes(data)
            files = ["e2e_result.json", ".e2e_state", "screenshot_check.png"]
            directories = ["__pycache__", "abx_e2e_workspace", "e2e_output"]
            for name in files:
                (root / name).write_text("generated")
            for name in directories:
                (root / name).mkdir()
                (root / name / "generated").write_text("generated")
            _cleanup(root)
            for name, data in sources.items():
                self.assertTrue((root / name).is_file(), name)
                self.assertEqual((root / name).read_bytes(), data)
            for name in files + directories:
                self.assertFalse((root / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
