"""A delayed real Node startup must not make a missing entry look successful."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import shlex
import signal
import subprocess

import pytest


def test_missing_entry_rejected_before_delayed_node_startup(tmp_path, monkeypatch):
    node = shutil.which('node')
    assert node, 'This regression requires a real Node runtime'
    shim = tmp_path / 'bin'
    shim.mkdir()
    script = shim / 'node'
    script.write_text('#!/bin/sh\nsleep 3\nexec ' + shlex.quote(node) + ' "$@"\n')
    script.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('WORKSPACE', str(tmp_path))
    monkeypatch.setenv('PATH', str(shim) + os.pathsep + os.environ['PATH'])
    spec = importlib.util.spec_from_file_location('node_web_startup_regression', Path(__file__).with_name('commands.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    processes = []
    real_popen = subprocess.Popen

    def owned_popen(*args, **kwargs):
        process = real_popen(*args, **{**kwargs, 'start_new_session': True})
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, 'Popen', owned_popen)
    try:
        with pytest.raises((RuntimeError, ValueError), match='entry'):
            module.serve(entry='missing-entry.js', port=3999)
    finally:
        for process in processes:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate(timeout=5)
