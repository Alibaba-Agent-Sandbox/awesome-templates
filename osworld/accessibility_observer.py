"""One native AT-SPI observation; no socket listener or persistent client cache."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import logging
from pathlib import Path
import shutil
import sys


def main():
    try:
        upstream = Path(sys.argv[1]).resolve(strict=True)
        sys.path.insert(0, str(upstream))
        spec = importlib.util.spec_from_file_location("owned_original_observer", upstream / "main.py")
        server = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(server)
            from runtime import normalize_nullable_attributes
            normalize_nullable_attributes(server.Accessible)
            if not shutil.which("libreoffice"):
                server._get_libreoffice_version = lambda: ()
            logging.disable(logging.CRITICAL)
            response = server.app.test_client().get("/accessibility")
            if response.status_code != 200:
                raise RuntimeError("native observation failed")
            tree = response.get_json()["AT"]
        if not isinstance(tree, str) or len(tree.encode()) > 2 * 1024 * 1024:
            raise RuntimeError("invalid bounded native tree")
        print(json.dumps({"tree": tree}, ensure_ascii=False))
        return 0
    except Exception:
        # Task content, raw native errors and paths never become protocol errors.
        print(json.dumps({"error": "native accessibility observation failed"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
