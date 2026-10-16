#!/usr/bin/env python3
"""Verify source-runtime startup isolation without importing its cloud CLI."""
from __future__ import annotations

import ast
from pathlib import Path
import secrets
import subprocess
import sys
from types import SimpleNamespace
import unittest

RUNNER = Path(__file__).with_name('express_runtime_e2e.py')


def socket_expression() -> ast.expr:
    """Select the actual startup environment assignment without running cloud code."""
    module = ast.parse(RUNNER.read_text(encoding='utf-8'))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (isinstance(target, ast.Subscript)
                    and ast.unparse(target.value) == 'os.environ'
                    and isinstance(target.slice, ast.Constant)
                    and target.slice.value == 'ABX_ENGINE_SOCKET'):
                return node.value
    raise AssertionError('source-runtime startup must explicitly isolate its engine socket')


def isolated_socket() -> str:
    # Native execs can share a filesystem while exposing identical PID values.
    return eval(compile(ast.Expression(socket_expression()), str(RUNNER), 'eval'), {
        'os': SimpleNamespace(getpid=lambda: 3), 'secrets': secrets,
    })


class RuntimeSocketIsolation(unittest.TestCase):
    def test_same_pid_startups_have_independent_engine_sockets(self) -> None:
        sockets = [isolated_socket() for _ in range(4)]
        self.assertEqual(len(set(sockets)), len(sockets),
                         'concurrent runs must not attach to another run with the same PID')

    def test_socket_stays_local_and_within_grpc_path_limit(self) -> None:
        socket = isolated_socket()
        self.assertEqual(Path(socket).parent, Path('/tmp'))
        self.assertLessEqual(len(socket.encode()), 104)

    def test_separate_processes_with_identical_pid_view_are_isolated(self) -> None:
        expression = ast.unparse(socket_expression())
        code = ('import secrets; from types import SimpleNamespace; '
                'os = SimpleNamespace(getpid=lambda: 3); print(' + expression + ')')
        first = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
        second = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
        self.assertNotEqual(first, second,
                            'process-local PID namespaces must not select a shared engine')


if __name__ == '__main__':
    unittest.main()
