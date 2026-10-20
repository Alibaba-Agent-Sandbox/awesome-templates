"""Pinned native HTTP probe contracts; no fixture is provider acceptance."""
import importlib.util
from pathlib import Path

import httpx
import pytest

spec = importlib.util.spec_from_file_location('openclaw_sdk_controller', Path(__file__).with_name('sdk_e2e_test.py'))
controller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controller)


@pytest.mark.parametrize('endpoint,status,body,expected', [
    ('healthz', 200, {'ok': True, 'status': 'live'}, True),
    ('readyz', 200, {'ready': True}, True),
    ('readyz', 200, {'ready': True, 'failing': []}, True),
    ('readyz', 503, {'ready': False}, False),
    ('readyz', 200, {'ok': True}, False),
    ('readyz', 200, {'ready': 1}, False),
    ('readyz', 200, {'ready': 'true'}, False),
    ('readyz', 401, {'ready': True}, False),
    ('healthz', 200, {'ready': True}, False),
    ('healthz', 200, [], False),
])
def test_actual_liveness_and_readiness_are_distinct(endpoint, status, body, expected):
    assert controller.probe_succeeded(endpoint, httpx.Response(status, json=body)) is expected


def test_html_gateway_error_cannot_pass_readiness():
    assert not controller.probe_succeeded('readyz', httpx.Response(200, text='<html>proxy error</html>'))
