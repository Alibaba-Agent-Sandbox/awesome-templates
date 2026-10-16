"""Actual subprocess regressions: failure diagnostics must not echo request data."""
import sys

import pytest

from commands import _run


MARKER = "synthetic-private-python-value"


def test_nonzero_stderr_is_private():
    with pytest.raises(RuntimeError) as error:
        _run([sys.executable, "-c", f"import sys; print('{MARKER}', file=sys.stderr); sys.exit(7)"], timeout=5)
    assert str(error.value) == "Python command exited 7; output omitted"
    assert MARKER not in str(error.value)


def test_nonzero_stdout_is_private():
    with pytest.raises(RuntimeError) as error:
        _run([sys.executable, "-c", f"import sys; print('{MARKER}'); sys.exit(8)"], timeout=5)
    assert str(error.value) == "Python command exited 8; output omitted"
    assert MARKER not in str(error.value)


def test_deadline_omits_inline_source():
    with pytest.raises(RuntimeError) as error:
        _run([sys.executable, "-c", f"import time; secret='{MARKER}'; time.sleep(5)"], timeout=0.1)
    assert str(error.value) == "Python command exceeded its execution deadline; output omitted"
    assert MARKER not in str(error.value)


def test_startup_failure_omits_executable_path(tmp_path):
    with pytest.raises(RuntimeError) as error:
        _run([str(tmp_path / MARKER / "missing-python")], timeout=5)
    assert str(error.value) == "Python command could not start; request details omitted"
    assert MARKER not in str(error.value)
