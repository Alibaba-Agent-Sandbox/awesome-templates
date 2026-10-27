"""Actual optional Docker regression for root-owned restrictive COPY inputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

import pytest


def test_nonroot_toolchain_from_restrictive_context():
    base = os.environ.get("NEXT_APP_TEST_BASE_IMAGE")
    if not base:
        pytest.skip("requires an explicit resolved default base and Docker")
    if "\n" in base or "\r" in base or base.startswith("-"):
        raise ValueError("base must be one resolved image reference")
    tag = "next-app-permissions-regression:" + uuid.uuid4().hex
    source = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="next-app-restrictive-") as temporary:
        context = Path(temporary)
        for name in ("package.json", "package-lock.json", "commands.py", "lifecycle.py"):
            shutil.copyfile(source / name, context / name)
            (context / name).chmod(0o600)
        recipe = (source / "Dockerfile").read_text().splitlines()
        assert recipe[0].startswith("FROM fc-e2b-registry.")
        recipe[0] = "FROM " + base
        (context / "Dockerfile").write_text("\n".join(recipe) + "\n")
        try:
            subprocess.run(["docker", "build", "-t", tag, str(context)],
                           check=True, capture_output=True, text=True, timeout=1800)
            check = subprocess.run(["docker", "run", "--rm", "--entrypoint", "python3", tag,
                "-c", "import json,os,commands; assert os.getuid()!=0; print(json.dumps(commands.toolchain_versions()))"],
                check=True, capture_output=True, text=True, timeout=60)
            assert json.loads(check.stdout) == {"next": "16.4.2", "react": "19.3.1",
                                               "react-dom": "19.3.1", "vite": "8.3.4"}
        finally:
            subprocess.run(["docker", "image", "rm", tag], capture_output=True, text=True)
            absent = subprocess.run(["docker", "image", "inspect", tag], capture_output=True, text=True)
            assert absent.returncode != 0, "owned regression image remains"
