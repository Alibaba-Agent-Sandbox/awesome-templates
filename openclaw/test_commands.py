"""Gateway ownership, bounded execution and argument regressions."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import socket
import sys
import time

import pytest

spec = importlib.util.spec_from_file_location("openclaw_template", Path(__file__).with_name("commands.py"))
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


def test_missing_token_never_launches(monkeypatch):
    monkeypatch.delenv("OPENCLAW_GATEWAY_TOKEN", raising=False)
    monkeypatch.setattr(commands.subprocess, "Popen", lambda *a, **kw: pytest.fail("unexpected process"))
    with pytest.raises(RuntimeError, match="OPENCLAW_GATEWAY_TOKEN is required"):
        commands.gateway_start()


@pytest.mark.parametrize('value', ['0.0.0.0/0', '::/0', '224.0.0.0/4',
                                 '::ffff:0:0/96', '::fffe:0:0/95',
                                 'https://proxy.invalid/', '127.0.0.1,,::1',
                                 ','.join(['127.0.0.1'] * 17), 'x' * 2049])
def test_invalid_operator_proxy_list_never_launches(value, monkeypatch):
    monkeypatch.setenv('OPENCLAW_GATEWAY_TOKEN', 'synthetic-unit-test-token')
    monkeypatch.setenv('OPENCLAW_TRUSTED_PROXIES', value)
    monkeypatch.setattr(commands, '_binary', lambda: sys.executable)
    monkeypatch.setattr(commands.subprocess, 'Popen', lambda *a, **kw: pytest.fail('unexpected process'))
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        port = available.getsockname()[1]
    with pytest.raises(ValueError, match='OPENCLAW_TRUSTED_PROXIES'):
        commands.gateway_start(port=port, bind='lan')
    assert commands._STATE is None


def test_explicit_proxy_ips_reach_isolated_native_config_and_cleanup(monkeypatch):
    monkeypatch.setenv('OPENCLAW_GATEWAY_TOKEN', 'synthetic-unit-test-token')
    monkeypatch.setenv('OPENCLAW_TRUSTED_PROXIES', '192.0.2.8,2001:db8::/64,192.0.2.8/32')
    monkeypatch.setattr(commands, '_binary', lambda: sys.executable)
    original_popen = subprocess.Popen
    captured = {}

    def launch(*args, **kwargs):
        state = Path(kwargs['cwd'])
        captured['state'] = state
        captured['config'] = json.loads((state / 'openclaw.json').read_text())
        return original_popen([sys.executable, '-c', 'import time;time.sleep(30)'], **kwargs)

    monkeypatch.setattr(commands.subprocess, 'Popen', launch)
    monkeypatch.setattr(commands, '_probe', lambda timeout: True)
    with socket.socket() as available:
        available.bind(('127.0.0.1', 0))
        port = available.getsockname()[1]
    try:
        assert commands.gateway_start(port=port, bind='lan')['healthy'] is True
        assert captured['config']['gateway']['trustedProxies'] == ['192.0.2.8/32', '2001:db8::/64']
        assert captured['config']['gateway']['auth']['token'] == '${OPENCLAW_GATEWAY_TOKEN}'
    finally:
        commands.gateway_stop(command_timeout=1)
    assert not captured['state'].exists()


@pytest.mark.parametrize("args", [{"port": 80}, {"port": 9000}, {"port": 65536}, {"command_timeout": 0}, {"command_timeout": 121}, {"bind": "public"}])
def test_invalid_args(args):
    with pytest.raises(ValueError):
        commands.gateway_start(**args)


def test_alias_rejects_unknown_action_without_cli():
    with pytest.raises(ValueError, match="action must be"):
        commands.gateway(action="__invalid__")


def test_status_does_not_claim_health():
    assert commands.gateway_status() == {"running": False, "owned": False, "url": None}


def test_stop_ignores_stale_pid_file(tmp_path, monkeypatch):
    # An unrelated process appears in a legacy-looking pid file. No owned handle
    # means stop must not send any signal to it.
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        (tmp_path / "gateway.pid").write_text(str(child.pid))
        monkeypatch.chdir(tmp_path)
        assert commands.gateway_stop() == {"running": False, "owned": False}
        assert child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=5)


def test_stop_only_owned_process_and_is_idempotent():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    commands._PROCESS = child
    assert commands.gateway_status()["running"] is True
    assert commands.gateway_stop(command_timeout=1)["running"] is False
    assert child.poll() is not None
    assert commands.gateway_stop(command_timeout=1)["running"] is False


def test_health_requires_authenticated_rpc(monkeypatch):
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], start_new_session=True)
    commands._PROCESS = child
    monkeypatch.setattr(commands, "_binary", lambda: sys.executable)
    # A living PID doesn't implement OpenClaw authenticated RPC.
    try:
        with pytest.raises(RuntimeError, match="health check failed"):
            commands.gateway_health(command_timeout=1)
    finally:
        commands.gateway_stop(command_timeout=1)


def test_start_timeout_cleans_owned_process(monkeypatch):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "synthetic-unit-test-token")
    monkeypatch.setattr(commands, "_binary", lambda: sys.executable)
    original_popen = subprocess.Popen
    children = []
    def launch(*args, **kwargs):
        child = original_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(commands.subprocess, "Popen", launch)
    monkeypatch.setattr(commands, "_probe", lambda timeout: False)
    with pytest.raises(RuntimeError, match="before timeout"):
        commands.gateway_start(port=29876, command_timeout=1)
    assert children[0].poll() is not None
    assert commands._PROCESS is None
    assert commands._STATE is None


def test_stop_kills_term_ignoring_descendant_after_leader_exits(tmp_path):
    marker = tmp_path / "descendant-survived"
    ready = tmp_path / "descendant-ready"
    child = ("import signal,time;from pathlib import Path;"
             "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(2);Path({str(marker)!r}).write_text('bad');time.sleep(30)")
    parent = "import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);time.sleep(30)"
    process = subprocess.Popen([sys.executable, "-c", parent], start_new_session=True)
    commands._PROCESS = process
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        assert commands.gateway_stop(command_timeout=1)["running"] is False
        assert process.poll() is not None
        time.sleep(1.2)
        assert not marker.exists()
    finally:
        commands.gateway_stop(command_timeout=1)


def test_stop_cleans_group_when_owned_leader_already_exited(tmp_path):
    marker = tmp_path / "orphan-survived"
    ready = tmp_path / "orphan-ready"
    child = ("import signal,time;from pathlib import Path;"
             "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(2);Path({str(marker)!r}).write_text('bad');time.sleep(30)")
    parent = "import subprocess,sys;subprocess.Popen([sys.executable,'-c'," + repr(child) + "])"
    process = subprocess.Popen([sys.executable, "-c", parent], start_new_session=True)
    commands._PROCESS = process
    try:
        deadline = time.monotonic() + 5
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists()
        assert commands.gateway_status()["running"] is False
        # Status deliberately didn't reap the dead leader or expose its PID.
        assert process.returncode is None
        assert commands.gateway_stop(command_timeout=1)["running"] is False
        time.sleep(1.2)
        assert not marker.exists()
    finally:
        commands.gateway_stop(command_timeout=1)


@pytest.mark.parametrize("exit_code", [0, 7])
def test_completed_leader_stops_owned_children_with_redirected_stdio(tmp_path, exit_code):
    """A successful/error parent exit must never leave its owned worker running."""
    marker = tmp_path / "escaped-completion"
    ready = tmp_path / "child-ready"
    child = ("import time;from pathlib import Path;"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(1.3);Path({str(marker)!r}).write_text('bad')")
    leader = ("import subprocess,sys,time;from pathlib import Path;"
              "subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
              f"ready=Path({str(ready)!r});"
              "deadline=time.monotonic()+3\n"
              "while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)\n"
              "print('leader-output',flush=True);sys.exit(" + str(exit_code) + ")")
    code, stdout, stderr = commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=5)
    assert ready.exists()
    assert code == exit_code and stdout == "leader-output\n" and stderr == ""
    time.sleep(1.5)
    assert not marker.exists()


def test_deadline_leader_exit_cannot_orphan_term_ignoring_child(tmp_path):
    marker = tmp_path / "escaped-timeout"
    ready = tmp_path / "ignoring-child-ready"
    child = ("import signal,time;from pathlib import Path;"
             "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(2);Path({str(marker)!r}).write_text('bad');time.sleep(30)")
    leader = ("import subprocess,sys,time;subprocess.Popen([sys.executable,'-c'," + repr(child) +
              "],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(30)")
    with pytest.raises(RuntimeError, match="timed out"):
        commands._run_process([sys.executable, "-c", leader], cwd=str(tmp_path), timeout=1)
    assert ready.exists()
    time.sleep(1.2)
    assert not marker.exists()


def test_owned_runner_drains_both_large_pipes_before_return(tmp_path):
    code, stdout, stderr = commands._run_process([sys.executable, "-c",
        "import sys;sys.stdout.write('x'*200000);sys.stderr.write('y'*200000)"], cwd=str(tmp_path), timeout=5)
    assert code == 0 and stdout == "x"*200000 and stderr == "y"*200000


@pytest.mark.parametrize("mode", [0, 7, "timeout"])
def test_health_probe_cleans_its_child_group_without_stopping_gateway(monkeypatch, tmp_path, mode):
    marker = tmp_path / "probe-child-survived"
    ready = tmp_path / "probe-child-ready"
    child = ("import signal,time;from pathlib import Path;"
             "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
             f"Path({str(ready)!r}).write_text('ready');"
             f"time.sleep(1.5);Path({str(marker)!r}).write_text('bad');time.sleep(30)")
    script = tmp_path / "probe-cli"
    script.write_text(f"#!{sys.executable}\nimport subprocess,sys,time\nfrom pathlib import Path\n"
        f"subprocess.Popen([sys.executable,'-c',{child!r}],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        f"ready=Path({str(ready)!r})\ndeadline=time.monotonic()+3\n"
        "while not ready.exists() and time.monotonic()<deadline:time.sleep(.01)\n"
        + ("time.sleep(30)\n" if mode == "timeout" else f"print('{{\"ok\":true}}',flush=True)\nsys.exit({mode})\n"))
    script.chmod(0o700)
    gateway = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"], start_new_session=True)
    commands._PROCESS = gateway
    monkeypatch.setattr(commands, "_binary", lambda: str(script))
    monkeypatch.setattr(commands, "_ENV", {"PATH": "/usr/bin:/bin"})
    try:
        assert commands._probe(.5 if mode == "timeout" else 3) is (mode == 0)
        assert ready.exists() and gateway.poll() is None
        time.sleep(1.7)
        assert not marker.exists()
    finally:
        commands.gateway_stop(command_timeout=1)
